"""
OCR处理Worker

从RabbitMQ消费OCR任务，执行OCR识别、数据提取、LLM增强、数据清洗和校验
"""
import asyncio
import json
import os
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import logger
from app.core.database import SessionLocal
from app.core.mq import rabbitmq_client
from app.core.config import settings
from app.models.task import Task, TaskStatus
from app.models.rule import Rule
from app.services.ocr_service import OCRService
from app.services.extraction_service import ExtractionService
from app.services.llm_service import llm_service
from app.services.validation_service import ValidationService
from app.services.file_service import file_service
from app.services.hash_service import hash_service


class OCRWorker:
    """OCR处理Worker类"""
    
    def __init__(self):
        """初始化Worker"""
        self.ocr_service = None
        self.extraction_service = None
        self.validation_service = ValidationService()
        self.is_running = False
        
        logger.info("OCR Worker初始化完成")
    
    async def initialize_services(self):
        """初始化OCR和提取服务"""
        if not self.ocr_service:
            # 初始化OCR服务
            ocr_config = {
                'max_parallel': getattr(settings, 'OCR_MAX_PARALLEL', 4),
                'umiocr_endpoint': getattr(settings, 'UMIOCR_ENDPOINT', 'http://localhost:1224'),
                'umiocr_timeout': getattr(settings, 'UMIOCR_TIMEOUT', 60),
            }
            self.ocr_service = OCRService(ocr_config)
            logger.info("OCR服务初始化完成")
        
        if not self.extraction_service:
            self.extraction_service = ExtractionService()
            logger.info("提取服务初始化完成")

    async def start(self):
        """启动Worker，开始消费消息"""
        if self.is_running:
            logger.warning("OCR Worker已在运行中")
            return
        
        self.is_running = True
        logger.info("OCR Worker启动，开始消费任务...")
        
        try:
            # 初始化服务
            await self.initialize_services()
            
            # 连接RabbitMQ
            await rabbitmq_client.connect()
            
            # 开始消费OCR任务队列
            await rabbitmq_client.consume_tasks(
                queue_name=settings.RABBITMQ_QUEUE_OCR,
                callback=self.process_task
            )
            
        except Exception as e:
            logger.error(f"OCR Worker运行失败: {str(e)}")
            self.is_running = False
            raise
    
    async def stop(self):
        """停止Worker"""
        self.is_running = False
        await rabbitmq_client.close()
        logger.info("OCR Worker已停止")

    async def process_task(self, task_data: Dict[str, Any]):
        """
        处理单个OCR任务
        
        Args:
            task_data: 任务数据，包含task_id
        """
        task_id = task_data.get('task_id')
        if not task_id:
            logger.error("任务数据缺少task_id")
            return
        
        logger.info(f"开始处理任务: {task_id}")
        
        async with SessionLocal() as db:
            try:
                # 1. 更新任务状态为Processing
                task = await self._update_task_status(
                    db, task_id, TaskStatus.PROCESSING
                )
                if not task:
                    logger.error(f"任务不存在: {task_id}")
                    return
                
                # 2. 下载文件从MinIO
                local_file_path = await self._download_file(task)
                
                try:
                    # 3. 加载规则配置
                    rule_config = await self._load_rule_config(db, task.rule_id, task.rule_version)
                    
                    # 4. 执行OCR处理
                    ocr_result = await self._execute_ocr(task, local_file_path, rule_config)
                    
                    # 5. 执行数据提取（包含LLM Schema提取的Token消耗）
                    extraction_result = await self._execute_extraction(
                        ocr_result, rule_config
                    )
                    extracted_data = {
                        'data': extraction_result.get('data', {}),
                        'confidence_scores': extraction_result.get('confidence_scores', {})
                    }
                    
                    # 记录数据提取阶段的LLM消耗
                    extraction_llm_stats = extraction_result.get('llm_stats', {})
                    total_llm_tokens = extraction_llm_stats.get('token_count', 0)
                    total_llm_cost = extraction_llm_stats.get('cost', 0.0)
                    
                    # 6. 执行LLM增强（如果配置）
                    if rule_config.get('llm_config', {}).get('enabled', False):
                        extracted_data, enhancement_llm_stats = await self._execute_llm_enhancement(
                            ocr_result, extracted_data, rule_config
                        )
                        # 累加LLM增强阶段的Token消耗
                        total_llm_tokens += enhancement_llm_stats.get('token_count', 0)
                        total_llm_cost += enhancement_llm_stats.get('cost', 0.0)
                    
                    # 更新任务的LLM统计信息（包含提取和增强两个阶段）
                    task.llm_token_count = total_llm_tokens
                    task.llm_cost = total_llm_cost
                    logger.info(f"任务LLM消耗统计: Token={total_llm_tokens}, 费用=¥{total_llm_cost:.4f}")
                    
                    # 7. 执行数据清洗
                    cleaned_data = await self._execute_cleaning(
                        extracted_data, rule_config
                    )
                    
                    # 8. 执行数据校验
                    validation_result = await self._execute_validation(
                        cleaned_data, rule_config
                    )
                    
                    # 9. 保存结果到数据库
                    await self._save_results(
                        db, task, ocr_result, cleaned_data, validation_result, rule_config
                    )
                    
                    # 10. 判断是否需要人工审核
                    needs_audit = self._check_needs_audit(
                        validation_result, cleaned_data, rule_config
                    )
                    
                    if needs_audit:
                        # 更新状态为待审核
                        await self._update_task_status(
                            db, task_id, TaskStatus.PENDING_AUDIT
                        )
                        logger.info(f"任务需要人工审核: {task_id}")
                    else:
                        # 更新状态为已完成
                        await self._update_task_status(
                            db, task_id, TaskStatus.COMPLETED
                        )
                        
                        # 触发推送任务
                        await self._trigger_push_task(task_id)
                        logger.info(f"任务处理完成: {task_id}")
                    
                finally:
                    # 清理临时文件
                    if os.path.exists(local_file_path):
                        os.remove(local_file_path)
                        logger.debug(f"临时文件已删除: {local_file_path}")
                
            except Exception as e:
                logger.error(f"任务处理失败 [{task_id}]: {str(e)}", exc_info=True)
                # 更新任务状态为失败
                await self._update_task_status(
                    db, task_id, TaskStatus.FAILED, error_message=str(e)
                )

    async def _update_task_status(
        self,
        db: AsyncSession,
        task_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None
    ) -> Optional[Task]:
        """
        更新任务状态
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息（可选）
            
        Returns:
            更新后的任务对象
        """
        try:
            stmt = select(Task).where(Task.id == task_id)
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()
            
            if not task:
                return None
            
            task.status = status
            
            if status == TaskStatus.PROCESSING and not task.started_at:
                task.started_at = datetime.utcnow()
            
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                task.completed_at = datetime.utcnow()
            
            if error_message:
                task.error_message = error_message
            
            await db.commit()
            await db.refresh(task)
            
            logger.info(f"任务状态已更新: {task_id} -> {status.value}")
            return task
            
        except Exception as e:
            logger.error(f"更新任务状态失败 [{task_id}]: {str(e)}")
            await db.rollback()
            raise
    
    async def _download_file(self, task: Task) -> str:
        """
        从MinIO下载文件到本地临时目录
        
        Args:
            task: 任务对象
            
        Returns:
            本地文件路径
        """
        try:
            # 创建临时目录
            temp_dir = tempfile.gettempdir()
            local_path = os.path.join(temp_dir, f"{task.id}_{task.file_name}")
            
            # 从MinIO下载文件
            await file_service.download_to_file(task.file_path, local_path)
            
            logger.info(f"文件下载成功: {task.file_path} -> {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"文件下载失败: {str(e)}")
            raise
    
    async def _load_rule_config(
        self,
        db: AsyncSession,
        rule_id: str,
        rule_version: str = None
    ) -> Dict[str, Any]:
        """
        加载规则配置（从数据库）
        
        Args:
            db: 数据库会话
            rule_id: 规则ID
            rule_version: 规则版本（可选，默认使用当前发布版本）
            
        Returns:
            规则配置字典
        """
        try:
            from app.models.rule import RuleVersion
            
            # 先查询规则获取当前版本
            stmt = select(Rule).where(Rule.id == rule_id)
            result = await db.execute(stmt)
            rule = result.scalar_one_or_none()
            
            if not rule:
                raise ValueError(f"规则不存在: {rule_id}")
            
            # 确定要使用的版本
            target_version = rule_version or rule.current_version
            if not target_version:
                raise ValueError(f"规则 {rule_id} 没有已发布的版本")
            
            # 查询规则版本获取配置
            stmt = select(RuleVersion).where(
                RuleVersion.rule_id == rule_id,
                RuleVersion.version == target_version
            )
            result = await db.execute(stmt)
            version_obj = result.scalar_one_or_none()
            
            if not version_obj:
                raise ValueError(f"规则版本不存在: {rule_id} - {target_version}")
            
            # 从版本配置中解析规则配置
            version_config = version_obj.config or {}
            
            # 将前端的extraction配置转换为extraction_rules数组（与沙箱测试保持一致）
            extraction_config = version_config.get('extraction', {})
            extraction_rules = []
            if extraction_config and isinstance(extraction_config, dict):
                for field_name, rule_config in extraction_config.items():
                    if rule_config and isinstance(rule_config, dict):
                        rule = {'field': field_name, **rule_config}
                        extraction_rules.append(rule)
            
            # 从validation配置中提取cleaning和validation规则（与沙箱测试保持一致）
            validation_config = version_config.get('validation', {})
            cleaning_rules = []
            validation_rules = []
            
            if validation_config and isinstance(validation_config, dict):
                for field_path, field_config in validation_config.items():
                    # 收集清洗规则
                    field_cleaning = field_config.get('cleaning', [])
                    if field_cleaning:
                        cleaning_rules.append({
                            'field': field_path,
                            'operations': field_cleaning
                        })
                    
                    # 收集验证规则
                    field_validation = field_config.get('validation', [])
                    for rule in field_validation:
                        validation_rules.append({
                            'field': field_path,
                            **rule
                        })
            
            config = {
                'basic': version_config.get('basic', {}),
                'schema': version_config.get('schema', {}),
                'extraction_rules': extraction_rules,
                'extraction_config': extraction_config,  # 保留原始配置供LLM提取使用
                'llm_config': version_config.get('llm_config', {}),
                'cleaning_rules': cleaning_rules,
                'validation_rules': validation_rules,
                'audit_config': version_config.get('audit_config', {}),
            }
            
            logger.info(f"规则配置加载成功: {rule_id} (版本: {target_version})")
            logger.info(f"提取规则数量: {len(extraction_rules)}, 清洗规则数量: {len(cleaning_rules)}, 校验规则数量: {len(validation_rules)}")
            logger.debug(f"原始validation配置: {validation_config}")
            return config
            
        except Exception as e:
            logger.error(f"加载规则配置失败: {str(e)}")
            raise

    async def _execute_ocr(
        self,
        task: Task,
        file_path: str,
        rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行OCR处理
        
        Args:
            task: 任务对象
            file_path: 本地文件路径
            rule_config: 规则配置
            
        Returns:
            OCR结果字典
        """
        try:
            # 每次任务创建新的OCR服务实例，避免PaddleOCR状态问题
            # PaddleOCR在处理多页时可能存在内存或状态累积问题
            ocr_config = {
                'max_parallel': getattr(settings, 'OCR_MAX_PARALLEL', 4),
                'umiocr_endpoint': getattr(settings, 'UMIOCR_ENDPOINT', 'http://localhost:1224'),
                'umiocr_timeout': getattr(settings, 'UMIOCR_TIMEOUT', 60),
            }
            task_ocr_service = OCRService(ocr_config, fast_mode=True)
            
            # 从basic配置中读取OCR相关配置（与前端配置结构一致）
            basic_config = rule_config.get('basic', {})
            
            # 获取OCR引擎配置
            engine = basic_config.get('ocrEngine', 'paddleocr')
            language_code = basic_config.get('language', 'zh')
            page_strategy_mode = basic_config.get('pageStrategy', 'multi_page')
            
            # 构建页面策略配置
            page_strategy = {'mode': page_strategy_mode}
            if page_strategy_mode == 'specified_pages':
                page_strategy['page_range'] = basic_config.get('pageRange', '1')
            
            # 语言映射：不同OCR引擎需要不同的语言代码
            if engine == 'tesseract':
                # Tesseract语言代码
                language_map = {
                    'zh': 'chi_sim',
                    'en': 'eng',
                    'zh_en': 'chi_sim+eng'
                }
                language = language_map.get(language_code, 'eng')
            elif engine == 'umiocr':
                # UmiOCR语言代码（与PaddleOCR类似）
                language_map = {
                    'zh': 'ch',
                    'en': 'en',
                    'zh_en': 'ch'
                }
                language = language_map.get(language_code, 'ch')
            else:
                # PaddleOCR语言代码
                language_map = {
                    'zh': 'ch',
                    'en': 'en',
                    'zh_en': 'ch'
                }
                language = language_map.get(language_code, 'en')
            
            # 禁用fallback，严格使用用户配置的引擎
            enable_fallback = False
            fallback_engine = None
            
            logger.info(f"开始OCR处理: 引擎={engine}, 语言={language}, 页面策略={page_strategy}, fallback=disabled")
            
            # 执行OCR（使用任务专用的OCR服务实例）
            ocr_result = await task_ocr_service.process_document(
                file_path=file_path,
                engine=engine,
                page_strategy=page_strategy,
                language=language,
                enable_fallback=enable_fallback,
                fallback_engine=fallback_engine
            )
            
            # 更新任务的页数
            task.page_count = ocr_result.page_count
            
            # 转换为字典格式
            result_dict = {
                'merged_text': ocr_result.merged_text,
                'page_count': ocr_result.page_count,
                'engine_used': ocr_result.engine_used,
                'fallback_used': ocr_result.fallback_used,
                'page_results': [
                    {
                        'page_num': pr.page_num,
                        'text': pr.text,
                        'confidence': pr.confidence,
                        'boxes': pr.boxes
                    }
                    for pr in ocr_result.page_results
                ]
            }
            
            logger.info(
                f"OCR处理完成: 页数={ocr_result.page_count}, "
                f"引擎={ocr_result.engine_used}, "
                f"文本长度={len(ocr_result.merged_text)}"
            )
            
            return result_dict
            
        except Exception as e:
            logger.error(f"OCR处理失败: {str(e)}")
            raise
    
    async def _execute_extraction(
        self,
        ocr_result: Dict[str, Any],
        rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行数据提取
        
        Args:
            ocr_result: OCR结果
            rule_config: 规则配置
            
        Returns:
            提取的数据字典，包含data、confidence_scores和llm_stats
        """
        try:
            schema = rule_config.get('schema', {})
            extraction_rules = rule_config.get('extraction_rules', [])
            
            if not extraction_rules:
                logger.warning("未配置提取规则，跳过数据提取")
                return {'data': {}, 'confidence_scores': {}, 'llm_stats': {'token_count': 0, 'cost': 0.0}}
            
            logger.info(f"开始数据提取: {len(extraction_rules)} 个规则")
            
            # 重构OCR结果为服务所需格式
            from app.services.ocr_service import OCRResult, PageOCRResult
            
            page_results = [
                PageOCRResult(
                    page_num=pr['page_num'],
                    text=pr['text'],
                    boxes=pr['boxes'],
                    confidence=pr['confidence']
                )
                for pr in ocr_result['page_results']
            ]
            
            ocr_result_obj = OCRResult(
                merged_text=ocr_result['merged_text'],
                page_results=page_results,
                page_count=ocr_result['page_count'],
                engine_used=ocr_result['engine_used'],
                fallback_used=ocr_result['fallback_used']
            )
            
            # 执行提取
            extraction_config = rule_config.get('extraction_config', {})
            extraction_results, llm_stats = await self.extraction_service.extract_fields(
                ocr_result=ocr_result_obj,
                schema=schema,
                extraction_rules=extraction_rules,
                extraction_config=extraction_config
            )
            
            # 转换为字典格式
            extracted_data = {}
            confidence_scores = {}
            
            for field_name, result in extraction_results.items():
                extracted_data[field_name] = result.value
                confidence_scores[field_name] = result.confidence
            
            logger.info(f"数据提取完成: {len(extracted_data)} 个字段, LLM Token消耗: {llm_stats.get('token_count', 0)}")
            
            return {
                'data': extracted_data,
                'confidence_scores': confidence_scores,
                'llm_stats': llm_stats
            }
            
        except Exception as e:
            logger.error(f"数据提取失败: {str(e)}")
            raise

    async def _execute_llm_enhancement(
        self,
        ocr_result: Dict[str, Any],
        extracted_data: Dict[str, Any],
        rule_config: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        执行LLM增强
        
        Args:
            ocr_result: OCR结果
            extracted_data: 已提取的数据
            rule_config: 规则配置
            
        Returns:
            (增强后的数据, LLM统计信息)
        """
        try:
            llm_config = rule_config.get('llm_config', {})
            llm_fields = llm_config.get('fields', [])
            
            if not llm_fields:
                logger.info("未配置LLM增强字段")
                return extracted_data, {'token_count': 0, 'cost': 0.0}
            
            logger.info(f"开始LLM增强: {len(llm_fields)} 个字段")
            
            total_tokens = 0
            total_cost = 0.0
            enhanced_data = extracted_data.get('data', {}).copy()
            confidence_scores = extracted_data.get('confidence_scores', {}).copy()
            
            # 对每个配置了LLM的字段进行增强
            for field_config in llm_fields:
                field_name = field_config.get('field')
                if not field_name:
                    continue
                
                # 调用LLM服务
                llm_result = await llm_service.extract_by_llm(
                    ocr_result=ocr_result,
                    field_name=field_name,
                    extraction_rule=field_config
                )
                
                if llm_result:
                    # 更新字段值和置信度
                    enhanced_data[field_name] = llm_result.get('value')
                    confidence_scores[field_name] = llm_result.get('confidence', 0.0)
                    
                    # 累计Token消耗
                    token_count = llm_result.get('token_count', 0)
                    total_tokens += token_count
                    
                    logger.info(
                        f"LLM增强完成: {field_name}, "
                        f"Token={token_count}, "
                        f"置信度={llm_result.get('confidence', 0.0)}"
                    )
            
            # 计算总费用
            total_cost = llm_service.calculate_cost(total_tokens)
            
            logger.info(
                f"LLM增强完成: 总Token={total_tokens}, 总费用=¥{total_cost}"
            )
            
            return {
                'data': enhanced_data,
                'confidence_scores': confidence_scores
            }, {
                'token_count': total_tokens,
                'cost': total_cost
            }
            
        except Exception as e:
            logger.error(f"LLM增强失败: {str(e)}")
            # LLM失败不影响整体流程，返回原始数据
            return extracted_data, {'token_count': 0, 'cost': 0.0}
    
    async def _execute_cleaning(
        self,
        extracted_data: Dict[str, Any],
        rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行数据清洗
        
        Args:
            extracted_data: 提取的数据
            rule_config: 规则配置
            
        Returns:
            清洗后的数据
        """
        try:
            cleaning_rules = rule_config.get('cleaning_rules', [])
            
            if not cleaning_rules:
                logger.info("未配置清洗规则，跳过数据清洗")
                return extracted_data
            
            logger.info(f"开始数据清洗: {len(cleaning_rules)} 个规则")
            
            data = extracted_data.get('data', {})
            
            # 执行清洗
            cleaned_data = self.validation_service.clean_data(
                data=data,
                cleaning_rules=cleaning_rules
            )
            
            logger.info("数据清洗完成")
            
            return {
                'data': cleaned_data,
                'confidence_scores': extracted_data.get('confidence_scores', {})
            }
            
        except Exception as e:
            logger.error(f"数据清洗失败: {str(e)}")
            # 清洗失败返回原始数据
            return extracted_data
    
    async def _execute_validation(
        self,
        cleaned_data: Dict[str, Any],
        rule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行数据校验
        
        Args:
            cleaned_data: 清洗后的数据
            rule_config: 规则配置
            
        Returns:
            校验结果
        """
        try:
            schema = rule_config.get('schema', {})
            validation_rules = rule_config.get('validation_rules', [])
            
            # 自动根据Schema的required字段生成必填校验规则
            auto_required_rules = self._generate_required_rules_from_schema(schema)
            
            # 合并用户配置的规则和自动生成的必填规则
            all_validation_rules = auto_required_rules + validation_rules
            
            logger.info(f"开始数据校验: {len(all_validation_rules)} 个规则 (自动必填: {len(auto_required_rules)}, 用户配置: {len(validation_rules)})")
            
            data = cleaned_data.get('data', {})
            
            # 执行类型转换和校验
            converted_data, warnings = self.validation_service.convert_schema_types(
                data=data,
                schema=schema
            )
            
            # 执行校验规则
            validation_result = self.validation_service.validate(
                data=converted_data,
                validation_rules=all_validation_rules
            )
            
            # 添加类型转换的警告
            for warning in warnings:
                validation_result.add_warning(warning)
            
            logger.info(
                f"数据校验完成: 有效={validation_result.is_valid}, "
                f"错误数={len(validation_result.errors)}, "
                f"警告数={len(validation_result.warnings)}"
            )
            
            return {
                'is_valid': validation_result.is_valid,
                'errors': [e.to_dict() for e in validation_result.errors],
                'warnings': validation_result.warnings,
                'converted_data': converted_data
            }
            
        except Exception as e:
            logger.error(f"数据校验失败: {str(e)}")
            raise
    
    def _generate_required_rules_from_schema(
        self,
        schema: Dict[str, Any],
        parent_path: str = ''
    ) -> List[Dict[str, Any]]:
        """
        根据Schema的required字段自动生成必填校验规则
        
        Args:
            schema: Schema定义
            parent_path: 父路径（用于嵌套字段）
            
        Returns:
            必填校验规则列表
        """
        rules = []
        
        for field_key, field_def in schema.items():
            field_path = f"{parent_path}.{field_key}" if parent_path else field_key
            node_type = field_def.get('nodeType', 'field')
            is_required = field_def.get('required', False)
            
            # 如果字段标记为必填，生成校验规则
            if is_required:
                rules.append({
                    'field': field_path,
                    'required': True
                })
                logger.debug(f"自动生成必填校验规则: {field_path}")
            
            # 递归处理嵌套结构
            if node_type == 'object' and 'properties' in field_def:
                child_rules = self._generate_required_rules_from_schema(
                    field_def['properties'], field_path
                )
                rules.extend(child_rules)
            elif node_type in ('array', 'table'):
                items = field_def.get('items', field_def.get('columns', {}))
                if items:
                    # 收集数组子字段中标记为必填的字段
                    required_child_fields = []
                    for item_key, item_def in items.items():
                        if item_def.get('required', False):
                            required_child_fields.append(item_key)
                    
                    # 如果有必填子字段，生成数组元素校验规则
                    if required_child_fields:
                        rules.append({
                            'field': field_path,
                            'type': 'array_items_required',
                            'required_fields': required_child_fields
                        })
                        logger.debug(f"自动生成数组子字段必填校验规则: {field_path}, 必填字段: {required_child_fields}")
        
        return rules

    async def _save_results(
        self,
        db: AsyncSession,
        task: Task,
        ocr_result: Dict[str, Any],
        cleaned_data: Dict[str, Any],
        validation_result: Dict[str, Any],
        rule_config: Dict[str, Any] = None
    ):
        """
        保存OCR结果和提取结果到数据库
        
        Args:
            db: 数据库会话
            task: 任务对象
            ocr_result: OCR结果
            cleaned_data: 清洗后的数据
            validation_result: 校验结果
            rule_config: 规则配置（用于获取置信度阈值）
        """
        try:
            # 保存OCR文本
            task.ocr_text = ocr_result.get('merged_text', '')
            
            # 保存完整OCR结果（含坐标），去掉重复的merged_text字段
            ocr_result_to_save = {k: v for k, v in ocr_result.items() if k != 'merged_text'}
            task.ocr_result = ocr_result_to_save
            
            # 保存提取的数据（使用转换后的数据）
            task.extracted_data = validation_result.get('converted_data', {})
            
            # 保存置信度分数
            confidence_scores = cleaned_data.get('confidence_scores', {})
            task.confidence_scores = confidence_scores
            
            # 收集审核原因
            audit_reasons = []
            
            # 1. 校验错误
            if not validation_result.get('is_valid', True):
                for error in validation_result.get('errors', []):
                    audit_reasons.append({
                        'type': 'validation_error',
                        'field': error.get('field'),
                        'message': error.get('message'),
                        'value': error.get('value')
                    })
            
            # 2. 置信度过低（使用每个字段在Schema中配置的阈值）
            if rule_config:
                schema = rule_config.get('schema', {})
                # 全局默认阈值（当字段未配置时使用）
                default_threshold = rule_config.get('audit_config', {}).get('confidence_threshold', 80.0)
                
                for field_name, confidence in confidence_scores.items():
                    # 获取字段在Schema中配置的阈值
                    field_threshold = self._get_field_confidence_threshold(
                        field_name, schema, default_threshold
                    )
                    
                    if confidence < field_threshold:
                        audit_reasons.append({
                            'type': 'confidence_low',
                            'field': field_name,
                            'message': f'置信度过低 ({confidence:.1f}% < {field_threshold}%)',
                            'confidence': confidence,
                            'threshold': field_threshold
                        })
            
            # 保存审核原因
            if audit_reasons:
                task.audit_reasons = audit_reasons
            
            await db.commit()
            logger.info(f"任务结果已保存: {task.id}")
            
        except Exception as e:
            logger.error(f"保存任务结果失败: {str(e)}")
            await db.rollback()
            raise
    
    def _check_needs_audit(
        self,
        validation_result: Dict[str, Any],
        cleaned_data: Dict[str, Any],
        rule_config: Dict[str, Any]
    ) -> bool:
        """
        判断是否需要人工审核
        
        审核条件：
        1. 校验失败（有错误）
        2. 置信度低于阈值
        
        Args:
            validation_result: 校验结果
            cleaned_data: 清洗后的数据
            rule_config: 规则配置
            
        Returns:
            是否需要审核
        """
        # 1. 校验失败
        if not validation_result.get('is_valid', True):
            logger.info("校验失败，需要人工审核")
            return True
        
        # 2. 检查置信度（使用每个字段在Schema中配置的阈值）
        schema = rule_config.get('schema', {})
        # 全局默认阈值（当字段未配置时使用）
        default_threshold = rule_config.get('audit_config', {}).get('confidence_threshold', 80.0)
        
        logger.info(f"Schema配置: {schema}")
        
        confidence_scores = cleaned_data.get('confidence_scores', {})
        
        for field_name, confidence in confidence_scores.items():
            # 获取字段在Schema中配置的阈值
            field_threshold = self._get_field_confidence_threshold(
                field_name, schema, default_threshold
            )
            
            if confidence < field_threshold:
                logger.info(
                    f"字段 {field_name} 置信度过低 ({confidence} < {field_threshold})，"
                    f"需要人工审核"
                )
                return True
        
        # 不需要审核
        return False
    
    def _get_field_confidence_threshold(
        self,
        field_name: str,
        schema: Dict[str, Any],
        default_threshold: float = 80.0
    ) -> float:
        """
        获取字段在Schema中配置的置信度阈值
        
        支持嵌套字段路径，如 "jinge.ext_price"
        
        Args:
            field_name: 字段名（支持点号分隔的嵌套路径）
            schema: Schema定义
            default_threshold: 默认阈值
            
        Returns:
            字段的置信度阈值
        """
        if not field_name or not schema:
            logger.debug(f"字段 {field_name} 使用默认阈值: {default_threshold} (schema为空)")
            return default_threshold
        
        # 如果是顶层字段，直接获取
        if field_name in schema:
            field_def = schema[field_name]
            threshold = field_def.get('confidenceThreshold', default_threshold)
            logger.debug(f"字段 {field_name} Schema配置: {field_def}, 阈值: {threshold}")
            return threshold
        
        # 处理嵌套字段（如 jinge.ext_price）
        parts = field_name.split('.')
        current = schema
        
        for i, part in enumerate(parts):
            if part not in current:
                return default_threshold
            
            node = current[part]
            
            # 如果是最后一个部分，返回该节点的阈值
            if i == len(parts) - 1:
                return node.get('confidenceThreshold', default_threshold)
            
            # 继续向下查找
            node_type = node.get('nodeType', '')
            if node_type == 'object' and 'properties' in node:
                current = node['properties']
            elif node_type == 'array' and 'items' in node:
                current = node['items']
            elif node_type == 'table' and 'columns' in node:
                current = node['columns']
            else:
                # 无法继续向下查找，返回默认值
                return default_threshold
        
        return default_threshold
    
    async def _trigger_push_task(self, task_id: str):
        """
        触发Pipeline处理任务（如果有配置管道则先执行管道，否则直接推送）
        
        Args:
            task_id: 任务ID
        """
        try:
            # 发布到Pipeline队列（Pipeline Worker会判断是否有管道配置）
            pipeline_task_data = {
                'task_id': task_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await rabbitmq_client.publish_task(
                queue_name=settings.RABBITMQ_QUEUE_PIPELINE,
                task_data=pipeline_task_data
            )
            
            logger.info(f"Pipeline任务已触发: {task_id}")
            
        except Exception as e:
            logger.error(f"触发Pipeline任务失败: {str(e)}")
            # 触发失败不影响主流程



# 创建全局Worker实例
ocr_worker = OCRWorker()


async def main():
    """主函数，用于独立运行Worker"""
    try:
        logger.info("=" * 60)
        logger.info("OCR Worker 启动中...")
        logger.info("=" * 60)
        
        await ocr_worker.start()
        
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭Worker...")
        await ocr_worker.stop()
    except Exception as e:
        logger.error(f"Worker运行异常: {str(e)}", exc_info=True)
        await ocr_worker.stop()


if __name__ == "__main__":
    # 独立运行Worker
    asyncio.run(main())

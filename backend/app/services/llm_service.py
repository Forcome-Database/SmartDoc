"""
LLM集成服务

提供LLM调用、熔断器、一致性校验和Token消耗跟踪功能
基于Agently 4.0最佳实践优化：
- 分离关注点：input/info/instruct/output
- Output Schema只包含结构定义
- 字段提取指令通过info传递
"""
import asyncio
import time
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher

try:
    # Agently 4.x 导入方式
    from agently import Agently
    AGENTLY_AVAILABLE = True
except ImportError as e:
    AGENTLY_AVAILABLE = False
    Agently = None
    import_error = str(e)
except Exception as e:
    AGENTLY_AVAILABLE = False
    Agently = None
    import_error = f"Unexpected error: {str(e)}"

from app.core.config import settings
from app.core.logger import logger


class CircuitBreakerOpen(Exception):
    """熔断器打开异常"""
    pass


class LLMServiceError(Exception):
    """LLM服务错误"""
    pass


class CircuitBreaker:
    """
    熔断器实现

    监控LLM服务的响应时间和错误率，当超时或5xx错误时触发熔断
    熔断期间返回None，降级为纯OCR模式，每5分钟尝试恢复
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 300,
        expected_exception: type = LLMServiceError
    ):
        """
        初始化熔断器

        Args:
            failure_threshold: 失败阈值，连续失败次数达到此值时触发熔断
            recovery_timeout: 恢复超时时间（秒），熔断后等待此时间尝试恢复
            expected_exception: 预期的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    async def call(self, func, *args, **kwargs):
        """
        通过熔断器调用函数

        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            CircuitBreakerOpen: 熔断器打开时抛出
        """
        # 检查是否可以尝试恢复
        if self.state == "open":
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout:
                logger.info("熔断器尝试恢复，进入半开状态")
                self.state = "half_open"
            else:
                raise CircuitBreakerOpen("LLM服务熔断器打开")

        try:
            result = await func(*args, **kwargs)

            # 调用成功，重置失败计数
            if self.state == "half_open":
                logger.info("熔断器恢复成功，关闭熔断器")
                self.state = "closed"
                self.failure_count = 0
                self.last_failure_time = None
            elif self.failure_count > 0:
                self.failure_count = 0

            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            logger.warning(
                f"LLM服务调用失败 ({self.failure_count}/{self.failure_threshold}): {str(e)}"
            )

            # 达到失败阈值，打开熔断器
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"LLM服务连续失败{self.failure_count}次，触发熔断，"
                    f"将在{self.recovery_timeout}秒后尝试恢复"
                )

            raise


class LLMService:
    """
    LLM集成服务

    基于Agently 4.0最佳实践，提供结构化数据提取功能
    """

    def __init__(self):
        """初始化LLM服务"""
        # 初始化Agently配置
        self.agent_config = None
        self._initialize_client()

        # 初始化熔断器
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=300,
            expected_exception=LLMServiceError
        )

        # Token单价配置
        self.token_price = getattr(settings, 'LLM_TOKEN_PRICE', 0.002)

        # 超时时间配置
        self.timeout = getattr(settings, 'LLM_TIMEOUT', 60)

    def _initialize_client(self):
        """
        初始化Agently客户端配置

        使用OpenAI兼容协议配置base_url、API Key和模型
        """
        if not AGENTLY_AVAILABLE:
            error_msg = "Agently库未安装，LLM功能将不可用"
            if 'import_error' in globals():
                error_msg += f" (错误: {import_error})"
            logger.warning(error_msg)
            return

        try:
            # 获取配置
            api_key = getattr(settings, 'LLM_API_KEY', None)
            base_url = getattr(settings, 'LLM_BASE_URL', None)
            model_name = getattr(settings, 'LLM_MODEL', 'gpt-3.5-turbo')
            proxy = getattr(settings, 'LLM_PROXY', None)

            if not api_key:
                logger.warning("未配置LLM_API_KEY，LLM功能将不可用")
                return

            # 保存配置信息
            self.agent_config = {
                'api_key': api_key,
                'base_url': base_url,
                'model_name': model_name,
                'proxy': proxy
            }

            # 使用 Agently.set_settings 全局配置
            Agently.set_settings(
                "OpenAICompatible",
                {
                    "base_url": base_url,
                    "model": model_name,
                    "model_type": "chat",
                    "api_key": api_key,
                }
            )

            logger.info(
                f"LLM客户端配置成功 - "
                f"模型: {model_name}, "
                f"Base URL: {base_url or 'https://api.openai.com/v1'}"
            )

        except Exception as e:
            logger.error(f"LLM客户端配置失败: {str(e)}")
            self.agent_config = None

    # ==================== 核心提取方法 ====================

    async def extract_by_schema(
        self,
        ocr_result: Dict[str, Any],
        schema: Dict[str, Any],
        extraction_config: Dict[str, Any],
        context_scope: str = 'all_pages',
        n_pages: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        根据Schema结构提取字段（一次请求，严格匹配Schema结构）

        基于Agently最佳实践：
        - .input(): 文档内容
        - .info(): 字段提取提示
        - .instruct(): 通用提取规则
        - .output(): 纯结构定义

        Args:
            ocr_result: OCR识别结果，包含merged_text和page_results
            schema: Schema定义，包含字段结构（nodeType, type, label等）
            extraction_config: 提取配置，包含每个字段的提取规则（type, promptTemplate等）
            context_scope: 上下文范围 (all_pages, first_n_pages, region)
            n_pages: 页数限制

        Returns:
            提取结果字典，结构与Schema完全一致
            如果LLM服务不可用或熔断，返回None
        """
        if not self.agent_config:
            logger.warning("LLM客户端未配置，跳过LLM提取")
            return None

        if not schema:
            logger.warning("Schema为空，跳过LLM提取")
            return None

        try:
            # 通过熔断器调用LLM
            result = await self.circuit_breaker.call(
                self._call_llm_schema_api,
                ocr_result,
                schema,
                extraction_config,
                context_scope,
                n_pages
            )
            return result

        except CircuitBreakerOpen:
            logger.warning("LLM服务熔断，提取降级为纯OCR模式")
            return None
        except Exception as e:
            logger.error(f"LLM Schema提取失败: {str(e)}")
            return None

    async def _call_llm_schema_api(
        self,
        ocr_result: Dict[str, Any],
        schema: Dict[str, Any],
        extraction_config: Dict[str, Any],
        context_scope: str,
        n_pages: int
    ) -> Dict[str, Any]:
        """
        根据Schema调用LLM API提取字段（Agently最佳实践）

        Args:
            ocr_result: OCR识别结果
            schema: Schema定义
            extraction_config: 提取配置
            context_scope: 上下文范围
            n_pages: 页数限制

        Returns:
            提取结果字典，结构与Schema一致

        Raises:
            LLMServiceError: LLM服务调用失败
        """
        try:
            # 1. 提取上下文
            extraction_rule = {
                'context_scope': context_scope,
                'n_pages': n_pages
            }
            context = self._extract_context(ocr_result, extraction_rule)

            # 2. 构建Agently output schema（只包含结构定义）
            output_schema = self._build_output_schema(
                schema, extraction_config)

            # 3. 收集字段提取提示（用于.info()）
            field_hints = self._collect_field_hints(schema, extraction_config)

            logger.info(
                f"Output Schema: {json.dumps(output_schema, ensure_ascii=False, default=str)}")
            logger.info(
                f"Field Hints: {json.dumps(field_hints, ensure_ascii=False, default=str)}")

            # 4. 创建Agent实例
            agent = Agently.create_agent()

            start_time = time.time()

            # 5. 使用Agently最佳实践构建请求
            response = await asyncio.wait_for(
                self._execute_agent_structured(
                    agent, context, output_schema, field_hints),
                timeout=self.timeout
            )

            duration = time.time() - start_time
            token_count = self._estimate_token_count(context, response)

            logger.info(
                f"LLM Schema提取成功: Token={token_count}, 耗时={duration:.2f}s")
            logger.info(
                f"LLM返回结果: {json.dumps(response, ensure_ascii=False, default=str)}")

            # 6. 清理返回数据
            cleaned_response = self._clean_llm_response(response)

            return {
                'data': cleaned_response,
                'token_count': token_count,
                'duration': duration
            }

        except asyncio.TimeoutError:
            logger.error(f"LLM Schema请求超时 (>{self.timeout}s)")
            raise LLMServiceError("LLM schema request timeout")
        except Exception as e:
            logger.error(f"LLM Schema API调用失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise LLMServiceError(f"LLM schema request failed: {str(e)}")

    async def _execute_agent_structured(
        self,
        agent,
        context: str,
        output_schema: Dict[str, Any],
        field_hints: Dict[str, str]
    ) -> Any:
        """
        使用Agently最佳实践执行Agent请求

        分离关注点：
        - .input(): 文档内容
        - .info(): 字段级别的提取提示
        - .instruct(): 通用提取规则
        - .output(): 纯结构定义

        Args:
            agent: Agently Agent实例
            context: 文档文本内容
            output_schema: 输出结构定义
            field_hints: 字段提取提示

        Returns:
            Agent响应结果
        """
        loop = asyncio.get_event_loop()
        
        # 构建完整的提示词结构用于日志
        instruct_list = [
            "从{document_text}中提取结构化信息",
            "参考{extraction_hints}中每个字段的提取提示进行精确匹配",
            "找不到的信息返回空字符串",
            "数组字段提取所有匹配项，每项作为数组元素",
            "保持原始表述，不添加解释或修改",
        ]
        
        # 输出完整的提示词构建信息
        logger.info("=" * 60)
        logger.info("【Agently 请求构建】")
        logger.info(f"[input] document_text 长度: {len(context)} 字符")
        logger.info(f"[info] extraction_hints: {json.dumps(field_hints, ensure_ascii=False, indent=2)}")
        logger.info(f"[instruct]: {instruct_list}")
        logger.info(f"[output] schema: {json.dumps(output_schema, ensure_ascii=False, default=str, indent=2)}")
        logger.info("=" * 60)

        def _sync_call():
            # 构建请求链
            request = agent.input({"document_text": context})

            # 添加字段提取提示
            if field_hints:
                request = request.info("extraction_hints", field_hints)

            # 添加通用提取指令
            request = request.instruct(instruct_list)

            # 设置输出结构
            request = request.output(output_schema)

            return request.start()

        # 在线程池中执行同步调用
        result = await loop.run_in_executor(None, _sync_call)
        return result

    # ==================== Schema构建方法 ====================

    def _build_output_schema(
        self,
        schema: Dict[str, Any],
        extraction_config: Dict[str, Any],
        parent_path: str = ''
    ) -> Dict[str, Any]:
        """
        根据Schema结构构建Agently的output schema

        核心逻辑：
        1. 如果节点本身配置了LLM提取，直接按其nodeType生成输出结构
        2. 如果节点有子节点，递归处理子节点
        3. 对象类型配置了LLM：检查promptTemplate是否包含JSON格式，如果是则解析为对象结构

        Args:
            schema: Schema定义
            extraction_config: 提取配置
            parent_path: 父路径（用于嵌套字段）

        Returns:
            Agently格式的output schema
        """
        output_schema = {}

        for field_key, field_def in schema.items():
            field_path = f"{parent_path}.{field_key}" if parent_path else field_key
            node_type = field_def.get('nodeType', 'field')
            field_label = field_def.get('label', field_key)
            field_type = field_def.get('type', 'string')

            # 获取该字段的提取配置（优先使用完整路径）
            field_extraction = extraction_config.get(field_path, {})
            if not field_extraction:
                field_extraction = extraction_config.get(field_key, {})

            extraction_type = field_extraction.get('type', '')
            has_llm_config = extraction_type == 'llm'
            custom_prompt = field_extraction.get('promptTemplate', '')

            logger.debug(
                f"处理字段: {field_path}, nodeType={node_type}, extractionType={extraction_type}, hasLLM={has_llm_config}")

            # 类型映射
            type_map = {
                'string': 'String',
                'int': 'Integer',
                'decimal': 'Float',
                'date': 'String',
                'boolean': 'Boolean'
            }

            if node_type == 'field':
                # 普通字段：只有配置了LLM提取才添加
                if has_llm_config:
                    # 检查提示词中是否有JSON结构定义（用户可能想返回对象）
                    json_structure = self._parse_json_from_prompt(custom_prompt)
                    if json_structure:
                        # 用户在提示词中定义了JSON结构，按对象处理
                        output_schema[field_key] = self._build_schema_from_json_keys(json_structure, field_label)
                        logger.info(f"字段 {field_path} (field类型) 使用提示词中的JSON结构")
                    else:
                        agently_type = type_map.get(field_type, 'String')
                        desc = f"{field_label}的值"
                        output_schema[field_key] = (agently_type, desc)

            elif node_type == 'object':
                # 对象类型
                properties = field_def.get('properties', {})
                
                logger.debug(f"对象字段 {field_path}: hasLLM={has_llm_config}, properties={bool(properties)}, prompt长度={len(custom_prompt)}")
                
                if has_llm_config:
                    # 对象本身配置了LLM提取
                    # 检查promptTemplate是否包含JSON格式定义
                    json_structure = self._parse_json_from_prompt(custom_prompt)
                    logger.debug(f"字段 {field_path} JSON解析结果: {json_structure}")
                    
                    if json_structure:
                        # 用户在提示词中定义了期望的JSON结构
                        output_schema[field_key] = self._build_schema_from_json_keys(json_structure, field_label)
                        logger.info(f"字段 {field_path} 使用提示词中的JSON结构")
                    elif properties:
                        # 有子节点定义，按子节点结构生成
                        child_schema = self._build_object_schema_for_llm(properties, field_label)
                        if child_schema:
                            output_schema[field_key] = child_schema
                            logger.info(f"字段 {field_path} 使用Schema子节点结构")
                    else:
                        # 无子节点，返回字符串
                        output_schema[field_key] = ("String", f"{field_label}的内容")
                        logger.info(f"字段 {field_path} 无子节点，使用字符串类型")
                elif properties:
                    # 对象没有配置LLM，但子节点可能配置了，递归处理
                    child_schema = self._build_output_schema(
                        properties, extraction_config, field_path
                    )
                    if child_schema:
                        output_schema[field_key] = child_schema

            elif node_type in ('array', 'table'):
                # 数组/表格类型
                items = field_def.get('items', field_def.get('columns', {}))
                
                if has_llm_config:
                    # 数组配置了LLM提取
                    # 检查提示词中是否有JSON数组结构定义
                    json_structure = self._parse_array_json_from_prompt(custom_prompt)
                    
                    if json_structure:
                        # 用户在提示词中定义了数组元素的JSON结构
                        item_schema = self._build_schema_from_json_keys(json_structure, field_label)
                        output_schema[field_key] = [item_schema]
                        logger.info(f"字段 {field_path} 使用提示词中的数组元素JSON结构")
                    elif items:
                        # 有子节点定义，按子节点结构生成
                        item_schema = self._build_object_schema_for_llm(items, field_label)
                        if item_schema:
                            output_schema[field_key] = [item_schema]
                            logger.info(f"字段 {field_path} 使用Schema子节点结构")
                    else:
                        # 无子节点，返回字符串数组
                        desc = f"{field_label}的每个元素"
                        output_schema[field_key] = [("String", desc)]
                        logger.info(f"字段 {field_path} 无子节点，使用字符串数组")
                elif items:
                    # 数组没有配置LLM，但子节点可能配置了，递归处理
                    item_schema = self._build_output_schema(
                        items, extraction_config, field_path
                    )
                    if item_schema:
                        output_schema[field_key] = [item_schema]

        return output_schema

    def _parse_json_from_prompt(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        从提示词中解析JSON结构定义
        
        用户可能在提示词中写类似：
        请提取xxx，以下面格式返回
        {
            "fengge": "",
            "yinyue": ""
        }
        
        Args:
            prompt: 用户的提示词
            
        Returns:
            解析出的JSON结构，如果没有则返回None
        """
        if not prompt:
            return None
        
        import re
        
        logger.debug(f"尝试从提示词解析JSON，原始内容: {prompt[:200]}...")
        
        # 先统一替换中文引号为英文引号
        normalized_prompt = prompt.replace('"', '"').replace('"', '"')
        normalized_prompt = normalized_prompt.replace(''', "'").replace(''', "'")
        # 替换中文冒号
        normalized_prompt = normalized_prompt.replace('：', ':')
        
        # 方法1：查找 { 和 } 之间的内容
        start_idx = normalized_prompt.find('{')
        end_idx = normalized_prompt.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_candidate = normalized_prompt[start_idx:end_idx + 1]
            logger.debug(f"找到JSON候选: {json_candidate}")
            
            try:
                # 清理换行和多余空白
                cleaned = json_candidate.replace('\n', ' ').replace('\r', ' ')
                cleaned = ' '.join(cleaned.split())
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and len(parsed) > 0:
                    logger.info(f"成功从提示词解析JSON结构: {list(parsed.keys())}")
                    return parsed
            except json.JSONDecodeError as e:
                logger.debug(f"JSON解析失败: {e}")
        
        # 方法2：使用正则表达式（备用）
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, normalized_prompt, re.DOTALL)
        
        for match in matches:
            try:
                cleaned = ' '.join(match.split())
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and len(parsed) > 0:
                    logger.info(f"成功从提示词解析JSON结构(正则): {list(parsed.keys())}")
                    return parsed
            except json.JSONDecodeError:
                continue
        
        logger.debug("未能从提示词中解析出JSON结构")
        return None

    def _parse_array_json_from_prompt(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        从提示词中解析数组元素的JSON结构定义
        
        用户可能在提示词中写类似：
        提取所有旁白，返回JSON格式：
        [{"scene":"场景名", "narration":"旁白内容"}]
        
        Args:
            prompt: 用户的提示词
            
        Returns:
            解析出的数组元素JSON结构（对象），如果没有则返回None
        """
        if not prompt:
            return None
        
        import re
        
        logger.debug(f"尝试从提示词解析数组JSON，原始内容: {prompt[:200]}...")
        
        # 先统一替换中文引号为英文引号
        normalized_prompt = prompt.replace('"', '"').replace('"', '"')
        normalized_prompt = normalized_prompt.replace(''', "'").replace(''', "'")
        normalized_prompt = normalized_prompt.replace('：', ':')
        
        # 查找 [{ 和 }] 之间的内容（数组包含对象）
        array_start = normalized_prompt.find('[{')
        array_end = normalized_prompt.rfind('}]')
        
        if array_start != -1 and array_end != -1 and array_end > array_start:
            # 提取数组内容
            array_content = normalized_prompt[array_start:array_end + 2]
            logger.debug(f"找到数组JSON候选: {array_content}")
            
            try:
                cleaned = array_content.replace('\n', ' ').replace('\r', ' ')
                cleaned = ' '.join(cleaned.split())
                parsed = json.loads(cleaned)
                
                # 如果是数组且第一个元素是对象，返回第一个元素作为模板
                if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                    logger.info(f"成功从提示词解析数组元素JSON结构: {list(parsed[0].keys())}")
                    return parsed[0]
            except json.JSONDecodeError as e:
                logger.debug(f"数组JSON解析失败: {e}")
        
        # 备用：查找单独的 { } 对象（用户可能只写了元素结构）
        return self._parse_json_from_prompt(prompt)

    def _build_schema_from_json_keys(self, json_obj: Dict[str, Any], parent_label: str) -> Dict[str, Any]:
        """
        根据JSON对象的键构建Agently output schema
        
        Args:
            json_obj: JSON对象
            parent_label: 父节点标签
            
        Returns:
            Agently格式的schema
        """
        schema = {}
        for key, value in json_obj.items():
            if isinstance(value, dict):
                schema[key] = self._build_schema_from_json_keys(value, key)
            elif isinstance(value, list):
                schema[key] = [("String", f"{key}的每个元素")]
            else:
                schema[key] = ("String", f"{key}的值")
        return schema

    def _build_object_schema_for_llm(self, properties: Dict[str, Any], parent_label: str) -> Dict[str, Any]:
        """
        为配置了LLM提取的对象构建子字段schema
        
        当对象本身配置了LLM提取时，需要按其properties定义生成完整的子结构
        
        Args:
            properties: 对象的properties定义
            parent_label: 父节点标签
            
        Returns:
            Agently格式的schema
        """
        schema = {}
        type_map = {
            'string': 'String',
            'int': 'Integer',
            'decimal': 'Float',
            'date': 'String',
            'boolean': 'Boolean'
        }
        
        for field_key, field_def in properties.items():
            field_label = field_def.get('label', field_key)
            field_type = field_def.get('type', 'string')
            node_type = field_def.get('nodeType', 'field')
            
            if node_type == 'field':
                agently_type = type_map.get(field_type, 'String')
                schema[field_key] = (agently_type, f"{field_label}的值")
            elif node_type == 'object':
                sub_properties = field_def.get('properties', {})
                if sub_properties:
                    schema[field_key] = self._build_object_schema_for_llm(sub_properties, field_label)
                else:
                    schema[field_key] = ("String", f"{field_label}的内容")
            elif node_type in ('array', 'table'):
                items = field_def.get('items', field_def.get('columns', {}))
                if items:
                    item_schema = self._build_object_schema_for_llm(items, field_label)
                    schema[field_key] = [item_schema]
                else:
                    schema[field_key] = [("String", f"{field_label}的每个元素")]
        
        return schema

    def _collect_field_hints(
        self,
        schema: Dict[str, Any],
        extraction_config: Dict[str, Any],
        parent_path: str = ''
    ) -> Dict[str, str]:
        """
        收集字段级别的提取提示（用于.info()）

        Agently最佳实践：
        - hints 只包含"如何查找"的提示
        - 输出格式由 .output() 定义，不在 hints 中重复
        - 如果用户提示词中包含JSON格式定义，只提取查找部分

        Args:
            schema: Schema定义
            extraction_config: 提取配置
            parent_path: 父路径

        Returns:
            字段提取提示字典 {field_path: hint}
        """
        hints = {}

        for field_key, field_def in schema.items():
            field_path = f"{parent_path}.{field_key}" if parent_path else field_key
            field_label = field_def.get('label', field_key)
            node_type = field_def.get('nodeType', 'field')

            # 获取提取配置（优先使用完整路径）
            field_extraction = extraction_config.get(field_path, {})
            if not field_extraction:
                field_extraction = extraction_config.get(field_key, {})

            if field_extraction.get('type') == 'llm':
                custom_prompt = field_extraction.get('promptTemplate', '')
                if custom_prompt:
                    # 清理用户提示词：移除JSON格式定义部分，只保留查找提示
                    clean_hint = self._extract_search_hint(custom_prompt, field_label)
                    hints[field_path] = clean_hint
                else:
                    # 默认提示：根据节点类型生成
                    if node_type == 'field':
                        hints[field_path] = f'查找"{field_label}"的值'
                    elif node_type == 'object':
                        hints[field_path] = f'查找"{field_label}"部分的内容'
                    elif node_type in ('array', 'table'):
                        hints[field_path] = f'查找所有"{field_label}"项'

            # 递归处理子节点（仅当父节点没有配置LLM时才递归）
            if field_extraction.get('type') != 'llm':
                if node_type == 'object' and field_def.get('properties'):
                    child_hints = self._collect_field_hints(
                        field_def['properties'], extraction_config, field_path
                    )
                    hints.update(child_hints)
                elif node_type in ('array', 'table'):
                    items = field_def.get('items', field_def.get('columns', {}))
                    if items:
                        child_hints = self._collect_field_hints(
                            items, extraction_config, field_path)
                        hints.update(child_hints)

        return hints

    def _extract_search_hint(self, prompt: str, field_label: str) -> str:
        """
        从用户提示词中提取查找提示，移除JSON格式定义部分
        
        用户可能写：
        "请从文本中提取'动画风格建议'内容，返回JSON格式：{...}"
        
        我们只需要：
        "查找'动画风格建议'内容"
        
        Args:
            prompt: 用户的完整提示词
            field_label: 字段标签
            
        Returns:
            清理后的查找提示
        """
        if not prompt:
            return f'查找"{field_label}"的内容'
        
        import re
        
        # 查找 { 的位置，截取之前的内容
        json_start = prompt.find('{')
        if json_start > 0:
            hint = prompt[:json_start].strip()
            # 移除末尾的格式说明词
            hint = re.sub(r'[,，]?\s*(返回|以|按|用|输出).*格式.*$', '', hint, flags=re.IGNORECASE)
            hint = re.sub(r'[,，]?\s*(返回|以|按|用|输出).*JSON.*$', '', hint, flags=re.IGNORECASE)
            hint = hint.rstrip('：:,，\n\r\t ')
            if hint and len(hint) > 5:  # 确保有足够的内容
                return hint.strip()
        
        # 如果没有JSON或提取失败，清理原提示词
        cleaned = re.sub(r'[,，]?\s*(返回|输出|以|按|用).*格式.*', '', prompt, flags=re.IGNORECASE)
        cleaned = re.sub(r'\{[^}]*\}', '', cleaned)  # 移除JSON部分
        cleaned = cleaned.strip().rstrip('：:,，\n\r\t ')
        
        return cleaned if cleaned and len(cleaned) > 3 else f'查找"{field_label}"的内容'

    # ==================== 辅助方法 ====================

    def _extract_context(
        self,
        ocr_result: Dict[str, Any],
        extraction_rule: Dict[str, Any]
    ) -> str:
        """
        根据Context Scope提取上下文

        Args:
            ocr_result: OCR识别结果
            extraction_rule: 提取规则

        Returns:
            提取的上下文文本
        """
        context_scope = extraction_rule.get('context_scope', 'all_pages')

        if context_scope == 'all_pages':
            # 使用完整的合并文本
            context = ocr_result.get('merged_text', '')
            logger.debug(f"提取上下文 (all_pages): 长度={len(context)}")
            return context

        elif context_scope == 'first_n_pages':
            # 提取前N页
            n_pages = extraction_rule.get('n_pages', 1)
            page_results = ocr_result.get('page_results', [])

            texts = []
            for i, page_result in enumerate(page_results[:n_pages]):
                texts.append(page_result.get('text', ''))

            separator = extraction_rule.get('separator', '\n')
            return separator.join(texts)

        elif context_scope == 'region':
            # 提取指定坐标区域的文本
            region = extraction_rule.get('region', {})
            page_num = region.get('page', 1)
            x = region.get('x', 0)
            y = region.get('y', 0)
            width = region.get('width', 0)
            height = region.get('height', 0)

            page_results = ocr_result.get('page_results', [])
            if page_num <= len(page_results):
                page_result = page_results[page_num - 1]
                texts = []
                for block in page_result.get('blocks', []):
                    block_x = block.get('x', 0)
                    block_y = block.get('y', 0)
                    if (x <= block_x <= x + width and
                            y <= block_y <= y + height):
                        texts.append(block.get('text', ''))
                return ' '.join(texts)

        # 默认返回全文
        return ocr_result.get('merged_text', '')

    def _clean_llm_response(self, response: Any) -> Any:
        """
        清理LLM返回的数据

        - 移除字符串中的字面转义字符（如 \\n, \\t）
        - 清理多余的空白字符

        Args:
            response: LLM返回的原始数据

        Returns:
            清理后的数据
        """
        if isinstance(response, str):
            # 替换字面的转义字符为实际字符，然后再清理
            cleaned = response.replace('\\n', '\n').replace('\\t', '\t')
            # 将多个连续空白字符替换为单个空格
            cleaned = ' '.join(cleaned.split())
            return cleaned.strip()
        elif isinstance(response, dict):
            return {k: self._clean_llm_response(v) for k, v in response.items()}
        elif isinstance(response, list):
            return [self._clean_llm_response(item) for item in response]
        else:
            return response

    def _estimate_token_count(self, prompt: str, response: Any) -> int:
        """
        估算Token消耗

        使用简单的字符数估算方法：
        - 英文：约4个字符 = 1 token
        - 中文：约1.5个字符 = 1 token

        Args:
            prompt: 输入提示词
            response: 响应结果

        Returns:
            估算的Token数量
        """
        # 计算输入Token
        input_chars = len(prompt) if isinstance(
            prompt, str) else len(str(prompt))
        input_tokens = input_chars // 2

        # 计算输出Token
        if isinstance(response, dict):
            response_text = json.dumps(response, ensure_ascii=False)
        else:
            response_text = str(response)

        output_chars = len(response_text)
        output_tokens = output_chars // 2

        total_tokens = input_tokens + output_tokens

        logger.debug(
            f"Token估算: 输入={input_tokens}, 输出={output_tokens}, 总计={total_tokens}")

        return total_tokens

    # ==================== 单字段提取（向后兼容） ====================

    async def extract_by_llm(
        self,
        ocr_result: Dict[str, Any],
        field_name: str,
        extraction_rule: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        使用LLM提取字段值（单字段提取，保留向后兼容）

        Args:
            ocr_result: OCR识别结果
            field_name: 字段名称
            extraction_rule: 提取规则配置

        Returns:
            提取结果字典，包含value、confidence、token_count等信息
        """
        if not self.agent_config:
            logger.warning("LLM客户端未配置，跳过LLM提取")
            return None

        try:
            result = await self.circuit_breaker.call(
                self._call_llm_single_field,
                ocr_result,
                field_name,
                extraction_rule
            )
            return result

        except CircuitBreakerOpen:
            logger.warning(f"LLM服务熔断，字段 {field_name} 降级为纯OCR模式")
            return None
        except Exception as e:
            logger.error(f"LLM提取失败: {str(e)}")
            return None

    async def _call_llm_single_field(
        self,
        ocr_result: Dict[str, Any],
        field_name: str,
        extraction_rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        单字段LLM提取（Agently最佳实践）

        Args:
            ocr_result: OCR识别结果
            field_name: 字段名称
            extraction_rule: 提取规则

        Returns:
            提取结果

        Raises:
            LLMServiceError: LLM服务调用失败
        """
        try:
            # 1. 提取上下文
            context = self._extract_context(ocr_result, extraction_rule)

            # 2. 获取自定义提示词
            custom_prompt = extraction_rule.get('prompt', '')

            # 3. 构建输出结构
            output_schema = {
                "value": ("String", f"{field_name}的值"),
                "confidence": ("Float", "置信度分数，范围0-1"),
                "explanation": ("String", "提取依据说明")
            }

            # 4. 构建提取提示
            if custom_prompt:
                hint = custom_prompt
            else:
                hint = f'查找并提取"{field_name}"的值'

            # 5. 创建Agent并执行
            agent = Agently.create_agent()

            start_time = time.time()

            loop = asyncio.get_event_loop()

            def _sync_call():
                return (
                    agent
                    .input({"document_text": context})
                    .info("extraction_hint", hint)
                    .instruct([
                        "从{document_text}中提取信息",
                        "参考{extraction_hint}进行精确匹配",
                        "找不到返回空字符串",
                    ])
                    .output(output_schema)
                    .start()
                )

            response = await asyncio.wait_for(
                loop.run_in_executor(None, _sync_call),
                timeout=self.timeout
            )

            duration = time.time() - start_time

            # 6. 解析响应
            result = self._parse_single_field_response(response, field_name)
            result['token_count'] = self._estimate_token_count(
                context, response)
            result['duration'] = duration

            logger.info(f"LLM提取成功: 字段={field_name}, 耗时={duration:.2f}s")

            return result

        except asyncio.TimeoutError:
            logger.error(f"LLM请求超时 (>{self.timeout}s)")
            raise LLMServiceError("LLM request timeout")
        except Exception as e:
            logger.error(f"LLM API调用失败: {str(e)}")
            raise LLMServiceError(f"LLM request failed: {str(e)}")

    def _parse_single_field_response(
        self,
        response: Any,
        field_name: str
    ) -> Dict[str, Any]:
        """
        解析单字段LLM响应

        Args:
            response: LLM响应结果
            field_name: 字段名称

        Returns:
            解析后的结果字典
        """
        try:
            if isinstance(response, dict):
                value = response.get('value', '')
                confidence = response.get('confidence', 0.5)
                explanation = response.get('explanation', '')

                if isinstance(confidence, (int, float)):
                    confidence = max(0.0, min(1.0, float(confidence)))
                else:
                    confidence = 0.5

                return {
                    'value': value,
                    'confidence': confidence * 100,
                    'explanation': explanation,
                    'source': 'llm'
                }
            else:
                return {
                    'value': str(response),
                    'confidence': 50.0,
                    'explanation': 'LLM直接返回',
                    'source': 'llm'
                }

        except Exception as e:
            logger.error(f"解析LLM响应失败: {str(e)}")
            return {
                'value': '',
                'confidence': 0.0,
                'explanation': f'解析失败: {str(e)}',
                'source': 'llm'
            }

    # ==================== 视觉提取方法（一致性校验用） ====================

    async def extract_by_vision(
        self,
        file_path: str,
        schema: Dict[str, Any],
        extraction_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        使用LLM视觉能力直接从PDF/图片提取数据（用于一致性校验）
        
        基于Agently视觉模式：
        - 使用 .files() 传入图片（支持URL或base64）
        - 使用 .start("vision") 启动视觉模式
        
        Args:
            file_path: 文件路径（PDF或图片）
            schema: Schema定义
            extraction_config: 提取配置
            
        Returns:
            提取结果字典，如果不支持视觉或失败返回None
        """
        if not self.agent_config:
            logger.warning("LLM客户端未配置，跳过视觉提取")
            return None
        
        try:
            import base64
            import os
            
            # 将文件转换为base64 data URL格式
            image_urls = []
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                # PDF转图片（只取前3页）
                try:
                    from pdf2image import convert_from_path
                    import io
                    
                    images = convert_from_path(file_path, first_page=1, last_page=3, dpi=150)
                    for img in images:
                        buffer = io.BytesIO()
                        img.save(buffer, format='PNG')
                        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                        # Agently需要完整的data URL格式
                        image_urls.append(f"data:image/png;base64,{img_base64}")
                    logger.info(f"PDF转换为 {len(image_urls)} 张图片")
                except Exception as e:
                    logger.warning(f"PDF转图片失败: {e}，跳过视觉提取")
                    return None
            elif file_ext in ['.png', '.jpg', '.jpeg', '.webp']:
                # 直接读取图片
                with open(file_path, 'rb') as f:
                    img_base64 = base64.b64encode(f.read()).decode('utf-8')
                    mime_type = 'image/png' if file_ext == '.png' else 'image/jpeg'
                    image_urls.append(f"data:{mime_type};base64,{img_base64}")
            else:
                logger.warning(f"不支持的文件格式: {file_ext}，跳过视觉提取")
                return None
            
            if not image_urls:
                return None
            
            # 构建输出Schema
            output_schema = self._build_output_schema(schema, extraction_config)
            field_hints = self._collect_field_hints(schema, extraction_config)
            
            logger.info(f"开始视觉提取: {len(image_urls)}张图片")
            
            start_time = time.time()
            
            response = await asyncio.wait_for(
                self._execute_vision_extraction(image_urls, output_schema, field_hints),
                timeout=self.timeout * 2  # 视觉提取需要更长时间
            )
            
            duration = time.time() - start_time
            logger.info(f"视觉提取完成: 耗时={duration:.2f}s")
            
            if response is None:
                logger.warning("视觉提取返回None")
                return None
            
            # 清理返回数据
            cleaned_response = self._clean_llm_response(response)
            
            return {
                'data': cleaned_response,
                'duration': duration,
                'method': 'vision'
            }
            
        except asyncio.TimeoutError:
            logger.error("视觉提取超时")
            return None
        except ImportError as e:
            logger.warning(f"视觉提取依赖缺失: {e}")
            return None
        except Exception as e:
            logger.error(f"视觉提取失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def _execute_vision_extraction(
        self,
        image_urls: List[str],
        output_schema: Dict[str, Any],
        field_hints: Dict[str, str]
    ) -> Any:
        """
        执行视觉提取（Agently 4.x 多模态输入）
        
        使用 .set_request_prompt("attachment", ...) 底层方法传入图片
        配合 rich_content: True 启用多模态支持
        
        Args:
            image_urls: 图片URL列表（支持URL或base64格式）
            output_schema: 输出结构定义（与OCR提取使用相同的schema）
            field_hints: 字段提取提示（包含用户定义的提取策略）
            
        Returns:
            Agent响应结果
        """
        loop = asyncio.get_event_loop()
        
        def _sync_call():
            try:
                # 构建详细的提取提示文本（与OCR提取策略保持一致）
                prompt_parts = [
                    "你是一个文档信息提取专家。请仔细查看图片中的文字内容，按照以下要求提取信息。",
                    ""
                ]
                
                # 添加字段级别的提取提示（来自用户配置的提取策略）
                if field_hints:
                    prompt_parts.append("【字段提取要求】")
                    for field_path, hint in field_hints.items():
                        # 使用字段路径的最后一部分作为显示名
                        field_name = field_path.split('.')[-1]
                        prompt_parts.append(f"- {field_name}: {hint}")
                    prompt_parts.append("")
                
                # 添加通用提取规则
                prompt_parts.extend([
                    "【提取规则】",
                    "1. 严格按照上述字段要求进行提取",
                    "2. 找不到的信息返回空字符串",
                    "3. 数组/表格字段提取所有匹配项",
                    "4. 保持原始表述，不添加解释或修改",
                    "5. 如果字段要求返回特定JSON结构，请严格遵循"
                ])
                
                prompt = "\n".join(prompt_parts)
                
                # 构建attachment内容（图片+文本）
                attachment_content = []
                for url in image_urls:
                    attachment_content.append({
                        "type": "image",
                        "image": url
                    })
                attachment_content.append({
                    "type": "text",
                    "text": prompt
                })
                
                # 创建Agent实例并配置
                agent = (
                    Agently.create_agent()
                    .set_settings("current_model", "OpenAICompatible")
                    .set_settings("model.OpenAICompatible.url", settings.LLM_BASE_URL)
                    .set_settings("model.OpenAICompatible.auth", {"api_key": settings.LLM_API_KEY})
                    .set_settings("model.OpenAICompatible.options", {
                        "model": settings.LLM_MODEL,
                        "rich_content": True  # 启用多模态支持
                    })
                )
                
                # 使用底层方法设置attachment，配合output schema
                result = (
                    agent
                    .set_request_prompt("attachment", attachment_content)
                    .output(output_schema)
                    .start()
                )
                
                return result
            except Exception as e:
                logger.error(f"视觉提取执行失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
        
        result = await loop.run_in_executor(None, _sync_call)
        return result

    # ==================== 一致性校验方法 ====================

    def compare_results(
        self,
        result_a: Any,
        result_b: Any,
        threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        对比两个提取结果的一致性（支持字符串、对象、数组）

        Args:
            result_a: 第一个结果（OCR+提取策略的结果）
            result_b: 第二个结果（视觉提取的结果）
            threshold: 相似度阈值（0-1），低于此值标记为不一致

        Returns:
            对比结果字典
        """
        # 处理空值
        if result_a is None and result_b is None:
            return {
                "is_consistent": True,
                "similarity": 1.0,
                "value_a": result_a,
                "value_b": result_b,
                "difference": "两者均为空"
            }

        if result_a is None or result_b is None:
            return {
                "is_consistent": False,
                "similarity": 0.0,
                "value_a": result_a,
                "value_b": result_b,
                "difference": "一个为空，另一个不为空"
            }

        # 根据类型选择比较方法
        if isinstance(result_a, dict) and isinstance(result_b, dict):
            similarity = self._compare_dicts(result_a, result_b)
        elif isinstance(result_a, list) and isinstance(result_b, list):
            similarity = self._compare_lists(result_a, result_b)
        else:
            # 字符串比较
            str_a = str(result_a).strip()
            str_b = str(result_b).strip()
            similarity = SequenceMatcher(None, str_a, str_b).ratio()

        is_consistent = similarity >= threshold

        if is_consistent:
            difference = f"相似度{similarity:.2%}，高于阈值{threshold:.2%}"
        else:
            difference = f"相似度{similarity:.2%}，低于阈值{threshold:.2%}"

        return {
            "is_consistent": is_consistent,
            "similarity": similarity,
            "value_a": result_a,
            "value_b": result_b,
            "difference": difference
        }

    def _compare_dicts(self, dict_a: Dict, dict_b: Dict) -> float:
        """比较两个字典的相似度"""
        if not dict_a and not dict_b:
            return 1.0
        if not dict_a or not dict_b:
            return 0.0
        
        all_keys = set(dict_a.keys()) | set(dict_b.keys())
        if not all_keys:
            return 1.0
        
        total_similarity = 0.0
        for key in all_keys:
            val_a = dict_a.get(key)
            val_b = dict_b.get(key)
            
            if val_a is None and val_b is None:
                total_similarity += 1.0
            elif val_a is None or val_b is None:
                total_similarity += 0.0
            elif isinstance(val_a, dict) and isinstance(val_b, dict):
                total_similarity += self._compare_dicts(val_a, val_b)
            elif isinstance(val_a, list) and isinstance(val_b, list):
                total_similarity += self._compare_lists(val_a, val_b)
            else:
                str_a = str(val_a).strip()
                str_b = str(val_b).strip()
                total_similarity += SequenceMatcher(None, str_a, str_b).ratio()
        
        return total_similarity / len(all_keys)

    def _compare_lists(self, list_a: List, list_b: List) -> float:
        """比较两个列表的相似度"""
        if not list_a and not list_b:
            return 1.0
        if not list_a or not list_b:
            return 0.0
        
        # 简单比较：按顺序比较元素
        max_len = max(len(list_a), len(list_b))
        total_similarity = 0.0
        
        for i in range(max_len):
            if i < len(list_a) and i < len(list_b):
                item_a = list_a[i]
                item_b = list_b[i]
                
                if isinstance(item_a, dict) and isinstance(item_b, dict):
                    total_similarity += self._compare_dicts(item_a, item_b)
                else:
                    str_a = str(item_a).strip()
                    str_b = str(item_b).strip()
                    total_similarity += SequenceMatcher(None, str_a, str_b).ratio()
            # 缺失的元素贡献0相似度
        
        return total_similarity / max_len

    def batch_compare_results(
        self,
        results_a: Dict[str, Any],
        results_b: Dict[str, Any],
        threshold: float = 0.8
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量对比多个字段的提取结果

        Args:
            results_a: 第一组结果（OCR+提取策略）
            results_b: 第二组结果（视觉提取）
            threshold: 相似度阈值

        Returns:
            对比结果字典
        """
        comparison_results = {}
        all_fields = set(results_a.keys()) | set(results_b.keys())

        for field_name in all_fields:
            value_a = results_a.get(field_name)
            value_b = results_b.get(field_name)

            comparison_results[field_name] = self.compare_results(
                value_a, value_b, threshold
            )

        inconsistent_count = sum(
            1 for result in comparison_results.values()
            if not result['is_consistent']
        )

        logger.info(
            f"批量一致性校验完成: 总字段数={len(comparison_results)}, "
            f"不一致字段数={inconsistent_count}"
        )

        return comparison_results

    # ==================== Token计费方法 ====================

    def count_tokens(
        self,
        text: str,
        is_chinese: Optional[bool] = None
    ) -> int:
        """
        计算文本的Token数量

        Args:
            text: 要计算的文本
            is_chinese: 是否为中文文本，None表示自动检测

        Returns:
            估算的Token数量
        """
        if not text:
            return 0

        char_count = len(text)

        if is_chinese is None:
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            chinese_ratio = chinese_chars / char_count if char_count > 0 else 0
            is_chinese = chinese_ratio > 0.5

        if is_chinese:
            tokens = int(char_count / 1.5)
        else:
            tokens = int(char_count / 4)

        return max(1, tokens)

    def calculate_cost(
        self,
        token_count: int,
        price_per_token: Optional[float] = None
    ) -> float:
        """
        根据Token数量计算费用

        Args:
            token_count: Token数量
            price_per_token: 每个Token的单价

        Returns:
            费用（元）
        """
        if price_per_token is None:
            price_per_token = self.token_price

        cost = token_count * price_per_token
        return round(cost, 4)

    def track_token_usage(
        self,
        task_id: str,
        field_name: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        跟踪Token消耗记录

        Args:
            task_id: 任务ID
            field_name: 字段名称
            input_tokens: 输入Token数
            output_tokens: 输出Token数
            metadata: 额外的元数据

        Returns:
            Token使用记录
        """
        total_tokens = input_tokens + output_tokens
        cost = self.calculate_cost(total_tokens)

        usage_record = {
            "task_id": task_id,
            "field_name": field_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        logger.info(
            f"Token使用跟踪: 任务={task_id}, 字段={field_name}, "
            f"总计={total_tokens}, 费用=¥{cost}"
        )

        return usage_record

    def aggregate_token_usage(
        self,
        usage_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        聚合多条Token使用记录

        Args:
            usage_records: Token使用记录列表

        Returns:
            聚合统计结果
        """
        if not usage_records:
            return {
                "total_records": 0,
                "total_tokens": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0,
                "avg_tokens_per_field": 0.0
            }

        total_input = sum(r.get('input_tokens', 0) for r in usage_records)
        total_output = sum(r.get('output_tokens', 0) for r in usage_records)
        total_tokens = total_input + total_output
        total_cost = sum(r.get('cost', 0.0) for r in usage_records)

        return {
            "total_records": len(usage_records),
            "total_tokens": total_tokens,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost": round(total_cost, 4),
            "avg_tokens_per_field": round(total_tokens / len(usage_records), 2)
        }


# 创建全局LLM服务实例
llm_service = LLMService()

"""
Webhook推送服务
提供推送核心功能、日志记录、重试逻辑和死信队列处理
支持标准HTTP Webhook和金蝶K3 Cloud集成
"""
import json
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.task import Task, TaskStatus
from app.models.webhook import Webhook, AuthType, WebhookType
from app.models.push_log import PushLog
from app.core.config import settings
from app.core.security import generate_webhook_signature, decrypt_sensitive_data
from app.core.storage import minio_client
from app.services.kingdee_service import KingdeeClient, KingdeeResult

logger = logging.getLogger(__name__)


class PushResult:
    """推送结果类"""
    
    def __init__(
        self,
        success: bool,
        http_status: Optional[int] = None,
        response_body: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: int = 0
    ):
        self.success = success
        self.http_status = http_status
        self.response_body = response_body
        self.error_message = error_message
        self.duration_ms = duration_ms


class PushService:
    """Webhook推送服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.timeout = settings.PUSH_TIMEOUT
    
    async def push_to_webhook(
        self,
        task: Task,
        webhook: Webhook,
        retry_count: int = 0
    ) -> PushResult:
        """
        推送任务结果到Webhook目标
        
        根据webhook_type自动选择推送方式：
        - standard: 标准HTTP推送
        - kingdee: 金蝶K3 Cloud推送
        
        Args:
            task: 任务对象
            webhook: Webhook配置对象
            retry_count: 当前重试次数
            
        Returns:
            PushResult: 推送结果
        """
        # 根据Webhook类型分流
        webhook_type = getattr(webhook, 'webhook_type', None) or WebhookType.STANDARD
        
        if webhook_type == WebhookType.KINGDEE:
            return await self._push_to_kingdee(task, webhook, retry_count)
        else:
            return await self._push_to_http(task, webhook, retry_count)
    
    async def _push_to_kingdee(
        self,
        task: Task,
        webhook: Webhook,
        retry_count: int = 0
    ) -> PushResult:
        """
        推送到金蝶K3 Cloud
        
        管道清洗后的数据直接作为金蝶API请求体
        
        Args:
            task: 任务对象
            webhook: Webhook配置对象
            retry_count: 当前重试次数
            
        Returns:
            PushResult: 推送结果
        """
        start_time = time.time()
        
        try:
            # 1. 获取管道清洗后的数据作为请求体
            request_body = task.extracted_data
            
            if not request_body:
                error_msg = "任务没有提取数据，无法推送到金蝶"
                logger.error(f"{error_msg}, task_id={task.id}")
                return PushResult(
                    success=False,
                    error_message=error_msg,
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            
            # 2. 验证请求体格式（必须包含parameters字段）
            if not isinstance(request_body, dict) or 'parameters' not in request_body:
                error_msg = "金蝶请求体格式错误，必须包含parameters字段"
                logger.error(f"{error_msg}, task_id={task.id}")
                return PushResult(
                    success=False,
                    error_message=error_msg,
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            
            # 3. 调用金蝶服务
            async with KingdeeClient() as client:
                kingdee_result: KingdeeResult = await client.smart_save(request_body)
            
            # 4. 计算耗时
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 5. 保存推送日志
            await self.save_push_log(
                task_id=task.id,
                webhook_id=webhook.id,
                http_status=kingdee_result.http_status,
                request_headers={"Content-Type": "application/json"},
                request_body=json.dumps(request_body, ensure_ascii=False),
                response_headers={},
                response_body=kingdee_result.response_body or "",
                duration_ms=duration_ms,
                retry_count=retry_count,
                error_message=kingdee_result.error_message if not kingdee_result.success else None
            )
            
            # 6. 记录日志
            if kingdee_result.success:
                mode_info = f"({kingdee_result.save_mode})"
                if kingdee_result.is_degraded:
                    mode_info = "(降级暂存)"
                logger.info(
                    f"金蝶推送成功{mode_info}: task_id={task.id}, "
                    f"bill_no={kingdee_result.bill_no}, duration={duration_ms}ms"
                )
            else:
                logger.warning(
                    f"金蝶推送失败: task_id={task.id}, "
                    f"error={kingdee_result.error_message}, duration={duration_ms}ms"
                )
            
            return PushResult(
                success=kingdee_result.success,
                http_status=kingdee_result.http_status,
                response_body=kingdee_result.response_body,
                error_message=kingdee_result.error_message,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"金蝶推送异常: {str(e)}"
            logger.error(f"{error_msg}, task_id={task.id}")
            
            # 保存失败日志
            await self.save_push_log(
                task_id=task.id,
                webhook_id=webhook.id,
                http_status=None,
                request_headers={},
                request_body="",
                response_headers={},
                response_body="",
                duration_ms=duration_ms,
                retry_count=retry_count,
                error_message=error_msg
            )
            
            return PushResult(
                success=False,
                error_message=error_msg,
                duration_ms=duration_ms
            )
    
    async def _push_to_http(
        self,
        task: Task,
        webhook: Webhook,
        retry_count: int = 0
    ) -> PushResult:
        """
        标准HTTP推送（原有逻辑）
        
        Args:
            task: 任务对象
            webhook: Webhook配置对象
            retry_count: 当前重试次数
            
        Returns:
            PushResult: 推送结果
        """
        start_time = time.time()
        
        # 验证URL
        endpoint_url = webhook.endpoint_url or ""
        if not endpoint_url.startswith(('http://', 'https://')):
            error_msg = f"Webhook URL无效: {endpoint_url or '(空)'}"
            logger.error(f"{error_msg}, task_id={task.id}, webhook={webhook.name}")
            return PushResult(
                success=False,
                error_message=error_msg,
                duration_ms=int((time.time() - start_time) * 1000)
            )
        
        try:
            # 1. 渲染请求体模版
            request_body = await self._render_request_template(task, webhook)
            
            # 2. 构建请求头
            headers = await self._build_headers(webhook, request_body)
            
            # 3. 发送HTTP POST请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    webhook.endpoint_url,
                    json=json.loads(request_body),
                    headers=headers
                )
            
            # 4. 计算耗时
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 5. 判断是否成功（2xx状态码）
            success = 200 <= response.status_code < 300
            
            # 6. 保存推送日志
            await self.save_push_log(
                task_id=task.id,
                webhook_id=webhook.id,
                http_status=response.status_code,
                request_headers=dict(headers),
                request_body=request_body,
                response_headers=dict(response.headers),
                response_body=response.text,
                duration_ms=duration_ms,
                retry_count=retry_count
            )
            
            if success:
                logger.info(
                    f"推送成功: task_id={task.id}, webhook={webhook.name}, "
                    f"status={response.status_code}, duration={duration_ms}ms"
                )
            else:
                logger.warning(
                    f"推送失败: task_id={task.id}, webhook={webhook.name}, "
                    f"status={response.status_code}, duration={duration_ms}ms"
                )
            
            return PushResult(
                success=success,
                http_status=response.status_code,
                response_body=response.text,
                duration_ms=duration_ms
            )
            
        except httpx.TimeoutException as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"推送超时: {str(e)}"
            logger.error(f"{error_msg}, task_id={task.id}, webhook={webhook.name}")
            
            # 保存失败日志
            await self.save_push_log(
                task_id=task.id,
                webhook_id=webhook.id,
                http_status=None,
                request_headers={},
                request_body="",
                response_headers={},
                response_body="",
                duration_ms=duration_ms,
                retry_count=retry_count,
                error_message=error_msg
            )
            
            return PushResult(
                success=False,
                error_message=error_msg,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"推送异常: {str(e)}"
            logger.error(f"{error_msg}, task_id={task.id}, webhook={webhook.name}")
            
            # 保存失败日志
            await self.save_push_log(
                task_id=task.id,
                webhook_id=webhook.id,
                http_status=None,
                request_headers={},
                request_body="",
                response_headers={},
                response_body="",
                duration_ms=duration_ms,
                retry_count=retry_count,
                error_message=error_msg
            )
            
            return PushResult(
                success=False,
                error_message=error_msg,
                duration_ms=duration_ms
            )
    
    async def _render_request_template(
        self,
        task: Task,
        webhook: Webhook
    ) -> str:
        """
        渲染请求体模版，替换变量
        
        支持的变量:
        - {{task_id}}: 任务ID
        - {{result_json}}: 提取结果JSON
        - {{file_url}}: 文件预签名URL
        - {{meta_info}}: 任务元信息
        
        Args:
            task: 任务对象
            webhook: Webhook配置对象
            
        Returns:
            渲染后的请求体JSON字符串
        """
        template = webhook.request_template
        
        # 准备变量值
        variables = {
            "task_id": task.id,
            "result_json": task.extracted_data or {},
            "file_url": await self._generate_file_url(task),
            "meta_info": {
                "file_name": task.file_name,
                "page_count": task.page_count,
                "rule_id": task.rule_id,
                "rule_version": task.rule_version,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "confidence_scores": task.confidence_scores or {},
                "llm_token_count": task.llm_token_count,
                "llm_cost": float(task.llm_cost) if task.llm_cost else 0
            }
        }
        
        # 将模版转换为JSON字符串
        template_str = json.dumps(template, ensure_ascii=False)
        
        # 替换变量
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in template_str:
                # 将值转换为JSON字符串（不带外层引号）
                value_str = json.dumps(value, ensure_ascii=False)
                template_str = template_str.replace(f'"{placeholder}"', value_str)
        
        return template_str
    
    async def _generate_file_url(self, task: Task) -> str:
        """
        生成文件预签名URL
        
        Args:
            task: 任务对象
            
        Returns:
            预签名URL
        """
        try:
            # 从file_path中提取object_name
            # file_path格式: idp-files/2025/01/15/T_xxx/file.pdf
            object_name = task.file_path.split("/", 1)[1] if "/" in task.file_path else task.file_path
            
            # 生成1小时有效期的预签名URL
            from datetime import timedelta
            url = minio_client.generate_presigned_url(
                object_name=object_name,
                expires=timedelta(hours=1)
            )
            return url
        except Exception as e:
            logger.error(f"生成文件URL失败: {str(e)}, task_id={task.id}")
            return ""
    
    async def _build_headers(
        self,
        webhook: Webhook,
        request_body: str
    ) -> Dict[str, str]:
        """
        构建请求头，包含认证信息和签名
        
        Args:
            webhook: Webhook配置对象
            request_body: 请求体JSON字符串
            
        Returns:
            请求头字典
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"{settings.APP_NAME}/{settings.APP_VERSION}",
            "X-IDP-Timestamp": str(int(time.time()))
        }
        
        # 添加HMAC签名
        if webhook.secret_key:
            # 解密secret_key
            secret_key = decrypt_sensitive_data(webhook.secret_key)
            signature = generate_webhook_signature(request_body, secret_key)
            headers["X-IDP-Signature"] = signature
        
        # 根据认证类型添加认证信息
        if webhook.auth_type == AuthType.BASIC:
            # Basic Auth
            if webhook.auth_config:
                username = webhook.auth_config.get("username", "")
                password = webhook.auth_config.get("password", "")
                # 解密密码
                password = decrypt_sensitive_data(password) if password else ""
                
                import base64
                credentials = f"{username}:{password}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
        
        elif webhook.auth_type == AuthType.BEARER:
            # Bearer Token
            if webhook.auth_config:
                token = webhook.auth_config.get("token", "")
                # 解密token
                token = decrypt_sensitive_data(token) if token else ""
                headers["Authorization"] = f"Bearer {token}"
        
        elif webhook.auth_type == AuthType.API_KEY:
            # API Key
            if webhook.auth_config:
                key_name = webhook.auth_config.get("key_name", "X-API-Key")
                key_value = webhook.auth_config.get("key_value", "")
                # 解密key_value
                key_value = decrypt_sensitive_data(key_value) if key_value else ""
                headers[key_name] = key_value
        
        return headers

    
    async def save_push_log(
        self,
        task_id: str,
        webhook_id: str,
        http_status: Optional[int],
        request_headers: Dict[str, Any],
        request_body: str,
        response_headers: Dict[str, Any],
        response_body: str,
        duration_ms: int,
        retry_count: int = 0,
        error_message: Optional[str] = None
    ) -> PushLog:
        """
        保存推送日志到数据库
        
        Args:
            task_id: 任务ID
            webhook_id: Webhook ID
            http_status: HTTP状态码
            request_headers: 请求头
            request_body: 请求体
            response_headers: 响应头
            response_body: 响应体
            duration_ms: 耗时（毫秒）
            retry_count: 重试次数
            error_message: 错误信息
            
        Returns:
            PushLog: 推送日志对象
        """
        try:
            # 创建推送日志记录
            push_log = PushLog(
                task_id=task_id,
                webhook_id=webhook_id,
                http_status=http_status,
                request_headers=request_headers,
                request_body=request_body,
                response_headers=response_headers,
                response_body=response_body,
                duration_ms=duration_ms,
                retry_count=retry_count,
                error_message=error_message,
                created_at=datetime.utcnow()
            )
            
            self.db.add(push_log)
            await self.db.commit()
            await self.db.refresh(push_log)
            
            logger.debug(f"推送日志已保存: log_id={push_log.id}, task_id={task_id}")
            return push_log
            
        except Exception as e:
            logger.error(f"保存推送日志失败: {str(e)}, task_id={task_id}")
            await self.db.rollback()
            raise
    
    async def get_push_logs(
        self,
        task_id: str,
        webhook_id: Optional[str] = None
    ) -> List[PushLog]:
        """
        获取任务的推送日志
        
        Args:
            task_id: 任务ID
            webhook_id: Webhook ID（可选，用于筛选特定Webhook的日志）
            
        Returns:
            推送日志列表
        """
        try:
            query = select(PushLog).where(PushLog.task_id == task_id)
            
            if webhook_id:
                query = query.where(PushLog.webhook_id == webhook_id)
            
            query = query.order_by(PushLog.created_at.desc())
            
            result = await self.db.execute(query)
            logs = result.scalars().all()
            
            return list(logs)
            
        except Exception as e:
            logger.error(f"获取推送日志失败: {str(e)}, task_id={task_id}")
            return []

    
    def calculate_retry_delay(self, retry_count: int) -> int:
        """
        计算重试延迟时间（指数退避）
        
        Args:
            retry_count: 当前重试次数（0-based）
            
        Returns:
            延迟时间（秒）
        """
        # 使用配置的延迟时间列表
        if retry_count < len(settings.PUSH_RETRY_DELAYS):
            return settings.PUSH_RETRY_DELAYS[retry_count]
        
        # 超出配置范围，使用最后一个值
        return settings.PUSH_RETRY_DELAYS[-1]
    
    async def should_retry(
        self,
        push_result: PushResult,
        retry_count: int
    ) -> bool:
        """
        判断是否应该重试
        
        Args:
            push_result: 推送结果
            retry_count: 当前重试次数
            
        Returns:
            是否应该重试
        """
        # 如果已达到最大重试次数，不再重试
        if retry_count >= settings.PUSH_RETRY_MAX:
            return False
        
        # 如果推送成功，不需要重试
        if push_result.success:
            return False
        
        # 如果是4xx客户端错误（除了429），不重试
        if push_result.http_status and 400 <= push_result.http_status < 500:
            if push_result.http_status != 429:  # 429 Too Many Requests可以重试
                return False
        
        # 其他情况（5xx服务器错误、超时、网络错误等）都重试
        return True
    
    async def retry_push(
        self,
        task_id: str,
        webhook_id: str,
        retry_count: int
    ) -> Dict[str, Any]:
        """
        创建重试推送任务
        
        Args:
            task_id: 任务ID
            webhook_id: Webhook ID
            retry_count: 重试次数
            
        Returns:
            重试任务信息
        """
        delay = self.calculate_retry_delay(retry_count)
        
        retry_info = {
            "task_id": task_id,
            "webhook_id": webhook_id,
            "retry_count": retry_count + 1,
            "delay": delay,
            "scheduled_at": datetime.utcnow().timestamp() + delay
        }
        
        logger.info(
            f"计划重试推送: task_id={task_id}, webhook_id={webhook_id}, "
            f"retry_count={retry_count + 1}, delay={delay}s"
        )
        
        return retry_info
    
    async def push_with_retry(
        self,
        task: Task,
        webhook: Webhook,
        max_retries: Optional[int] = None
    ) -> PushResult:
        """
        推送任务结果，支持自动重试
        
        Args:
            task: 任务对象
            webhook: Webhook配置对象
            max_retries: 最大重试次数（可选，默认使用配置值）
            
        Returns:
            PushResult: 最终推送结果
        """
        if max_retries is None:
            max_retries = settings.PUSH_RETRY_MAX
        
        retry_count = 0
        last_result = None
        
        while retry_count <= max_retries:
            # 执行推送
            result = await self.push_to_webhook(task, webhook, retry_count)
            last_result = result
            
            # 如果成功，直接返回
            if result.success:
                return result
            
            # 判断是否应该重试
            if not await self.should_retry(result, retry_count):
                logger.warning(
                    f"推送失败且不应重试: task_id={task.id}, webhook={webhook.name}, "
                    f"status={result.http_status}, retry_count={retry_count}"
                )
                break
            
            # 如果还有重试机会，等待后重试
            if retry_count < max_retries:
                delay = self.calculate_retry_delay(retry_count)
                logger.info(
                    f"等待{delay}秒后重试: task_id={task.id}, webhook={webhook.name}, "
                    f"retry_count={retry_count + 1}"
                )
                
                import asyncio
                await asyncio.sleep(delay)
                retry_count += 1
            else:
                break
        
        # 所有重试都失败
        logger.error(
            f"推送失败，已达最大重试次数: task_id={task.id}, webhook={webhook.name}, "
            f"retry_count={retry_count}"
        )
        
        return last_result

    
    async def move_to_dlq(
        self,
        task_id: str,
        webhook_id: str,
        failure_reason: str,
        retry_count: int = 0
    ) -> bool:
        """
        将推送失败的任务移入死信队列
        
        Args:
            task_id: 任务ID
            webhook_id: Webhook ID
            failure_reason: 失败原因
            retry_count: 重试次数
            
        Returns:
            是否成功移入死信队列
        """
        try:
            # 1. 更新任务状态为Push Failed
            result = await self.db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                logger.error(f"任务不存在: task_id={task_id}")
                return False
            
            # 更新任务状态
            task.status = TaskStatus.PUSH_FAILED
            task.error_message = f"推送失败（重试{retry_count}次）: {failure_reason}"
            
            await self.db.commit()
            
            logger.warning(
                f"任务已移入死信队列: task_id={task_id}, webhook_id={webhook_id}, "
                f"reason={failure_reason}, retry_count={retry_count}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"移入死信队列失败: {str(e)}, task_id={task_id}")
            await self.db.rollback()
            return False
    
    async def get_dlq_tasks(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        获取死信队列中的任务
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            任务列表
        """
        try:
            query = (
                select(Task)
                .where(Task.status == TaskStatus.PUSH_FAILED)
                .order_by(Task.completed_at.desc())
                .limit(limit)
                .offset(offset)
            )
            
            result = await self.db.execute(query)
            tasks = result.scalars().all()
            
            return list(tasks)
            
        except Exception as e:
            logger.error(f"获取死信队列任务失败: {str(e)}")
            return []
    
    async def retry_dlq_task(
        self,
        task_id: str,
        webhook_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        手动重推死信队列中的任务
        
        Args:
            task_id: 任务ID
            webhook_id: Webhook ID（可选，如果不指定则推送到所有关联的Webhook）
            
        Returns:
            重推结果
        """
        try:
            # 1. 获取任务
            result = await self.db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                return {
                    "success": False,
                    "message": f"任务不存在: {task_id}"
                }
            
            # 2. 获取Webhook配置
            if webhook_id:
                # 推送到指定Webhook
                webhook_result = await self.db.execute(
                    select(Webhook).where(Webhook.id == webhook_id)
                )
                webhook = webhook_result.scalar_one_or_none()
                
                if not webhook:
                    return {
                        "success": False,
                        "message": f"Webhook不存在: {webhook_id}"
                    }
                
                webhooks = [webhook]
            else:
                # 推送到所有关联的Webhook
                webhooks = task.rule.webhooks if task.rule else []
            
            if not webhooks:
                return {
                    "success": False,
                    "message": "没有关联的Webhook配置"
                }
            
            # 3. 更新任务状态为Pushing
            task.status = TaskStatus.PUSHING
            task.error_message = None
            await self.db.commit()
            
            # 4. 执行推送
            results = []
            for webhook in webhooks:
                push_result = await self.push_to_webhook(task, webhook, retry_count=0)
                results.append({
                    "webhook_id": webhook.id,
                    "webhook_name": webhook.name,
                    "success": push_result.success,
                    "http_status": push_result.http_status,
                    "error_message": push_result.error_message
                })
            
            # 5. 判断整体结果
            all_success = all(r["success"] for r in results)
            
            if all_success:
                task.status = TaskStatus.PUSH_SUCCESS
                await self.db.commit()
                
                return {
                    "success": True,
                    "message": "重推成功",
                    "results": results
                }
            else:
                task.status = TaskStatus.PUSH_FAILED
                task.error_message = "部分或全部推送失败"
                await self.db.commit()
                
                return {
                    "success": False,
                    "message": "重推失败",
                    "results": results
                }
            
        except Exception as e:
            logger.error(f"重推任务失败: {str(e)}, task_id={task_id}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"重推异常: {str(e)}"
            }
    
    async def batch_push(
        self,
        task: Task,
        webhooks: List[Webhook]
    ) -> List[PushResult]:
        """
        批量推送到多个Webhook目标
        
        Args:
            task: 任务对象
            webhooks: Webhook配置列表
            
        Returns:
            推送结果列表
        """
        import asyncio
        
        # 并行推送到所有Webhook
        tasks = [
            self.push_to_webhook(task, webhook)
            for webhook in webhooks
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"批量推送异常: task_id={task.id}, "
                    f"webhook={webhooks[i].name}, error={str(result)}"
                )
                processed_results.append(
                    PushResult(
                        success=False,
                        error_message=str(result)
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results


# 工具函数

async def get_push_service(db: AsyncSession) -> PushService:
    """
    获取推送服务实例（依赖注入）
    
    Args:
        db: 数据库会话
        
    Returns:
        PushService实例
    """
    return PushService(db)

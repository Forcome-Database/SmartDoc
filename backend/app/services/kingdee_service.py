# -*- coding: utf-8 -*-
"""
金蝶K3 Cloud通用推送服务

提供金蝶K3 Cloud API集成功能：
- 登录认证（Session Cookie）
- Save接口（创建单据，严格校验）
- Draft接口（暂存单据，宽松校验）
- 智能保存（Save失败自动降级Draft）

接口说明：
- 登录: AuthService.ValidateUser.common.kdsvc
- 保存: DynamicFormService.Save.common.kdsvc（ValidateFlag=true，严格校验）
- 暂存: DynamicFormService.Draft.common.kdsvc（校验宽松，允许不完整数据）
"""
import json
import time
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class KingdeeResult:
    """金蝶API调用结果"""
    success: bool
    http_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: int = 0
    bill_no: Optional[str] = None  # 单据编号
    bill_id: Optional[int] = None  # 单据ID
    save_mode: Optional[str] = None  # "save" 或 "draft"
    is_degraded: bool = False  # 是否降级保存


class KingdeeClient:
    """
    金蝶K3 Cloud API客户端
    
    使用环境变量配置连接信息，form_id从请求体中获取
    """
    
    def __init__(self, timeout: int = None):
        """
        初始化金蝶客户端
        
        Args:
            timeout: 请求超时时间（秒），默认使用配置值
        """
        self.api_url = (settings.KINGDEE_API_URL or '').rstrip('/')
        self.db_id = settings.KINGDEE_DB_ID or ''
        self.username = settings.KINGDEE_USERNAME or ''
        self.password = settings.KINGDEE_PASSWORD or ''
        self.save_mode = settings.KINGDEE_SAVE_MODE or 'smart'
        self.timeout = timeout or settings.KINGDEE_TIMEOUT or 30
        
        # HTTP客户端和会话状态
        self._client: Optional[httpx.AsyncClient] = None
        self._cookies: Dict[str, str] = {}
        self._is_logged_in: bool = False
    
    @property
    def is_configured(self) -> bool:
        """检查金蝶配置是否完整"""
        return bool(self.api_url and self.db_id and self.username and self.password)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建HTTP客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        self._is_logged_in = False
        self._cookies = {}
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    
    async def login(self) -> bool:
        """
        登录金蝶系统
        
        POST: {api_url}/Kingdee.BOS.WebApi.ServicesStub.AuthService.ValidateUser.common.kdsvc
        Body: {"parameters": "[\"db_id\",\"username\",\"password\",2052]"}
        
        Returns:
            是否登录成功
        """
        if not self.is_configured:
            logger.error("金蝶配置不完整，无法登录")
            return False
        
        url = f"{self.api_url}/Kingdee.BOS.WebApi.ServicesStub.AuthService.ValidateUser.common.kdsvc"
        params = [self.db_id, self.username, self.password, 2052]
        payload = {"parameters": json.dumps(params)}
        
        try:
            client = await self._get_client()
            response = await client.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            # 保存Cookie用于后续请求
            self._cookies = dict(response.cookies)
            
            result = response.json()
            if result.get("LoginResultType") == 1:
                self._is_logged_in = True
                logger.info(f"金蝶登录成功: user={self.username}, db={self.db_id}")
                return True
            else:
                error_msg = result.get('Message', '未知错误')
                logger.error(f"金蝶登录失败: {error_msg}")
                return False
                
        except httpx.TimeoutException:
            logger.error(f"金蝶登录超时: url={url}")
            return False
        except Exception as e:
            logger.error(f"金蝶登录异常: {str(e)}")
            return False
    
    async def _ensure_logged_in(self) -> bool:
        """确保已登录，未登录则自动登录"""
        if not self._is_logged_in:
            return await self.login()
        return True
    
    async def save_bill(self, request_body: Dict[str, Any]) -> KingdeeResult:
        """
        Save接口 - 保存单据（创建状态，严格校验）
        
        POST: {api_url}/Kingdee.BOS.WebApi.ServicesStub.DynamicFormService.Save.common.kdsvc
        
        注意：Save接口默认 ValidateFlag=true，会执行严格的必填校验
        即使设置 FDocumentStatus="Z"（暂存状态），仍然会校验必填字段
        
        Args:
            request_body: 完整的金蝶API请求体，格式如：
                {
                    "parameters": [
                        "PAEZ_PO",  # FormId
                        {
                            "NeedUpDateFields": [],
                            "NeedReturnFields": ["FBillNo", "FID"],
                            "IsDeleteEntry": "true",
                            "Model": { ... }  # 单据数据
                        }
                    ]
                }
        
        Returns:
            KingdeeResult: 保存结果
        """
        url = f"{self.api_url}/Kingdee.BOS.WebApi.ServicesStub.DynamicFormService.Save.common.kdsvc"
        return await self._execute_save(url, request_body, "save")
    
    async def draft_bill(self, request_body: Dict[str, Any]) -> KingdeeResult:
        """
        Draft接口 - 暂存单据（草稿状态，宽松校验）
        
        POST: {api_url}/Kingdee.BOS.WebApi.ServicesStub.DynamicFormService.Draft.common.kdsvc
        
        注意：Draft接口校验较宽松，允许保存不完整的数据
        适用于数据不完整但需要先保存的场景
        
        Args:
            request_body: 完整的金蝶API请求体（格式同save_bill）
        
        Returns:
            KingdeeResult: 暂存结果
        """
        url = f"{self.api_url}/Kingdee.BOS.WebApi.ServicesStub.DynamicFormService.Draft.common.kdsvc"
        return await self._execute_save(url, request_body, "draft")
    
    async def _execute_save(
        self,
        url: str,
        request_body: Dict[str, Any],
        mode: str
    ) -> KingdeeResult:
        """
        执行保存/暂存操作
        
        Args:
            url: API URL
            request_body: 请求体
            mode: 模式 ("save" 或 "draft")
            
        Returns:
            KingdeeResult: 执行结果
        """
        start_time = time.time()
        
        # 确保已登录
        if not await self._ensure_logged_in():
            return KingdeeResult(
                success=False,
                error_message="金蝶登录失败",
                duration_ms=int((time.time() - start_time) * 1000),
                save_mode=mode
            )
        
        try:
            client = await self._get_client()
            response = await client.post(
                url,
                json=request_body,
                headers={'Content-Type': 'application/json'},
                cookies=self._cookies
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            result = response.json()
            response_body = json.dumps(result, ensure_ascii=False)
            
            # 解析响应
            response_status = result.get("Result", {}).get("ResponseStatus", {})
            is_success = response_status.get("IsSuccess", False)
            
            if is_success:
                # 获取返回的单据信息
                success_entities = response_status.get("SuccessEntitys", [])
                bill_no = None
                bill_id = None
                if success_entities:
                    bill_no = success_entities[0].get("Number")
                    bill_id = success_entities[0].get("Id")
                
                logger.info(f"金蝶{mode}成功: bill_no={bill_no}, bill_id={bill_id}, duration={duration_ms}ms")
                
                return KingdeeResult(
                    success=True,
                    http_status=response.status_code,
                    response_body=response_body,
                    duration_ms=duration_ms,
                    bill_no=bill_no,
                    bill_id=bill_id,
                    save_mode=mode
                )
            else:
                # 获取错误信息
                errors = response_status.get("Errors", [])
                error_messages = [e.get("Message", "") for e in errors]
                error_msg = "; ".join(error_messages) if error_messages else "未知错误"
                
                logger.warning(f"金蝶{mode}失败: {error_msg}, duration={duration_ms}ms")
                
                return KingdeeResult(
                    success=False,
                    http_status=response.status_code,
                    response_body=response_body,
                    error_message=error_msg,
                    duration_ms=duration_ms,
                    save_mode=mode
                )
                
        except httpx.TimeoutException:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"金蝶{mode}请求超时"
            logger.error(f"{error_msg}: url={url}")
            
            return KingdeeResult(
                success=False,
                error_message=error_msg,
                duration_ms=duration_ms,
                save_mode=mode
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"金蝶{mode}异常: {str(e)}"
            logger.error(error_msg)
            
            return KingdeeResult(
                success=False,
                error_message=error_msg,
                duration_ms=duration_ms,
                save_mode=mode
            )

    
    async def smart_save(self, request_body: Dict[str, Any]) -> KingdeeResult:
        """
        智能保存：根据配置的save_mode执行保存策略
        
        策略说明：
        - smart: 先尝试Save，如果因校验失败则自动降级到Draft
        - save_only: 仅使用Save接口
        - draft_only: 仅使用Draft接口
        
        Args:
            request_body: 完整的金蝶API请求体
            
        Returns:
            KingdeeResult: 保存结果
        """
        if self.save_mode == "draft_only":
            logger.info("金蝶保存模式: draft_only，直接使用Draft接口")
            return await self.draft_bill(request_body)
        
        if self.save_mode == "save_only":
            logger.info("金蝶保存模式: save_only，仅使用Save接口")
            return await self.save_bill(request_body)
        
        # smart模式：先Save，失败后自动降级Draft
        logger.info("金蝶保存模式: smart，先尝试Save接口")
        save_result = await self.save_bill(request_body)
        
        if save_result.success:
            return save_result
        
        # Save失败，检查是否为校验错误（可降级）
        # 常见的校验错误关键词
        validation_keywords = ['必填', '不能为空', '校验', '验证', 'required', 'validate']
        is_validation_error = any(
            keyword in (save_result.error_message or '').lower() 
            for keyword in validation_keywords
        )
        
        if is_validation_error:
            logger.info(f"Save因校验失败，自动降级到Draft: {save_result.error_message}")
            draft_result = await self.draft_bill(request_body)
            
            if draft_result.success:
                # 标记为降级保存
                draft_result.is_degraded = True
                draft_result.error_message = f"已降级为暂存（原因: {save_result.error_message}）"
                logger.info(f"Draft降级保存成功: bill_no={draft_result.bill_no}")
            
            return draft_result
        else:
            # 非校验错误，直接返回Save结果
            logger.warning(f"Save失败（非校验错误），不降级: {save_result.error_message}")
            return save_result


class KingdeeService:
    """
    金蝶推送服务
    
    封装KingdeeClient，提供更高级的推送功能
    """
    
    def __init__(self):
        """初始化金蝶服务"""
        self.client: Optional[KingdeeClient] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = KingdeeClient()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.close()
    
    async def push(self, request_body: Dict[str, Any]) -> KingdeeResult:
        """
        推送数据到金蝶
        
        Args:
            request_body: 管道清洗后的金蝶API请求体
            
        Returns:
            KingdeeResult: 推送结果
        """
        if not self.client:
            self.client = KingdeeClient()
        
        if not self.client.is_configured:
            return KingdeeResult(
                success=False,
                error_message="金蝶配置不完整，请检查环境变量"
            )
        
        return await self.client.smart_save(request_body)


# 便捷函数
async def push_to_kingdee(request_body: Dict[str, Any]) -> KingdeeResult:
    """
    推送数据到金蝶（便捷函数）
    
    Args:
        request_body: 管道清洗后的金蝶API请求体
        
    Returns:
        KingdeeResult: 推送结果
    """
    async with KingdeeService() as service:
        return await service.push(request_body)

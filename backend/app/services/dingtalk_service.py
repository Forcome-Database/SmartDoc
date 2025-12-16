"""
钉钉群机器人通知服务
支持发送多种事件通知到钉钉群
支持加签安全验证、规则过滤、@指定人员
"""
import httpx
import hmac
import hashlib
import base64
import urllib.parse
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.database import SessionLocal
from app.models.system_config import SystemConfig
from sqlalchemy import select

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "enabled": False,
    "webhook_url": "",
    "secret": "",
    "at_all": True,
    "at_mobiles": [],
    "notify_events": {
        "pending_audit": True,
        "audit_completed": False,
        "pipeline_success": False,
        "pipeline_failed": True,
        "push_success": False,
        "push_failed": True
    },
    "notify_rules": []  # 空数组表示全部规则
}

# 事件名称映射
EVENT_NAMES = {
    "pending_audit": "人工审核提醒",
    "audit_completed": "审核完成通知",
    "pipeline_success": "管道处理成功",
    "pipeline_failed": "管道处理失败",
    "push_success": "推送成功通知",
    "push_failed": "推送失败通知"
}


class DingTalkService:
    """钉钉群机器人服务"""

    def __init__(self):
        self.timeout = 10
        self._config_cache = None
        self._cache_time = 0
        self._cache_ttl = 60  # 缓存60秒

    async def get_config(self) -> Dict[str, Any]:
        """获取钉钉配置（带缓存）"""
        now = time.time()
        if self._config_cache and (now - self._cache_time) < self._cache_ttl:
            return self._config_cache

        try:
            async with SessionLocal() as db:
                result = await db.execute(
                    select(SystemConfig).where(
                        SystemConfig.key == "dingtalk_config")
                )
                config = result.scalar_one_or_none()
                if config and config.value:
                    self._config_cache = {**DEFAULT_CONFIG, **config.value}
                else:
                    self._config_cache = DEFAULT_CONFIG.copy()
                self._cache_time = now
                return self._config_cache
        except Exception as e:
            logger.error(f"获取钉钉配置失败: {str(e)}")
            return DEFAULT_CONFIG.copy()

    def clear_cache(self):
        """清除配置缓存"""
        self._config_cache = None
        self._cache_time = 0

    async def is_enabled(self) -> bool:
        """检查钉钉通知是否启用"""
        config = await self.get_config()
        return config.get("enabled", False)

    async def should_notify(self, event: str, rule_id: str = None) -> bool:
        """
        检查是否应该发送通知
        
        Args:
            event: 事件类型
            rule_id: 规则ID（可选）
        """
        config = await self.get_config()
        
        # 检查总开关
        if not config.get("enabled", False):
            return False
        
        # 检查事件是否启用
        notify_events = config.get("notify_events", {})
        if not notify_events.get(event, False):
            return False
        
        # 检查规则过滤
        notify_rules = config.get("notify_rules", [])
        if notify_rules and rule_id and rule_id not in notify_rules:
            return False
        
        return True

    def _generate_sign(self, secret: str, timestamp: int) -> str:
        """生成钉钉加签签名"""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        return urllib.parse.quote_plus(base64.b64encode(hmac_code).decode('utf-8'))

    def _get_signed_url(self, webhook_url: str, secret: str) -> str:
        """获取带签名的Webhook URL"""
        timestamp = int(time.time() * 1000)
        sign = self._generate_sign(secret, timestamp)
        if '?' in webhook_url:
            return f"{webhook_url}&timestamp={timestamp}&sign={sign}"
        return f"{webhook_url}?timestamp={timestamp}&sign={sign}"

    async def _send_request(
        self,
        message: Dict[str, Any],
        webhook_url: str = None,
        secret: str = None
    ) -> bool:
        """发送请求到钉钉"""
        config = await self.get_config()
        
        url = webhook_url or config.get("webhook_url", "")
        sec = secret or config.get("secret", "")
        
        if not url:
            logger.warning("钉钉Webhook URL未配置")
            return False
        
        # 添加签名
        final_url = self._get_signed_url(url, sec) if sec else url
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    final_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    return True
                logger.error(f"钉钉消息发送失败: {result.get('errmsg')}")
            else:
                logger.error(f"钉钉消息发送失败: HTTP {response.status_code}")
            return False
        except Exception as e:
            logger.error(f"钉钉消息发送异常: {str(e)}")
            return False

    async def send_markdown(
        self,
        title: str,
        text: str,
        at_all: bool = None,
        at_mobiles: List[str] = None
    ) -> bool:
        """发送Markdown消息"""
        config = await self.get_config()
        
        if not config.get("enabled", False):
            return False
        
        # 使用配置的@设置，除非明确指定
        if at_all is None:
            at_all = config.get("at_all", True)
        if at_mobiles is None:
            at_mobiles = config.get("at_mobiles", [])
        
        # 钉钉Markdown消息@人需要在文本中包含@手机号
        at_text = ""
        if at_mobiles and len(at_mobiles) > 0:
            at_text = "\n\n" + " ".join([f"@{mobile}" for mobile in at_mobiles])
        
        message = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text + at_text},
            "at": {"isAtAll": at_all, "atMobiles": at_mobiles}
        }
        
        return await self._send_request(message)

    async def notify_pending_audit(
        self,
        task_id: str,
        file_name: str,
        rule_id: str,
        rule_name: str,
        audit_reasons: List[Dict],
        page_count: int = 1
    ) -> bool:
        """发送人工审核通知"""
        if not await self.should_notify("pending_audit", rule_id):
            return False
        
        reasons_text = self._format_reasons(audit_reasons)
        title = "📋 文档待审核通知"
        text = f"""### {title}

**任务ID**: {task_id}

**文件名**: {file_name}

**规则**: {rule_name}

**页数**: {page_count}

**审核原因**:{reasons_text}

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
请及时处理待审核任务
"""
        return await self.send_markdown(title, text)

    async def notify_audit_completed(
        self,
        task_id: str,
        file_name: str,
        rule_id: str,
        rule_name: str,
        status: str,
        auditor: str = None
    ) -> bool:
        """发送审核完成通知"""
        if not await self.should_notify("audit_completed", rule_id):
            return False
        
        status_text = "✅ 审核通过" if status == "completed" else "❌ 已驳回"
        title = f"📝 审核完成 - {status_text}"
        text = f"""### {title}

**任务ID**: {task_id}

**文件名**: {file_name}

**规则**: {rule_name}

**审核结果**: {status_text}

**审核人**: {auditor or '系统'}

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return await self.send_markdown(title, text)

    async def notify_pipeline_result(
        self,
        task_id: str,
        file_name: str,
        rule_id: str,
        rule_name: str,
        success: bool,
        error_message: str = None
    ) -> bool:
        """发送管道处理结果通知"""
        event = "pipeline_success" if success else "pipeline_failed"
        if not await self.should_notify(event, rule_id):
            return False
        
        if success:
            title = "✅ 管道处理成功"
            text = f"""### {title}

**任务ID**: {task_id}

**文件名**: {file_name}

**规则**: {rule_name}

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            title = "❌ 管道处理失败"
            text = f"""### {title}

**任务ID**: {task_id}

**文件名**: {file_name}

**规则**: {rule_name}

**错误信息**: {error_message or '未知错误'}

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
请检查管道配置和数据格式
"""
        return await self.send_markdown(title, text)

    async def notify_push_result(
        self,
        task_id: str,
        file_name: str,
        rule_id: str,
        rule_name: str,
        success: bool,
        webhook_name: str = None,
        error_message: str = None
    ) -> bool:
        """发送推送结果通知"""
        event = "push_success" if success else "push_failed"
        if not await self.should_notify(event, rule_id):
            return False
        
        if success:
            title = "✅ 数据推送成功"
            text = f"""### {title}

**任务ID**: {task_id}

**文件名**: {file_name}

**规则**: {rule_name}

**目标**: {webhook_name or '默认Webhook'}

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            title = "❌ 数据推送失败"
            text = f"""### {title}

**任务ID**: {task_id}

**文件名**: {file_name}

**规则**: {rule_name}

**目标**: {webhook_name or '默认Webhook'}

**错误信息**: {error_message or '未知错误'}

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
任务已进入死信队列，请手动处理
"""
        return await self.send_markdown(title, text)

    def _format_reasons(self, audit_reasons: List[Dict], max_count: int = 5) -> str:
        """格式化审核原因"""
        reasons_text = ""
        for reason in audit_reasons[:max_count]:
            reason_type = reason.get('type', '')
            field = reason.get('field', '')
            message = reason.get('message', '')
            
            if reason_type == 'validation_error':
                reasons_text += f"\n> - 校验错误: {field} - {message}"
            elif reason_type == 'confidence_low':
                reasons_text += f"\n> - 置信度低: {field} - {message}"
            else:
                reasons_text += f"\n> - {message}"
        
        if len(audit_reasons) > max_count:
            reasons_text += f"\n> - ...还有 {len(audit_reasons) - max_count} 个问题"
        
        return reasons_text or "\n> - 无"

    @staticmethod
    def generate_sign_for_test(secret: str, webhook_url: str) -> str:
        """为测试生成带签名的URL"""
        timestamp = int(time.time() * 1000)
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode('utf-8'))
        
        if '?' in webhook_url:
            return f"{webhook_url}&timestamp={timestamp}&sign={sign}"
        return f"{webhook_url}?timestamp={timestamp}&sign={sign}"


# 全局服务实例
dingtalk_service = DingTalkService()

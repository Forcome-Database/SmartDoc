"""
安全模块
提供密码加密、JWT Token管理、API Key管理、数据加密和HMAC签名功能
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import secrets
import hashlib
import hmac
import base64
from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.core.config import settings


# ============================================================================
# 5.1 密码加密
# ============================================================================

# 密码加密上下文（使用bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    使用bcrypt算法对密码进行哈希加密
    
    Args:
        password: 明文密码
        
    Returns:
        加密后的密码哈希值
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# 5.2 JWT Token管理
# ============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    生成JWT访问令牌
    
    Args:
        data: 要编码到Token中的数据（通常包含user_id、username、role等）
        expires_delta: Token过期时间，默认使用配置中的值
        
    Returns:
        JWT Token字符串
    """
    to_encode = data.copy()
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    # 生成JWT Token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证JWT Token并返回解码后的数据
    
    Args:
        token: JWT Token字符串
        
    Returns:
        解码后的Token数据，如果验证失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT Token，提取用户信息
    不验证签名和过期时间，仅用于提取信息
    
    Args:
        token: JWT Token字符串
        
    Returns:
        解码后的Token数据
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_signature": True, "verify_exp": True}
        )
        return payload
    except JWTError:
        return None


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    从Token中提取用户信息
    
    Args:
        token: JWT Token字符串
        
    Returns:
        用户信息字典，包含user_id、username、role等
    """
    payload = verify_token(token)
    if payload is None:
        return None
    
    return {
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "role": payload.get("role"),
        "email": payload.get("email")
    }


# ============================================================================
# 5.3 API Key管理
# ============================================================================

def generate_api_key() -> Tuple[str, str]:
    """
    生成API Key（key_id和secret）
    
    Returns:
        (key_id, secret) 元组
        - key_id: 公开的Key标识符（32字符）
        - secret: 私密的Secret密钥（64字符）
    """
    # 生成key_id（使用前缀 + 随机字符串）
    key_id = f"idp_{secrets.token_urlsafe(24)}"
    
    # 生成secret（更长的随机字符串）
    secret = secrets.token_urlsafe(48)
    
    return key_id, secret


def hash_api_key_secret(secret: str) -> str:
    """
    对API Key的Secret进行哈希存储
    
    Args:
        secret: API Key的Secret
        
    Returns:
        哈希后的Secret
    """
    return pwd_context.hash(secret)


def verify_api_key_secret(plain_secret: str, hashed_secret: str) -> bool:
    """
    验证API Key的Secret是否正确
    
    Args:
        plain_secret: 明文Secret
        hashed_secret: 哈希后的Secret
        
    Returns:
        Secret是否匹配
    """
    return pwd_context.verify(plain_secret, hashed_secret)


def mask_api_key_secret(secret: str, visible_chars: int = 8) -> str:
    """
    遮蔽API Key Secret，仅显示前几位
    
    Args:
        secret: 完整的Secret
        visible_chars: 显示的字符数
        
    Returns:
        遮蔽后的Secret（如：idp_abc1***）
    """
    if len(secret) <= visible_chars:
        return secret
    
    return secret[:visible_chars] + "***"


# ============================================================================
# 5.4 数据加密服务（AES-256）
# ============================================================================

class DataEncryption:
    """数据加密服务类"""
    
    def __init__(self):
        """初始化加密器"""
        # 如果配置中有加密密钥，使用配置的密钥
        # 否则使用SECRET_KEY派生加密密钥
        if settings.ENCRYPTION_KEY:
            encryption_key = settings.ENCRYPTION_KEY.encode()
        else:
            # 使用PBKDF2从SECRET_KEY派生加密密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'idp_platform_salt',  # 固定salt，生产环境应使用配置
                iterations=100000,
                backend=default_backend()
            )
            encryption_key = kdf.derive(settings.SECRET_KEY.encode())
        
        # 创建Fernet加密器（使用AES-256）
        self.cipher = Fernet(base64.urlsafe_b64encode(encryption_key))
    
    def encrypt(self, plaintext: str) -> str:
        """
        使用AES-256加密数据
        
        Args:
            plaintext: 明文字符串
            
        Returns:
            加密后的Base64编码字符串
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        使用AES-256解密数据
        
        Args:
            ciphertext: 加密后的Base64编码字符串
            
        Returns:
            解密后的明文字符串
        """
        if not ciphertext:
            return ""
        
        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except Exception:
            # 解密失败，返回空字符串
            return ""


# 创建全局加密器实例
data_encryption = DataEncryption()


def encrypt_sensitive_data(data: str) -> str:
    """
    加密敏感数据（Secret Key、API Key等）
    
    Args:
        data: 明文数据
        
    Returns:
        加密后的数据
    """
    return data_encryption.encrypt(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """
    解密敏感数据
    
    Args:
        encrypted_data: 加密后的数据
        
    Returns:
        解密后的明文数据
    """
    return data_encryption.decrypt(encrypted_data)


# ============================================================================
# 5.5 HMAC签名服务
# ============================================================================

def generate_signature(
    data: str,
    secret_key: str,
    algorithm: str = "sha256"
) -> str:
    """
    生成HMAC-SHA256签名
    用于Webhook推送签名
    
    Args:
        data: 要签名的数据（通常是请求体JSON字符串）
        secret_key: 签名密钥
        algorithm: 哈希算法，默认sha256
        
    Returns:
        十六进制格式的签名字符串
    """
    # 将数据和密钥转换为字节
    data_bytes = data.encode('utf-8')
    key_bytes = secret_key.encode('utf-8')
    
    # 生成HMAC签名
    signature = hmac.new(
        key_bytes,
        data_bytes,
        getattr(hashlib, algorithm)
    ).hexdigest()
    
    return signature


def verify_signature(
    data: str,
    signature: str,
    secret_key: str,
    algorithm: str = "sha256"
) -> bool:
    """
    验证HMAC签名
    
    Args:
        data: 原始数据
        signature: 待验证的签名
        secret_key: 签名密钥
        algorithm: 哈希算法，默认sha256
        
    Returns:
        签名是否有效
    """
    # 生成期望的签名
    expected_signature = generate_signature(data, secret_key, algorithm)
    
    # 使用恒定时间比较，防止时序攻击
    return hmac.compare_digest(signature, expected_signature)


def generate_webhook_signature(
    request_body: str,
    secret_key: str
) -> str:
    """
    生成Webhook推送签名
    使用HMAC-SHA256算法
    
    Args:
        request_body: 请求体JSON字符串
        secret_key: Webhook配置的Secret Key
        
    Returns:
        签名字符串（格式：sha256=<signature>）
    """
    signature = generate_signature(request_body, secret_key, "sha256")
    return f"sha256={signature}"


def verify_webhook_signature(
    request_body: str,
    signature_header: str,
    secret_key: str
) -> bool:
    """
    验证Webhook推送签名
    
    Args:
        request_body: 请求体JSON字符串
        signature_header: X-IDP-Signature请求头的值
        secret_key: Webhook配置的Secret Key
        
    Returns:
        签名是否有效
    """
    # 解析签名头（格式：sha256=<signature>）
    if not signature_header.startswith("sha256="):
        return False
    
    received_signature = signature_header[7:]  # 去掉"sha256="前缀
    
    # 生成期望的签名
    expected_signature = generate_signature(request_body, secret_key, "sha256")
    
    # 验证签名
    return hmac.compare_digest(received_signature, expected_signature)


# ============================================================================
# 工具函数
# ============================================================================

def generate_random_string(length: int = 32) -> str:
    """
    生成随机字符串
    
    Args:
        length: 字符串长度
        
    Returns:
        随机字符串
    """
    return secrets.token_urlsafe(length)


def calculate_file_hash(file_content: bytes) -> str:
    """
    计算文件的SHA256哈希值
    
    Args:
        file_content: 文件内容（字节）
        
    Returns:
        SHA256哈希值（十六进制字符串）
    """
    return hashlib.sha256(file_content).hexdigest()


def generate_task_key(file_hash: str, rule_id: str, rule_version: str) -> str:
    """
    生成任务唯一标识Key（用于去重）
    
    Args:
        file_hash: 文件SHA256哈希
        rule_id: 规则ID
        rule_version: 规则版本
        
    Returns:
        任务Key
    """
    combined = f"{file_hash}:{rule_id}:{rule_version}"
    return hashlib.sha256(combined.encode()).hexdigest()


# ============================================================================
# 新星肉羊育种系统 - 安全中间件
# NovaBreed Sheep System - Security Middleware
#
# 文件: security.py
# 功能: 安全相关中间件和工具函数
# ============================================================================

import hashlib
import hmac
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
import logging

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, validator, field_validator
import bleach

from config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# 密码处理
# Password Handling
# ============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    安全地哈希密码
    
    使用 bcrypt 算法，自动加盐
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    验证密码强度
    
    返回: (是否有效, 错误信息)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"密码长度至少 {settings.PASSWORD_MIN_LENGTH} 位"
    
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, "密码必须包含大写字母"
    
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False, "密码必须包含小写字母"
    
    if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        return False, "密码必须包含数字"
    
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "密码必须包含特殊字符"
    
    return True, ""

# ============================================================================
# JWT Token 处理
# JWT Token Handling
# ============================================================================

security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    """解码并验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[dict]:
    """
    获取当前用户
    
    从 Authorization header 中提取并验证 JWT token
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    强制要求认证
    
    如果未认证则抛出 401 错误
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# ============================================================================
# 输入验证和清理
# Input Validation and Sanitization
# ============================================================================

def sanitize_html(text: str) -> str:
    """
    清理 HTML 内容，防止 XSS 攻击
    
    仅允许安全的标签和属性
    """
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    allowed_attrs = {}
    
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，防止路径遍历攻击
    """
    # 移除路径分隔符
    filename = filename.replace('/', '').replace('\\', '')
    # 移除特殊字符
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    # 限制长度
    return filename[:255]

def validate_sql_identifier(identifier: str) -> bool:
    """
    验证 SQL 标识符（表名、列名等）
    
    防止 SQL 注入
    """
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier))

class SecureInput(BaseModel):
    """安全输入基类，自动清理 HTML"""
    
    @field_validator('*', mode='before')
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            # 移除潜在的危险字符
            v = v.strip()
            # 检测潜在的脚本注入
            if re.search(r'<script|javascript:|on\w+=', v, re.IGNORECASE):
                raise ValueError("检测到潜在的脚本注入")
        return v

# ============================================================================
# 速率限制
# Rate Limiting
# ============================================================================

class RateLimiter:
    """
    简单的内存速率限制器
    
    生产环境建议使用 Redis 实现
    """
    
    def __init__(self):
        self._requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(
        self, 
        key: str, 
        max_requests: int = 100, 
        window_seconds: int = 60
    ) -> bool:
        """
        检查是否允许请求
        
        Args:
            key: 限制键（通常是IP地址或用户ID）
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
        
        Returns:
            是否允许请求
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        if key not in self._requests:
            self._requests[key] = []
        
        # 清理过期的请求记录
        self._requests[key] = [
            t for t in self._requests[key] if t > window_start
        ]
        
        if len(self._requests[key]) >= max_requests:
            return False
        
        self._requests[key].append(now)
        return True
    
    def get_remaining(
        self, 
        key: str, 
        max_requests: int = 100, 
        window_seconds: int = 60
    ) -> int:
        """获取剩余请求次数"""
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        if key not in self._requests:
            return max_requests
        
        current_count = len([
            t for t in self._requests[key] if t > window_start
        ])
        
        return max(0, max_requests - current_count)

# 全局速率限制器实例
rate_limiter = RateLimiter()

async def check_rate_limit(request: Request, max_requests: int = 100):
    """
    速率限制依赖
    
    用于保护 API 端点免受滥用
    """
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip, max_requests=max_requests):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后重试",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Remaining": "0"
            }
        )

# ============================================================================
# CSRF 保护
# CSRF Protection
# ============================================================================

def generate_csrf_token() -> str:
    """生成 CSRF 令牌"""
    return secrets.token_urlsafe(32)

def verify_csrf_token(token: str, stored_token: str) -> bool:
    """验证 CSRF 令牌"""
    return hmac.compare_digest(token, stored_token)

# ============================================================================
# API 密钥验证
# API Key Verification
# ============================================================================

def generate_api_key() -> str:
    """生成 API 密钥"""
    return f"nova_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """哈希 API 密钥用于存储"""
    return hashlib.sha256(api_key.encode()).hexdigest()

# ============================================================================
# 安全日志
# Security Logging
# ============================================================================

def log_security_event(
    event_type: str,
    description: str,
    request: Optional[Request] = None,
    user_id: Optional[int] = None,
    severity: str = "INFO"
):
    """
    记录安全事件
    
    用于审计和入侵检测
    """
    log_data = {
        "event_type": event_type,
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "severity": severity,
        "user_id": user_id
    }
    
    if request:
        log_data.update({
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "path": str(request.url.path),
            "method": request.method
        })
    
    if severity == "WARNING":
        logger.warning(f"Security Event: {log_data}")
    elif severity == "ERROR":
        logger.error(f"Security Event: {log_data}")
    elif severity == "CRITICAL":
        logger.critical(f"Security Event: {log_data}")
    else:
        logger.info(f"Security Event: {log_data}")

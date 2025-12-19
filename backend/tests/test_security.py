# ============================================================================
# 新星肉羊育种系统 - 安全性测试
# NovaBreed Sheep System - Security Tests
# ============================================================================

import pytest
import re
from unittest.mock import MagicMock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security import (
    hash_password, verify_password, validate_password_strength,
    create_access_token, create_refresh_token, decode_token,
    sanitize_html, sanitize_filename, validate_sql_identifier,
    RateLimiter, generate_csrf_token, verify_csrf_token,
    generate_api_key, hash_api_key, log_security_event
)


class TestPasswordSecurity:
    """密码安全测试"""
    
    def test_hash_password_returns_hash(self):
        """测试密码哈希返回哈希值"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt哈希较长
        assert hashed.startswith('$2')  # bcrypt格式
    
    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) == True
    
    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password("WrongPassword", hashed) == False
    
    def test_password_strength_valid(self):
        """测试有效密码强度"""
        valid, msg = validate_password_strength("StrongP@ss123")
        assert valid == True
        assert msg == ""
    
    def test_password_strength_too_short(self):
        """测试密码过短"""
        valid, msg = validate_password_strength("Ab1!")
        assert valid == False
        assert "长度" in msg
    
    def test_same_password_different_hash(self):
        """测试相同密码产生不同哈希（加盐）"""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # 加盐使每次哈希不同


class TestJWTSecurity:
    """JWT安全测试"""
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        data = {"sub": "user123", "roles": ["admin"]}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
        assert token.count('.') == 2  # JWT格式: header.payload.signature
    
    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert token.count('.') == 2
    
    def test_decode_valid_token(self):
        """测试解码有效令牌"""
        data = {"sub": "user123", "roles": ["admin"]}
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert "exp" in decoded
        assert "iat" in decoded
    
    def test_decode_invalid_token(self):
        """测试解码无效令牌"""
        result = decode_token("invalid.token.here")
        assert result is None
    
    def test_token_contains_type(self):
        """测试令牌包含类型标识"""
        access_token = create_access_token({"sub": "user"})
        refresh_token = create_refresh_token({"sub": "user"})
        
        access_decoded = decode_token(access_token)
        refresh_decoded = decode_token(refresh_token)
        
        assert access_decoded["type"] == "access"
        assert refresh_decoded["type"] == "refresh"


class TestInputSanitization:
    """输入清理测试"""
    
    def test_sanitize_html_removes_script(self):
        """测试HTML清理移除脚本标签"""
        malicious = '<script>alert("XSS")</script>Hello'
        cleaned = sanitize_html(malicious)
        
        assert '<script>' not in cleaned
        assert 'alert' not in cleaned
        assert 'Hello' in cleaned
    
    def test_sanitize_html_keeps_safe_tags(self):
        """测试HTML清理保留安全标签"""
        safe_html = '<b>Bold</b> and <i>italic</i>'
        cleaned = sanitize_html(safe_html)
        
        assert '<b>' in cleaned
        assert '<i>' in cleaned
    
    def test_sanitize_html_removes_onclick(self):
        """测试HTML清理移除事件属性"""
        malicious = '<div onclick="malicious()">Click me</div>'
        cleaned = sanitize_html(malicious)
        
        assert 'onclick' not in cleaned
    
    def test_sanitize_filename_removes_path_traversal(self):
        """测试文件名清理移除路径遍历"""
        dangerous = '../../../etc/passwd'
        cleaned = sanitize_filename(dangerous)
        
        assert '..' not in cleaned
        assert '/' not in cleaned
        assert '\\' not in cleaned
    
    def test_sanitize_filename_limits_length(self):
        """测试文件名清理限制长度"""
        long_name = 'a' * 500 + '.txt'
        cleaned = sanitize_filename(long_name)
        
        assert len(cleaned) <= 255
    
    def test_validate_sql_identifier_valid(self):
        """测试SQL标识符验证-有效"""
        assert validate_sql_identifier('farm_name') == True
        assert validate_sql_identifier('id') == True
        assert validate_sql_identifier('_private') == True
    
    def test_validate_sql_identifier_invalid(self):
        """测试SQL标识符验证-无效"""
        assert validate_sql_identifier('1starts_with_number') == False
        assert validate_sql_identifier('has spaces') == False
        assert validate_sql_identifier('has-dashes') == False
        assert validate_sql_identifier("'; DROP TABLE --") == False


class TestRateLimiting:
    """速率限制测试"""
    
    def test_rate_limiter_allows_initial_requests(self):
        """测试速率限制允许初始请求"""
        limiter = RateLimiter()
        
        for _ in range(5):
            assert limiter.is_allowed("test_ip", max_requests=10) == True
    
    def test_rate_limiter_blocks_excess_requests(self):
        """测试速率限制阻止过多请求"""
        limiter = RateLimiter()
        
        # 发送最大数量的请求
        for _ in range(10):
            limiter.is_allowed("test_ip2", max_requests=10)
        
        # 第11个请求应该被阻止
        assert limiter.is_allowed("test_ip2", max_requests=10) == False
    
    def test_rate_limiter_different_keys_independent(self):
        """测试不同键独立限制"""
        limiter = RateLimiter()
        
        # 用尽一个IP的配额
        for _ in range(5):
            limiter.is_allowed("ip1", max_requests=5)
        
        assert limiter.is_allowed("ip1", max_requests=5) == False
        assert limiter.is_allowed("ip2", max_requests=5) == True
    
    def test_get_remaining_requests(self):
        """测试获取剩余请求次数"""
        limiter = RateLimiter()
        
        limiter.is_allowed("test_ip3", max_requests=10)
        limiter.is_allowed("test_ip3", max_requests=10)
        
        remaining = limiter.get_remaining("test_ip3", max_requests=10)
        assert remaining == 8


class TestCSRFProtection:
    """CSRF保护测试"""
    
    def test_generate_csrf_token(self):
        """测试生成CSRF令牌"""
        token = generate_csrf_token()
        
        assert isinstance(token, str)
        assert len(token) >= 32
    
    def test_verify_csrf_token_valid(self):
        """测试验证有效CSRF令牌"""
        token = generate_csrf_token()
        
        assert verify_csrf_token(token, token) == True
    
    def test_verify_csrf_token_invalid(self):
        """测试验证无效CSRF令牌"""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        
        assert verify_csrf_token(token1, token2) == False
    
    def test_csrf_tokens_unique(self):
        """测试CSRF令牌唯一"""
        tokens = [generate_csrf_token() for _ in range(100)]
        unique_tokens = set(tokens)
        
        assert len(unique_tokens) == len(tokens)


class TestAPIKeyManagement:
    """API密钥管理测试"""
    
    def test_generate_api_key_format(self):
        """测试API密钥格式"""
        key = generate_api_key()
        
        assert key.startswith('nova_')
        assert len(key) > 40
    
    def test_generate_api_key_unique(self):
        """测试API密钥唯一"""
        keys = [generate_api_key() for _ in range(50)]
        unique_keys = set(keys)
        
        assert len(unique_keys) == len(keys)
    
    def test_hash_api_key(self):
        """测试API密钥哈希"""
        key = generate_api_key()
        hashed = hash_api_key(key)
        
        assert hashed != key
        assert len(hashed) == 64  # SHA256输出长度


class TestSecurityLogging:
    """安全日志测试"""
    
    def test_log_security_event_basic(self):
        """测试基本安全事件日志"""
        # 这个测试主要确保函数不会抛出异常
        log_security_event(
            event_type="LOGIN_ATTEMPT",
            description="User login attempt",
            user_id=123,
            severity="INFO"
        )
    
    def test_log_security_event_with_request(self):
        """测试带请求信息的安全事件日志"""
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "Mozilla/5.0"
        mock_request.url.path = "/api/v1/login"
        mock_request.method = "POST"
        
        log_security_event(
            event_type="FAILED_LOGIN",
            description="Failed login attempt",
            request=mock_request,
            severity="WARNING"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

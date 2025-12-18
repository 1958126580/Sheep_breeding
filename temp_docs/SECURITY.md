# Security Policy - 安全策略

## Supported Versions - 支持的版本

We release patches for security vulnerabilities for the following versions:

我们为以下版本提供安全补丁：

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability - 报告漏洞

### English

We take the security of the NovaBreed Sheep System seriously. If you believe you have found a security vulnerability, please report it to us as described below.

#### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **1958126580@qq.com**

Include the following information:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

#### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Communication**: We will keep you informed about our progress
- **Fix Timeline**: We aim to release a fix within 30 days for critical vulnerabilities
- **Credit**: We will credit you in our security advisory (unless you prefer to remain anonymous)

### 中文

我们非常重视新星肉羊育种系统的安全性。如果您发现了安全漏洞，请按照以下方式向我们报告。

#### 如何报告

**请不要通过公开的 GitHub Issues 报告安全漏洞。**

请通过电子邮件报告：**1958126580@qq.com**

请包含以下信息：

- 问题类型（如：缓冲区溢出、SQL 注入、跨站脚本等）
- 与问题相关的源文件完整路径
- 受影响源代码的位置（标签/分支/提交或直接 URL）
- 重现问题所需的任何特殊配置
- 重现问题的分步说明
- 概念验证或漏洞利用代码（如果可能）
- 问题的影响，包括攻击者可能如何利用它

#### 您可以期待

- **确认回复**: 我们将在 48 小时内确认收到您的漏洞报告
- **沟通**: 我们会及时告知您我们的进展
- **修复时间**: 我们力争在 30 天内发布关键漏洞的修复
- **致谢**: 我们会在安全公告中感谢您（除非您希望保持匿名）

## Security Best Practices - 安全最佳实践

### For Users - 用户

1. **Keep Updated** - Always use the latest version
   - 始终使用最新版本
2. **Strong Passwords** - Use strong, unique passwords
   - 使用强密码和唯一密码
3. **HTTPS Only** - Always use HTTPS in production
   - 生产环境始终使用 HTTPS
4. **Regular Backups** - Maintain regular database backups
   - 定期备份数据库
5. **Access Control** - Implement proper role-based access control
   - 实施适当的基于角色的访问控制

### For Developers - 开发者

1. **Input Validation** - Always validate and sanitize user input
   - 始终验证和清理用户输入
2. **SQL Injection** - Use parameterized queries (SQLAlchemy ORM)
   - 使用参数化查询（SQLAlchemy ORM）
3. **XSS Prevention** - Escape output and use Content Security Policy
   - 转义输出并使用内容安全策略
4. **Authentication** - Use JWT tokens with proper expiration
   - 使用带有适当过期时间的 JWT 令牌
5. **Secrets Management** - Never commit secrets to version control
   - 永远不要将密钥提交到版本控制
6. **Dependencies** - Regularly update dependencies
   - 定期更新依赖项
7. **Code Review** - All code changes must be reviewed
   - 所有代码更改必须经过审查

### For Administrators - 管理员

1. **Firewall** - Configure firewall rules properly
   - 正确配置防火墙规则
2. **Monitoring** - Set up security monitoring and alerting
   - 设置安全监控和警报
3. **Logging** - Enable comprehensive logging
   - 启用全面的日志记录
4. **Encryption** - Use encryption for data at rest and in transit
   - 对静态和传输中的数据使用加密
5. **Regular Audits** - Conduct regular security audits
   - 进行定期安全审计

## Known Security Considerations - 已知安全注意事项

### Environment Variables - 环境变量

- **Never commit `.env` files** to version control
  - 永远不要将 `.env` 文件提交到版本控制
- Store sensitive configuration in environment variables
  - 将敏感配置存储在环境变量中
- Use different credentials for development and production
  - 开发和生产使用不同的凭据

### Database Security - 数据库安全

- Use strong database passwords
  - 使用强数据库密码
- Limit database user permissions
  - 限制数据库用户权限
- Enable SSL/TLS for database connections
  - 为数据库连接启用 SSL/TLS
- Regular database backups
  - 定期数据库备份

### API Security - API 安全

- Implement rate limiting
  - 实施速率限制
- Use API keys or JWT tokens
  - 使用 API 密钥或 JWT 令牌
- Validate all input data
  - 验证所有输入数据
- Return appropriate error messages (don't leak sensitive info)
  - 返回适当的错误消息（不要泄露敏感信息）

## Security Updates - 安全更新

Security updates will be announced through:

- GitHub Security Advisories
- Release notes in CHANGELOG.md
- Email notifications to registered users

安全更新将通过以下方式公布：

- GitHub 安全公告
- CHANGELOG.md 中的发布说明
- 向注册用户发送电子邮件通知

## Compliance - 合规性

This system is designed with the following security standards in mind:

- OWASP Top 10
- CWE/SANS Top 25
- General Data Protection Regulation (GDPR) principles

本系统在设计时考虑了以下安全标准：

- OWASP Top 10
- CWE/SANS Top 25
- 通用数据保护条例（GDPR）原则

## Contact - 联系方式

For security-related inquiries:

- Email: 1958126580@qq.com
- GitHub: https://github.com/1958126580/Sheep_breeding

安全相关咨询：

- 邮箱：1958126580@qq.com
- GitHub：https://github.com/1958126580/Sheep_breeding

---

**Thank you for helping keep NovaBreed Sheep System secure!**

**感谢您帮助保护新星肉羊育种系统的安全！**

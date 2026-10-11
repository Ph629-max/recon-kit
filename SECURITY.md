# 安全政策

## 支持范围

| 版本 | 支持 |
|------|------|
| 0.1.x | ✅ |

## 报告安全漏洞

**请不要通过公开 Issue 报告安全问题。**

请通过以下方式之一私下联系：

- 使用 GitHub 的 [私密漏洞报告](https://docs.github.com/zh/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) 功能（本仓库 Security 标签页 → Report a vulnerability）
- 或发送邮件至仓库所有者邮箱（见 GitHub 个人主页）

请尽量包含：

1. 问题类型与影响
2. 复现步骤（最小可复现示例）
3. 受影响版本
4. 你的修复建议（如有）

我会在 **72 小时内**确认收到，并在修复后致谢（如果你希望署名）。

## 本工具自身的攻击面

recon-kit 会解析来自网络的不可信数据（crt.sh 响应、目标响应体），相关风险点：

| 风险 | 现状 |
|------|------|
| 正则回溯（ReDoS） | 规则正则由用户提供，内置规则已避免嵌套量词；如发现恶意规则可导致卡顿请上报 |
| 响应体过大 | `http_get` 有 `max_bytes` 上限（默认 256 KB） |
| 规则文件注入 | 规则为 JSON，仅作正则使用；不执行任何代码 |
| SSRF | 工具会请求用户指定的 URL，这是其设计用途；请勿对未授权目标使用 |

## 使用者的责任

本工具用于**自有资产**或**已获书面授权**的测试。

使用者需确保测试行为符合当地法律法规和目标方的授权范围。作者不对未授权的使用承担责任。

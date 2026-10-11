# 贡献指南

感谢你有兴趣改进 recon-kit。这是一个小工具，保持简单是它的设计目标之一。

## 开发环境

```bash
git clone https://github.com/Ph629-max/recon-kit.git
cd recon-kit

# 运行时零依赖；测试需要 pytest
pip install -r requirements-dev.txt

# 跑测试
pytest -q

# 离线端到端冒烟（本地起 HTTP 服务，不访问外网）
python tests/smoke_offline.py
```

## 设计原则

提 PR 前请先确认你的改动符合这几条，否则可能被拒：

1. **运行时保持零第三方依赖。** 只用标准库。需要额外能力时，做成可选依赖并优雅降级。
2. **批量场景不抛异常。** 网络错误通过返回值传递（如 `error` 字段），不要中断整个任务。
3. **不把"失败"伪装成"没有结果"。** 数据源故障必须显式暴露（见 `warnings` 机制）。
4. **结论要有证据。** 任何"命中/发现"都应能给出原始片段或可复现的请求。
5. **测试必须离线。** 单元测试不允许访问网络，否则 CI 会不稳定。

## 新增指纹规则

规则文件：`reconkit/rules/fingerprints.json`

```json
{
  "name": "示例框架",
  "category": "framework",
  "headers": { "X-Powered-By": "Example/[0-9.]+" },
  "body": ["example-framework"],
  "cookies": ["example_session"],
  "title": ["Example Admin"]
}
```

| 字段 | 说明 |
|------|------|
| `name` / `category` | 技术名 / 分类 |
| `headers` | `{"响应头名": "正则"}`（大小写不敏感） |
| `body` | 响应体正则列表 |
| `cookies` | Set-Cookie 正则列表 |
| `title` | 页面标题正则列表 |

**提交规则请附带一个能命中它的响应样例**（去掉真实域名），便于评审。

## 提交 PR

1. 从 `main` 切分支，命名如 `feat/xxx`、`fix/xxx`
2. 改动请配套测试（新增函数 → 新增用例）
3. 确保 `pytest -q` 与 `python tests/smoke_offline.py` 都通过
4. PR 描述里说明：**解决了什么问题** + **怎么验证**

## 提交信息

用 [Conventional Commits](https://www.conventionalcommits.org/) 风格：

```
feat: 新增 TLS 证书信息采集
fix: 修正被动源失败时被误判为无结果
docs: 补充规则文件格式说明
test: 增加 crt.sh 解析的畸形输入用例
```

## 授权与合规

本工具用于**自有资产**或**已获书面授权**的安全测试。

**不接受**以下类型的贡献：
- 针对特定真实目标的硬编码逻辑
- 绕过鉴权、批量拖库、DoS 等破坏性功能
- 任何未授权攻击场景的"便利化"封装

## 报告问题

安全问题请走 [SECURITY.md](SECURITY.md)，不要开公开 Issue。

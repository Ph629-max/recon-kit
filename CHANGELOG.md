# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Planned
- TLS 证书信息采集（颁发者 / SAN / 有效期）
- 端口存活快速探测
- Markdown 报告导出
- 可选依赖 dnspython，支持 CNAME / TXT 记录

## [0.1.0] - 2026-10-11

首个版本。

### Added
- 子域名枚举
  - 被动：证书透明度日志（crt.sh）查询与解析
  - 主动：字典并发解析（线程池，可调线程数与超时）
- 技术栈指纹识别
  - 35 条内置规则，覆盖 Web 服务器 / 框架 / 语言 / CMS / 中间件 / CI / CDN-WAF / 面板
  - 支持 headers / body / cookies / title 四个维度，任一命中即算匹配
  - 每条命中附带**命中的原始片段**作为证据
  - 规则文件为 JSON，可自定义
- 输出渲染：等宽表格（CJK 宽度感知）/ Markdown / JSON
- CLI：`subdomains`、`fingerprint` 两个子命令
- 打包：`pyproject.toml`，支持 `pip install .` 并生成 `reconkit` 命令
- 测试：18 个离线单元测试 + 离线端到端冒烟测试
- CI：GitHub Actions 在 Python 3.8 ~ 3.13 六个版本上跑测试，并验证包可构建安装

### Fixed
- **被动数据源故障与"无结果"不可区分**：crt.sh 返回 HTTP 502 时，旧实现返回空集合，
  与"该域名确实没有子域记录"完全一样，会导致使用者把服务端故障误读为
  "目标很干净"。现改为返回结构化的 `warnings`，终端打印 `[!]` 告警，JSON 输出含 `warnings` 字段。
  （此问题由一次真实目标测试发现，详见 README 的"设计取舍"）
- 离线冒烟测试的 `sys.path` 计算错误：脚本被移入 `tests/` 后，`dirname(__file__)` 不再指向仓库根，
  导致 `ModuleNotFoundError`。CI 在六个版本上同时暴露了该问题。

[Unreleased]: https://github.com/Ph629-max/recon-kit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Ph629-max/recon-kit/releases/tag/v0.1.0

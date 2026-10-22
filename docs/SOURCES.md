# 官方依据与证据边界

核对日期：2026-10-21（America/Los_Angeles）。页面可能继续更新。以下仅列支持架构决定的原始来源，未复制全文。

| 编号 | 官方来源 | 本次据此确认 | 不能由此推断 |
|---|---|---|---|
| S1 | [Android：Foreground service types](https://developer.android.com/develop/background-work/services/fgs/service-types) | 麦克风前台服务类型、权限与启动限制 | vivo 全天稳定、任意后台自启 |
| S2 | [Android：Sharing audio input](https://developer.android.com/media/platform/sharing-audio-input) | 多应用争用时可能被静音 | 每次正数 read 都有有效讲话 |
| S3 | [OpenAI：MCP Events](https://developers.openai.com/plugins/build/mcp-events) | dots 事件路径、协议要求、webhook 与接收语义 | 账户已授权、事件已写入记忆 |
| S4 | [OpenAI：Connect and test your plugin](https://developers.openai.com/plugins/deploy/connect-chatgpt) | 连接、测试、HTTPS/安全隧道路线 | 本地服务已可被远端访问 |
| S5 | [OpenAI：Authentication](https://developers.openai.com/plugins/build/auth) | OAuth 与授权发现要求 | 普通 API key 可替代账号授权 |
| S6 | [sherpa-onnx：SenseVoice pretrained models](https://k2-fsa.github.io/sherpa/onnx/sense-voice/pretrained.html) | 官方模型与 Android 示例入口 | X200 Ultra 识别质量、功耗与速度 |
| S7 | [Android：AGP 8.9 release notes](https://developer.android.com/build/releases/agp-8-9-0-release-notes) | 固定构建基线的兼容要求 | 当前源码已成功构建或满足未来上架要求 |
| S8 | [OpenAI：Build an MCP server](https://developers.openai.com/plugins/build/mcp-server) | 官方 SDK、工具 schema、只读注解与测试方式 | 本版 `/mcp` 已实现 |
| S9 | [华为：GT 6 系列功能兼容性](https://consumer.huawei.com/cn/support/content/zh-cn16066413/) | 录音机功能与固件版本条件 | 第三方录音、导出到 vivo、自由固件开发 |
| S10 | [GitHub CLI：gh repo create](https://cli.github.com/manual/gh_repo_create) | 私有建仓、从本地源码推送 | 本次会话已创建远端 |

## 证据分级

**D 文档证据**：官方描述能力或限制。**C 代码证据**：仓库存在实现且有自动测试。**V 真机证据**：实际设备日志、录音与测量。**I 集成证据**：真实账户授权后的端到端行为。

当前中继具有 C；Android 系统规则与 SDK 路线具有 D；X200 Ultra 录音、GT 6 Pro 导出无 V；真实 dot 接入无 I。开发报告应保留这四种标记，不能把 D 自动升级成 V/I。

## 待重新核对的外部条件

手机系统版本、手表地区固件、可用 SDK 与模型许可、OpenAI 账号/工作区权限、MCP 当前规范和 GitHub CLI 本机登录状态。任何一个未知项都不能用演示截图替代。

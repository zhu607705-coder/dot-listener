# v0.1.0 导入前代码审查

审查日期：2026-10-22（Asia/Taipei）。基线：用户提供的 59 文件源码包，以及现有 GitHub 仓库初始提交 `146e4cd`。审查方法：主审读取实现、运行回归与本地烟测；独立只读复核 Android 生命周期、Python 权限/游标和浏览器数据边界。没有执行设备测试或生产安全审计。

## 发现与处理

| 级别 | 问题与触发条件 | 处理与证据 | 验证边界 |
|---|---|---|---|
| P2 | 用户暂停或麦克风中断使阻塞 read 返回负数/抛异常时，服务把既有终态改写为 ERROR | 提取 `readWhileRunning`，读取前后及异常时检查运行状态；六条新增 JVM 断言先失败后通过 | 纯 JVM 策略，不是 Android API/设备测试 |
| P2 | worker 启动/释放与停止存在竞争；旧任务无条件 stopSelf 可能误停新启动 | 用锁串行启动/停止/释放；结束时 `stopSelf(startId)` | 静态复核未发现锁顺序死锁；待 SDK 构建与快速启停真机验收 |
| P2 | UTC 归一化越过 datetime 年份边界时抛 OverflowError，API 不能正常返回参数错误 | 将溢出转为 ValueError，使 API 返回 422；最小/最大年份两条回归先失败后通过 | FastAPI TestClient，合成输入 |
| P2（文档） | README/状态文档称无许可证、默认私有或仓库未创建，与目标公开 Apache-2.0 仓库不符 | 保留现有 LICENSE、历史及忽略规则，更新仓库/许可说明；旧私有建仓脚本保持防覆盖行为 | GitHub 元数据、源码差异 |

## 本次实际验证

- Python 3.13.12：62 项 pytest 通过；一条上游 Starlette/AnyIO 弃用警告。
- 真实回环 HTTP：6 项检查通过；后端合成烟测通过。
- Kotlin 2.3.0 / OpenJDK 21：1,451 条纯 JVM 断言通过；不是 Android 工程编译。
- 依赖检查：pip check 通过；使用项目固定依赖版本，网络超时后借助缓存及 `--no-build-isolation` 完成 editable install。
- 浏览器合成演示：22 项检查通过，桌面与手机宽度均无横向溢出，无 JS 错误、无外网请求。Playwright 1.57.0 使用本机已有 Chromium headless shell revision 1208 的独立临时 profile；未使用用户浏览器登录态。结果见 `STATUS.md` 和 `../evidence/browser-checks.json`。
- Markdown 相对链接解析通过；Android Manifest 仅检查 XML 格式。

本次新增回归和运行环境记录保存在 `../evidence/review-20261022/`。原始包中的旧 evidence 保留用于追溯，不能当作本次重跑结果。

## 审查结论

可作为架构/工程验证版通过 PR 导入；不能视为已可日常使用的全天录音产品。源码中 ingest/read/admin 权限分离、未发布内容隐藏、重复上传去重、晚发布游标、删除墓碑与防重放有实现及对应测试；本次未发现足以确认的权限绕过。浏览器模拟器使用合成数据，不调用麦克风或外网。

未验收：Android SDK 构建/APK、vivo 录音/熄屏/功耗、ASR、手机持久同步、生产 OAuth/MCP/订阅投递、真实 dot 和 GT 6 Pro 音频获取。依赖漏洞扫描、真实公网部署和生产多用户安全性也不在本次通过结论内。后续按 ROADMAP 的能力门逐项验收。

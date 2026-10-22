# 当前交付状态

版本：0.1.0。最近审查与本地重跑：2026-10-22（Asia/Taipei）。原始源码包的日志基线为 2026-10-21 America/Los_Angeles；旧日志保留，不替代本次验证。

| 项目 | 当前结果 | 证据 |
|---|---|---|
| Python 文本中继 | 本次 62 项自动测试通过 | `evidence/review-20261022/python-tests.txt` |
| 真实回环 HTTP 服务 | 本次 6 项请求检查通过；合成烟测通过 | `evidence/review-20261022/http-smoke.json` |
| Kotlin 核心策略 | 本次 1,451 条断言通过；Kotlin 2.3.0 / JDK 21 | `evidence/review-20261022/kotlin-policy.txt` |
| 浏览器合成演示 | 本次 22 项通过；桌面/手机宽度；无 JS 错误、无外网请求 | `evidence/browser-checks.json` |
| Python 包本地可编辑安装 | 成功；项目固定依赖；pip check 通过 | `evidence/review-20261022/environment.json` |
| Android SDK 构建 / APK | 未执行 | 不交付可安装 APK |
| Android 停止状态与生命周期修正 | 源码已改；read 策略有 JVM 回归，服务生命周期尚无设备证据 | `docs/CODE-REVIEW.md` |
| vivo X200 Ultra 录音和耗电 | 未实机测试 | `docs/ANDROID.md` |
| 手机 ASR / 手机持久同步 | 未集成 | `docs/ROADMAP.md` |
| MCP 网关 / OAuth / 订阅与发送 | 未实现 | `/mcp` 返回 501 |
| 真实 dot | 未连接 | 没有账户端到端证据 |
| GT 6 Pro 自动取音频 | 未验证 | `docs/WATCH-PROBE.md` |
| GitHub 远端仓库 | 已存在，公开，采用 Apache-2.0；本版通过 PR 导入 | `https://github.com/zhu607705-coder/dot-listener` |

## 复跑命令

```bash
python -m pytest -q
python scripts/smoke_demo.py
python scripts/http_smoke.py
# 可选浏览器测试：安装额外依赖及浏览器
python -m pip install -e '.[browser]'
python -m playwright install chromium
python scripts/check_web.py
# Kotlin：需要本机已有 kotlinc 与 Java
kotlinc android/app/src/main/java/dev/dotlistener/CapturePolicy.kt android/core-tests/CapturePolicyCheck.kt -include-runtime -d /tmp/dot-policy.jar
java -jar /tmp/dot-policy.jar
```

浏览器检查将自有 HTML 内容直接载入测试页面，不导航用户浏览器，不使用用户登录状态。截图和计数属于合成流程验证。Kotlin 本次使用已有 Gradle 分发包内的编译器，命令结构保存在 evidence；没有使用它替代 Android SDK 编译。

本次审查详情见 `docs/CODE-REVIEW.md`。外部协议与模型来源文档保留原核对日期，本次没有将文档依据升级为真机或账户集成证据。

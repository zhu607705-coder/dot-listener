# Changelog

## 0.1.0 — architecture bootstrap

Added encrypted single-owner transcript relay, strict input contract, role separation, idempotent ingestion, publication cursor, deletion tombstones, event outbox and signature helpers. Added capture/sleep policy reference, Android experimental capture sources, synthetic interactive operation demo, source-backed architecture and acceptance documents. Added local tests and a private-repository publishing script.

Not shipped: a verified Android APK, mobile ASR, phone-to-relay sync, production OAuth/MCP Events delivery, real dot connection, verified GT 6 Pro audio import.


## 2026-10-22 — reviewed GitHub import

- Import v0.1.0 into the existing public repository through a feature branch and PR; preserve Apache-2.0 LICENSE, repository history, and existing ignore rules.
- Reject timezone conversion overflow as a 422 validation error rather than an unhandled exception; add lower/upper UTC boundary regressions.
- Preserve pause/interruption status when stopping a blocking audio read, serialize recorder startup/cleanup, and bind worker shutdown to its startId. Add six JVM read-policy assertions; Android lifecycle behavior remains unverified on a device.
- Re-run local relay, HTTP, Kotlin policy and browser checks with fresh evidence. Extend CI with the loopback HTTP smoke check.

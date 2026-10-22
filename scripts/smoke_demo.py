"""Run an in-process text pipeline with synthetic input. No network or microphone."""
import json
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from dot_listener.app import create_app
from dot_listener.config import Settings
root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    settings = Settings(Path(tmp)/"demo.sqlite3", "i"*40, "r"*40, "a"*40, Fernet.generate_key().decode())
    client = TestClient(create_app(settings))
    fragment = json.loads((root/"examples/fragment.json").read_text())
    ing = {"Authorization": "Bearer " + settings.ingest_token}
    read = {"Authorization": "Bearer " + settings.read_token}
    admin = {"Authorization": "Bearer " + settings.admin_token}
    actions = [
        ("1. 文本入库", client.post("/v1/fragments", json=fragment, headers=ing)),
        ("2. 相同片段重传", client.post("/v1/fragments", json=fragment, headers=ing)),
        ("3. 读取已发布索引", client.get("/v1/fragments", headers=read)),
        ("4. 读取转写原文", client.get("/v1/fragments/"+fragment["id"], headers=read)),
        ("5. 查看事件待发队列", client.get("/v1/outbox", headers=admin)),
    ]
    for label, response in actions:
        response.raise_for_status()
        print(label, json.dumps(response.json(), ensure_ascii=False, indent=2))
    print("BOUNDARY: dot is NOT connected; no ASR or microphone was used.")

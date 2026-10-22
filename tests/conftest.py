import json
from pathlib import Path
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from dot_listener.app import create_app
from dot_listener.config import Settings

@pytest.fixture
def settings(tmp_path):
    return Settings(tmp_path/"listener.sqlite3", "i"*40, "r"*40, "a"*40, Fernet.generate_key().decode())
@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c: yield c
@pytest.fixture
def fragment():
    return json.loads((Path(__file__).parents[1]/"examples/fragment.json").read_text())
@pytest.fixture
def headers(settings):
    return {role: {"Authorization": "Bearer " + getattr(settings, role + "_token")}
            for role in ("ingest", "read", "admin")}

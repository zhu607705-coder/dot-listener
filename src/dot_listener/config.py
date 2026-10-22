from dataclasses import dataclass
import os
from pathlib import Path
from cryptography.fernet import Fernet

@dataclass(frozen=True)
class Settings:
    db_path: Path
    ingest_token: str
    read_token: str
    admin_token: str
    encryption_key: str

    def validate(self) -> None:
        tokens = (self.ingest_token, self.read_token, self.admin_token)
        if any(len(t) < 32 for t in tokens) or len(set(tokens)) != 3:
            raise ValueError("Three distinct tokens of at least 32 characters are required")
        Fernet(self.encryption_key.encode("ascii"))

    @classmethod
    def from_env(cls) -> "Settings":
        keys = ("DL_INGEST_TOKEN", "DL_READ_TOKEN", "DL_ADMIN_TOKEN", "DL_FERNET_KEY")
        if any(not os.environ.get(k) for k in keys):
            raise ValueError("Missing secrets. Run scripts/init_dev.py; then source .env")
        s = cls(Path(os.environ.get("DL_DB_PATH", "runtime/listener.sqlite3")),
                *(os.environ[k] for k in keys))
        s.validate()
        return s

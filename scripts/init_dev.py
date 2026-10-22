"""Create development secrets without printing them or overwriting existing ones."""
from pathlib import Path
import os
import secrets
from cryptography.fernet import Fernet
root = Path(__file__).resolve().parents[1]
path = root / ".env"
try:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    raise SystemExit(".env already exists; left unchanged")
with os.fdopen(fd, "w") as f:
    f.write("DL_DB_PATH=runtime/listener.sqlite3\n")
    for role in ("INGEST", "READ", "ADMIN"):
        f.write(f"DL_{role}_TOKEN={secrets.token_urlsafe(36)}\n")
    f.write(f"DL_FERNET_KEY={Fernet.generate_key().decode()}\n")
print("Created .env (mode 0600). Keep it private; losing its key loses transcript access.")

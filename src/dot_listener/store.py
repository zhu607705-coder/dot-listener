"""Single-owner store. Transcript payloads are encrypted; indexes remain metadata.
Deletion removes ciphertext and prevents resurrection. It cannot erase backups or
copies previously sent to another system. SQLite files still need OS protection.
"""
import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from cryptography.fernet import Fernet
from .models import Fragment

class Conflict(Exception): pass
class Gone(Exception): pass
class Missing(Exception): pass

def now():
    return datetime.now(timezone.utc).isoformat()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

class Store:
    def __init__(self, path: Path, key: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.cipher = Fernet(key.encode("ascii"))
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value BLOB);
                CREATE TABLE IF NOT EXISTS fragments (
                  id TEXT PRIMARY KEY, digest TEXT NOT NULL, ciphertext BLOB,
                  created_at TEXT NOT NULL, published INTEGER NOT NULL DEFAULT 0,
                  deleted_at TEXT, last_retrieved_at TEXT);
                CREATE TABLE IF NOT EXISTS publications (
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, fragment_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS outbox (
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,
                  name TEXT NOT NULL, fragment_id TEXT NOT NULL, occurred_at TEXT NOT NULL,
                  status TEXT NOT NULL DEFAULT 'pending_not_dispatched');
            """)
            row = db.execute("SELECT value FROM metadata WHERE key='key_check'").fetchone()
            if row:
                if self.cipher.decrypt(row[0]) != b"dot-listener-key-v1":
                    raise ValueError("Incorrect encryption key")
            else:
                db.execute("INSERT INTO metadata VALUES ('key_check',?)",
                           (self.cipher.encrypt(b"dot-listener-key-v1"),))
        os.chmod(self.path, 0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def _publish(self, db, fid):
        db.execute("UPDATE fragments SET published=1 WHERE id=?", (fid,))
        db.execute("INSERT OR IGNORE INTO publications(fragment_id) VALUES (?)", (fid,))
        db.execute("INSERT INTO outbox(event_id,name,fragment_id,occurred_at) VALUES(?,?,?,?)",
                   (str(uuid4()), "transcript.ready", fid, now()))

    def ingest(self, fragment: Fragment):
        data = fragment.model_dump(mode="json")
        payload = canonical(data).encode()
        digest = hashlib.sha256(payload).hexdigest()
        fid = str(fragment.id)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM fragments WHERE id=?", (fid,)).fetchone()
            if row:
                if row["deleted_at"]: raise Gone(fid)
                if row["digest"] != digest: raise Conflict(fid)
                return {"id": fid, "duplicate": True, "stored": True,
                        "published": bool(row["published"]), "dot_delivery": "not_implemented"}
            db.execute("INSERT INTO fragments(id,digest,ciphertext,created_at) VALUES(?,?,?,?)",
                       (fid, digest, self.cipher.encrypt(payload), now()))
            if fragment.publish_to_dot:
                self._publish(db, fid)
        return {"id": fid, "duplicate": False, "stored": True,
                "published": fragment.publish_to_dot, "dot_delivery": "not_implemented"}

    def publish(self, fid):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM fragments WHERE id=?", (fid,)).fetchone()
            if not row: raise Missing(fid)
            if row["deleted_at"]: raise Gone(fid)
            if not row["published"]: self._publish(db, fid)
        return {"id": fid, "published": True, "dot_delivery": "not_implemented"}

    def get(self, fid, admin=False):
        with self.connect() as db:
            row = db.execute("SELECT * FROM fragments WHERE id=?", (fid,)).fetchone()
            if not row: raise Missing(fid)
            # Do not reveal whether an unpublished record exists to a read client.
            if not admin and not row["published"]: raise Missing(fid)
            if row["deleted_at"]: raise Gone(fid)
            result = json.loads(self.cipher.decrypt(row["ciphertext"]))
            result["publish_to_dot"] = bool(row["published"])
            retrieved = now()
            db.execute("UPDATE fragments SET last_retrieved_at=? WHERE id=?", (retrieved, fid))
        return {"fragment": result, "retrieved_at": retrieved,
                "trust": "untrusted_transcript", "memory_write_confirmed": False}

    def list_published(self, after_seq=0, limit=50):
        if after_seq < 0 or not 1 <= limit <= 100: raise ValueError("Invalid pagination")
        with self.connect() as db:
            rows = db.execute("""SELECT p.seq,f.* FROM publications p JOIN fragments f
                 ON p.fragment_id=f.id WHERE p.seq>? ORDER BY p.seq LIMIT ?""",
                 (after_seq, limit)).fetchall()
            items = []
            for row in rows:
                entry = {"seq": row["seq"], "id": row["id"],
                         "deleted": bool(row["deleted_at"])}
                if not row["deleted_at"]:
                    obj = json.loads(self.cipher.decrypt(row["ciphertext"]))
                    entry.update({k: obj[k] for k in
                                  ("started_at", "ended_at", "timezone", "source")})
                items.append(entry)
        return {"items": items, "next_after_seq": items[-1]["seq"] if items else after_seq}

    def delete(self, fid):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM fragments WHERE id=?", (fid,)).fetchone()
            if not row: raise Missing(fid)
            if not row["deleted_at"]:
                db.execute("UPDATE fragments SET ciphertext=NULL, deleted_at=? WHERE id=?", (now(), fid))
                db.execute("UPDATE outbox SET status='cancelled' WHERE fragment_id=?", (fid,))
                if row["published"]:
                    db.execute("INSERT INTO publications(fragment_id) VALUES (?)", (fid,))
                    db.execute("INSERT INTO outbox(event_id,name,fragment_id,occurred_at) VALUES(?,?,?,?)",
                               (str(uuid4()), "transcript.deleted", fid, now()))
        return {"id": fid, "deleted": True, "downstream_erasure": "not_confirmed"}

    def outbox(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM outbox ORDER BY seq LIMIT 500")]

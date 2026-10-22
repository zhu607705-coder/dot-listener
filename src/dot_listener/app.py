"""Local developer API. This is NOT an OAuth server or MCP transport."""
import hmac
from uuid import UUID
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from .config import Settings
from .models import Fragment
from .store import Store, Conflict, Gone, Missing

MAX_REQUEST = 128 * 1024

def create_app(settings: Settings | None = None):
    settings = settings or Settings.from_env()
    settings.validate()
    store = Store(settings.db_path, settings.encryption_key)
    app = FastAPI(title="Dot Listener — local text relay", version="0.1.0")
    app.state.store = store

    @app.middleware("http")
    async def guard(request: Request, call_next):
        # Count actual streamed bytes; a missing Content-Length does not bypass it.
        if request.method in {"POST", "PUT", "PATCH"}:
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > MAX_REQUEST:
                    return JSONResponse({"detail": "Request too large"}, status_code=413)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def role(request: Request):
        header = request.headers.get("authorization", "")
        token = header[7:] if header.startswith("Bearer ") else ""
        for name, expected in (("ingest", settings.ingest_token),
                               ("read", settings.read_token), ("admin", settings.admin_token)):
            if hmac.compare_digest(token.encode(), expected.encode()): return name
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})

    def allow(*roles):
        def check(name=Depends(role)):
            if name not in roles: raise HTTPException(403, "Insufficient permission")
            return name
        return check

    @app.exception_handler(Missing)
    async def missing(request, exc): return JSONResponse({"detail": "Not found"}, status_code=404)
    @app.exception_handler(Gone)
    async def gone(request, exc): return JSONResponse({"detail": "Deleted; replay is blocked"}, status_code=410)
    @app.exception_handler(Conflict)
    async def conflict(request, exc): return JSONResponse({"detail": "ID reused with different content"}, status_code=409)

    @app.get("/healthz")
    def health(): return {"status": "ok", "version": "0.1.0", "dot_connected": False}

    @app.post("/v1/fragments")
    def ingest(fragment: Fragment, who=Depends(allow("ingest", "admin"))):
        return store.ingest(fragment)

    @app.get("/v1/fragments")
    def listing(after_seq: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                who=Depends(allow("read", "admin"))):
        return store.list_published(after_seq, limit)

    @app.get("/v1/fragments/{fid}")
    def get(fid: UUID, who=Depends(allow("read", "admin"))):
        return store.get(str(fid), admin=who == "admin")

    @app.post("/v1/fragments/{fid}/publish")
    def publish(fid: UUID, who=Depends(allow("admin"))): return store.publish(str(fid))

    @app.delete("/v1/fragments/{fid}")
    def delete(fid: UUID, who=Depends(allow("admin"))): return store.delete(str(fid))

    @app.get("/v1/outbox")
    def outbox(who=Depends(allow("admin"))):
        return {"items": store.outbox(), "dispatcher": "not_implemented"}

    @app.post("/mcp")
    def mcp_placeholder(who=Depends(allow("read", "admin"))):
        raise HTTPException(501, "MCP transport, OAuth and Events subscriptions are not implemented in v0.1.0")

    return app

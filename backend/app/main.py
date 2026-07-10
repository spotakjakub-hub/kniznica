import os
import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db, SessionLocal
from app.routers import books, categories, meta, scan, queue, loans, export
from app.routers.categories import seed_categories
from app.services import queue_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_categories(db)
    finally:
        db.close()
    queue_worker.resume_on_startup()
    yield


app = FastAPI(title="Family Library API", version="0.1.0", lifespan=lifespan)

# Optional shared-password protection: set LIBRARY_PASSWORD to switch it on.
# The whole family uses one password; the frontend sends it as X-Library-Key.
LIBRARY_PASSWORD = os.environ.get("LIBRARY_PASSWORD", "")
AUTH_EXEMPT = {"/api/health", "/api/auth/check"}


@app.middleware("http")
async def shared_password_guard(request, call_next):
    if (
        LIBRARY_PASSWORD
        and request.url.path.startswith("/api")
        and request.url.path not in AUTH_EXEMPT
        and request.method != "OPTIONS"
    ):
        supplied = request.headers.get("x-library-key", "")
        if not secrets.compare_digest(supplied, LIBRARY_PASSWORD):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return await call_next(request)


# CORS must be registered AFTER the password guard: the middleware added last
# runs outermost, so even the guard's 401 responses get CORS headers —
# otherwise the browser drops them and the frontend never sees the 401.
origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(books.router)
app.include_router(categories.router)
app.include_router(meta.router)
app.include_router(scan.router)
app.include_router(queue.router)
app.include_router(loans.router)
app.include_router(export.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/auth/check")
def auth_check(key: str = ""):
    """Lets the frontend verify the shared password (and whether auth is on)."""
    if not LIBRARY_PASSWORD:
        return {"protected": False, "ok": True}
    return {"protected": True, "ok": secrets.compare_digest(key, LIBRARY_PASSWORD)}

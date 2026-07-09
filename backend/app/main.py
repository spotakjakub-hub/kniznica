import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, SessionLocal
from app.routers import books, categories, meta
from app.routers.categories import seed_categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_categories(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Rodinná knižnica API", version="0.1.0", lifespan=lifespan)

# Comma-separated list of allowed origins, e.g. "https://kniznica.vercel.app,http://localhost:5173"
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


@app.get("/api/health")
def health():
    return {"status": "ok"}

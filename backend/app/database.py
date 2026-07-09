import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    # Render/Heroku style URL -> SQLAlchemy dialect name
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if DATABASE_URL.startswith("postgresql://"):
    # use the psycopg v3 driver
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
if not DATABASE_URL:
    # dev fallback so the app runs without Supabase credentials
    DATABASE_URL = "sqlite:///./kniznica.db"
    print("WARNING: DATABASE_URL nie je nastavené — používam lokálny SQLite (len na vývoj)")

IS_POSTGRES = DATABASE_URL.startswith("postgresql")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    **({"pool_size": 5, "max_overflow": 5} if IS_POSTGRES else {"connect_args": {"check_same_thread": False}}),
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# unaccent extension makes search ignore Slovak/Czech diacritics
HAS_UNACCENT = False


def init_db():
    global HAS_UNACCENT
    from app.models import Base
    if IS_POSTGRES:
        with engine.begin() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
                HAS_UNACCENT = True
            except Exception:
                HAS_UNACCENT = False
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import time
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

is_sqlite = "sqlite" in settings.DATABASE_URL
is_postgres = "postgres" in settings.DATABASE_URL or "postgresql" in settings.DATABASE_URL

# Strict Production Guard
if settings.ENVIRONMENT == "production" and is_sqlite:
    raise RuntimeError(
        "CRITICAL: Production environment strictly requires PostgreSQL. "
        "SQLite fallback is prohibited in production to prevent data loss."
    )

if is_postgres:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False,
    )
elif is_sqlite:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Enable WAL mode for SQLite to maximize concurrent read/write throughput
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(settings.DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health(retries: int = 3, backoff_seconds: float = 0.5) -> bool:
    """Verifies database connectivity with exponential backoff retries."""
    for attempt in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except Exception:
            if attempt < retries - 1:
                time.sleep(backoff_seconds * (2 ** attempt))
    return False


def check_database_health() -> bool:
    return check_db_health()

"""
Database engine and session management.
Dynamically supports PostgreSQL (production) and SQLite WAL mode (zero-setup local dev).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

is_sqlite = "sqlite" in settings.DATABASE_URL
is_postgres = "postgres" in settings.DATABASE_URL

if is_postgres:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
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

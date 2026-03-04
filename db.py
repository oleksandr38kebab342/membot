import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = os.getenv("DB_URL", "sqlite:///data.db")

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _column_exists(conn, table, column):
    result = conn.execute(text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result)


def _ensure_columns():
    with engine.connect() as conn:
        if _table_exists(conn, "rating") and not _column_exists(conn, "rating", "accepted_count"):
            conn.execute(text("ALTER TABLE rating ADD COLUMN accepted_count INTEGER DEFAULT 0"))
        if _table_exists(conn, "users") and not _column_exists(conn, "users", "last_joke_at"):
            conn.execute(text("ALTER TABLE users ADD COLUMN last_joke_at DATETIME"))
        if _table_exists(conn, "users") and not _column_exists(conn, "users", "last_seen_at"):
            conn.execute(text("ALTER TABLE users ADD COLUMN last_seen_at DATETIME"))


def _table_exists(conn, table):
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name = :name"), {"name": table})
    return result.fetchone() is not None


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_columns()

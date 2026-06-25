from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def create_db_engine() -> Engine | None:
    settings = get_settings()
    if not settings.database_url:
        return None
    return create_engine(settings.database_url, pool_pre_ping=True)


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) if engine else None


@contextmanager
def session_scope() -> Generator[Session | None, None, None]:
    if SessionLocal is None:
        yield None
        return

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def save_chat_message(session: Session, sender_id: str, role: str, message: str) -> None:
    session.execute(
        text(
            """
            INSERT INTO chat_messages (sender_id, role, message)
            VALUES (:sender_id, :role, :message)
            """
        ),
        {"sender_id": sender_id, "role": role, "message": message},
    )


def load_recent_chat(session: Session, sender_id: str, limit: int = 20) -> list[dict[str, str]]:
    rows = session.execute(
        text(
            """
            SELECT role, message
            FROM chat_messages
            WHERE sender_id = :sender_id
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"sender_id": sender_id, "limit": limit},
    ).mappings()

    return [{"role": row["role"], "message": row["message"]} for row in reversed(list(rows))]


def load_memory(session: Session, sender_id: str) -> dict[str, str]:
    rows = session.execute(
        text(
            """
            SELECT memory_key, memory_value
            FROM family_memory
            WHERE sender_id = :sender_id
            ORDER BY memory_key ASC
            """
        ),
        {"sender_id": sender_id},
    ).mappings()

    return {row["memory_key"]: row["memory_value"] for row in rows}


def upsert_memory(session: Session, sender_id: str, memory_key: str, memory_value: str) -> None:
    session.execute(
        text(
            """
            INSERT INTO family_memory (sender_id, memory_key, memory_value)
            VALUES (:sender_id, :memory_key, :memory_value)
            ON CONFLICT (sender_id, memory_key)
            DO UPDATE SET memory_value = EXCLUDED.memory_value, updated_at = now()
            """
        ),
        {
            "sender_id": sender_id,
            "memory_key": memory_key,
            "memory_value": memory_value,
        },
    )

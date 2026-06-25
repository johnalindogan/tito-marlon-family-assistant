import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import session_scope


def main() -> None:
    with session_scope() as session:
        if session is None:
            raise RuntimeError("DATABASE_URL is not configured")

        rows = session.execute(
            text(
                """
                SELECT DISTINCT ON (sender_id)
                  sender_id,
                  message AS latest_message,
                  created_at
                FROM chat_messages
                WHERE role = 'user'
                ORDER BY sender_id, created_at DESC
                """
            )
        ).mappings()

        for row in rows:
            latest_message = row["latest_message"].replace("\n", " ")[:80]
            print(f"{row['sender_id']} | {row['created_at']} | {latest_message}")


if __name__ == "__main__":
    main()

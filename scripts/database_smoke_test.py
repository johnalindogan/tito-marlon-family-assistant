import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.database import session_scope


def main() -> None:
    if len(sys.argv) > 1:
        settings = get_settings()
        url = settings.database_url.replace("@localhost:", f"@{sys.argv[1]}:")
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_user, current_database()")).one()
            print(f"database_connected user={result[0]} db={result[1]}")
        return

    with session_scope() as session:
        if session is None:
            raise RuntimeError("DATABASE_URL is not configured")
        result = session.execute(text("SELECT current_user, current_database()")).one()
        print(f"database_connected user={result[0]} db={result[1]}")


if __name__ == "__main__":
    main()

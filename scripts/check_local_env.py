from pathlib import Path
import sys
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def main() -> None:
    from app.config import get_settings

    app_env = read_env(ROOT / ".env")
    postgres_env = read_env(ROOT / ".env.postgres.local")
    database_url = app_env.get("DATABASE_URL", "")
    settings_database_url = get_settings().database_url
    parsed = urlparse(database_url)
    settings_parsed = urlparse(settings_database_url)
    database_password = unquote(parsed.password or "")
    settings_password = unquote(settings_parsed.password or "")
    postgres_password = postgres_env.get("POSTGRES_PASSWORD", "")

    print(f"openai_key_present={bool(app_env.get('OPENAI_API_KEY'))}")
    print(f"database_url_present={bool(database_url)}")
    print(f"database_user={parsed.username or ''}")
    print(f"database_host={parsed.hostname or ''}")
    print(f"database_port={parsed.port or ''}")
    print(f"database_name={parsed.path.lstrip('/')}")
    print(f"postgres_env_present={bool(postgres_password)}")
    print(f"passwords_match={database_password == postgres_password}")
    print(f"settings_database_url_present={bool(settings_database_url)}")
    print(f"settings_database_host={settings_parsed.hostname or ''}")
    print(f"settings_matches_postgres_password={settings_password == postgres_password}")


if __name__ == "__main__":
    main()

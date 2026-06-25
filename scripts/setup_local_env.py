import secrets
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
POSTGRES_ENV_PATH = ROOT / ".env.postgres.local"


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


def write_env(path: Path, values: dict[str, str]) -> None:
    body = "\n".join(f"{key}={value}" for key, value in values.items()) + "\n"
    path.write_text(body, encoding="utf-8")


def main() -> None:
    postgres_values = read_env(POSTGRES_ENV_PATH)
    rotate = "--rotate-postgres-password" in sys.argv
    password = postgres_values.get("POSTGRES_PASSWORD")
    if rotate or not password:
        password = secrets.token_hex(24)

    postgres_values = {
        "POSTGRES_USER": "titomarlon",
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": "titomarlon",
    }
    write_env(POSTGRES_ENV_PATH, postgres_values)

    app_values = read_env(ENV_PATH)
    app_values.setdefault("OPENAI_API_KEY", "")
    app_values.setdefault("OPENAI_MODEL", "gpt-4.1-mini")
    app_values["DATABASE_URL"] = (
        f"postgresql+psycopg://titomarlon:{password}@localhost:55432/titomarlon"
    )
    app_values.setdefault("APP_ENV", "development")
    app_values.setdefault("LOG_LEVEL", "INFO")
    app_values.setdefault("MESSAGE_MAX_LENGTH", "2000")
    write_env(ENV_PATH, app_values)

    print("local-env-ready")


if __name__ == "__main__":
    main()

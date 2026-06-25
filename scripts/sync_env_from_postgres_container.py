import json
import subprocess
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
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in values.items()) + "\n",
        encoding="utf-8",
    )


def container_env() -> dict[str, str]:
    output = subprocess.check_output(
        ["docker", "inspect", "titomarlon-postgres"],
        text=True,
    )
    data = json.loads(output)[0]["Config"]["Env"]
    values: dict[str, str] = {}
    for item in data:
        if "=" in item:
            key, value = item.split("=", 1)
            values[key] = value
    return values


def main() -> None:
    container_values = container_env()
    password = container_values["POSTGRES_PASSWORD"]

    postgres_values = {
        "POSTGRES_USER": container_values.get("POSTGRES_USER", "titomarlon"),
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": container_values.get("POSTGRES_DB", "titomarlon"),
    }
    write_env(POSTGRES_ENV_PATH, postgres_values)

    app_values = read_env(ENV_PATH)
    app_values["DATABASE_URL"] = (
        f"postgresql+psycopg://{postgres_values['POSTGRES_USER']}:{password}"
        f"@localhost:55432/{postgres_values['POSTGRES_DB']}"
    )
    write_env(ENV_PATH, app_values)

    print("env-synced-from-container")


if __name__ == "__main__":
    main()

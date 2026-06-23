import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    values = read_env(ROOT / ".env.postgres.local")
    password = values["POSTGRES_PASSWORD"]
    sql = f"ALTER USER titomarlon WITH PASSWORD {sql_literal(password)};\n"

    subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            "titomarlon-postgres",
            "psql",
            "-U",
            "titomarlon",
            "-d",
            "titomarlon",
        ],
        input=sql,
        text=True,
        check=True,
    )
    print("postgres-password-reset")


if __name__ == "__main__":
    main()

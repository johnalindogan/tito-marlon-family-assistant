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


def main() -> None:
    password = read_env(ROOT / ".env.postgres.local")["POSTGRES_PASSWORD"]
    result = subprocess.run(
        [
            "docker",
            "exec",
            "-e",
            f"PGPASSWORD={password}",
            "titomarlon-postgres",
            "psql",
            "-h",
            "127.0.0.1",
            "-U",
            "titomarlon",
            "-d",
            "titomarlon",
            "-c",
            "SELECT 1;",
        ],
        capture_output=True,
        text=True,
    )
    print(f"container_tcp_password_ok={result.returncode == 0}")


if __name__ == "__main__":
    main()

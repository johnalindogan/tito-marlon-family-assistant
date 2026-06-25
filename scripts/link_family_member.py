import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import link_family_member_sender, session_scope


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/link_family_member.py <member_key> <messenger_sender_id>")

    member_key = sys.argv[1].strip()
    sender_id = sys.argv[2].strip()
    if not member_key or not sender_id:
        raise SystemExit("member_key and messenger_sender_id are required")

    with session_scope() as session:
        if session is None:
            raise RuntimeError("DATABASE_URL is not configured")
        link_family_member_sender(session, member_key, sender_id)

    print(f"linked {member_key}")


if __name__ == "__main__":
    main()

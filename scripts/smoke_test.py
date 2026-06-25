import json
import urllib.request


def request_json(url: str, payload: dict[str, str] | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    print(request_json("http://localhost:8000/health"))
    print(
        request_json(
            "http://localhost:8000/message",
            {
                "sender_id": "test-sender",
                "message": "Kumusta Tito Marlon?",
            },
        )
    )


if __name__ == "__main__":
    main()

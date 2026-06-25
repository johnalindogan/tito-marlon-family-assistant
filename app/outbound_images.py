RUNNING_IMAGE_URLS = [
    "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1200&q=80",
]

IMAGE_REQUEST_WORDS = (
    "image",
    "images",
    "photo",
    "photos",
    "picture",
    "pictures",
    "larawan",
    "pic",
    "pics",
)

RUNNING_WORDS = (
    "10k",
    "run",
    "running",
    "runner",
    "fun run",
    "jog",
    "jogging",
    "takbo",
    "marathon",
)


def outbound_image_urls_for_message(message: str) -> list[str]:
    text = message.lower()
    wants_images = any(word in text for word in IMAGE_REQUEST_WORDS)
    mentions_running = any(word in text for word in RUNNING_WORDS)

    if wants_images and mentions_running:
        return RUNNING_IMAGE_URLS

    return []

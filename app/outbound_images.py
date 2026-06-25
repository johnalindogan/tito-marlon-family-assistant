import re


RUNNING_IMAGE_URLS = [
    "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1200&q=80",
]

FAMILY_IMAGE_URLS = [
    "https://images.unsplash.com/photo-1511895426328-dc8714191300?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1516627145497-ae6968895b74?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=1200&q=80",
]

GENERAL_IMAGE_URLS = [
    "https://images.unsplash.com/photo-1493612276216-ee3925520721?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1490730141103-6cac27aaab94?auto=format&fit=crop&w=1200&q=80",
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

FAMILY_WORDS = (
    "family",
    "families",
    "pamilya",
    "filipino family",
    "pamilyang pilipino",
    "magulang",
    "parents",
    "kids",
    "children",
)


def outbound_image_urls_for_message(message: str) -> list[str]:
    text = message.lower()
    wants_images = any(_contains_word(text, word) for word in IMAGE_REQUEST_WORDS)
    mentions_running = any(_contains_word(text, word) for word in RUNNING_WORDS)
    mentions_family = any(_contains_word(text, word) for word in FAMILY_WORDS)

    if wants_images and mentions_running:
        return RUNNING_IMAGE_URLS

    if wants_images and mentions_family:
        return FAMILY_IMAGE_URLS

    if wants_images:
        return GENERAL_IMAGE_URLS

    return []


def _contains_word(text: str, word: str) -> bool:
    escaped = re.escape(word.lower())
    if " " in word:
        return escaped in text
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None

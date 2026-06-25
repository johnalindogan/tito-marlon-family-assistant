from dataclasses import dataclass
import base64
import json
import re
from typing import Literal
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from openai import OpenAI

from app.config import get_settings


MediaType = Literal["image", "link", "video"]
SourceType = Literal["curated", "generated", "official", "public"]


@dataclass(frozen=True)
class MediaAsset:
    asset_id: str
    type: MediaType
    url: str
    title: str
    caption: str
    device: str
    category: str
    language: str
    tags: tuple[str, ...]
    source: SourceType
    safety_level: str
    intended_use: str


@dataclass(frozen=True)
class MediaPlan:
    intent: str
    assets: list[MediaAsset]
    generated_prompt: str | None = None
    escalation_reason: str | None = None


OFFICIAL_LINKS: dict[str, str] = {
    "canon_g3010_manual": "https://ph.canon/en/support/PIXMA%20G3010/model",
    "samsung_a16_support": "https://www.samsung.com/support/",
    "xiaomi_redmi_note_9_support": "https://www.mi.com/global/support/",
    "xiaomi_smart_band_8": "https://www.mi.com/global/product/xiaomi-smart-band-8/",
    "pldt_support": "https://pldthome.com/support",
    "cignal_support": "https://cignal.tv/support",
}

ILLUSTRATION_URLS = {
    "printer": "https://images.unsplash.com/photo-1612815154858-60aa4c59eaa6?auto=format&fit=crop&w=1200&q=80",
    "wifi": "https://images.unsplash.com/photo-1606904825846-647eb07f5be2?auto=format&fit=crop&w=1200&q=80",
    "phone": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1200&q=80",
    "laptop": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1200&q=80",
    "tv": "https://images.unsplash.com/photo-1593784991095-a205069470b6?auto=format&fit=crop&w=1200&q=80",
    "wearable": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?auto=format&fit=crop&w=1200&q=80",
    "apps": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1200&q=80",
    "general": "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=1200&q=80",
}

SCENARIO_PACKS: tuple[dict[str, object], ...] = (
    {
        "device": "Canon G3010",
        "category": "printer",
        "tags": ("canon", "g3010", "printer", "ink", "refill", "paper", "jam", "wifi", "print"),
        "image": ILLUSTRATION_URLS["printer"],
        "official": OFFICIAL_LINKS["canon_g3010_manual"],
        "scenarios": (
            "refill ink",
            "check ink level",
            "paper jam",
            "printer not printing",
            "connect printer to wifi",
            "load paper",
            "power cycle printer",
            "printer warning light",
        ),
    },
    {
        "device": "PLDT Fiber Internet",
        "category": "wifi",
        "tags": ("pldt", "fiber", "internet", "wifi", "router", "modem", "slow", "no internet", "lights"),
        "image": ILLUSTRATION_URLS["wifi"],
        "official": OFFICIAL_LINKS["pldt_support"],
        "scenarios": (
            "no wifi",
            "slow internet",
            "router lights",
            "restart modem",
            "check cables",
            "connect phone to wifi",
            "forgot wifi password",
            "internet outage",
        ),
    },
    {
        "device": "Samsung Galaxy A16",
        "category": "phone",
        "tags": ("samsung", "galaxy", "a16", "phone", "android", "screenshot", "wifi", "volume", "brightness"),
        "image": ILLUSTRATION_URLS["phone"],
        "official": OFFICIAL_LINKS["samsung_a16_support"],
        "scenarios": (
            "take screenshot",
            "connect to wifi",
            "adjust volume",
            "adjust brightness",
            "open messenger",
            "open viber",
            "open youtube",
            "restart phone",
        ),
    },
    {
        "device": "Xiaomi Redmi Note 9",
        "category": "phone",
        "tags": ("xiaomi", "redmi", "note 9", "phone", "android", "screenshot", "wifi", "volume", "brightness"),
        "image": ILLUSTRATION_URLS["phone"],
        "official": OFFICIAL_LINKS["xiaomi_redmi_note_9_support"],
        "scenarios": (
            "take screenshot",
            "connect to wifi",
            "adjust volume",
            "adjust brightness",
            "open messenger",
            "open viber",
            "open youtube",
            "restart phone",
        ),
    },
    {
        "device": "Asus laptop",
        "category": "laptop",
        "tags": ("asus", "laptop", "windows", "wifi", "browser", "download", "restart", "file"),
        "image": ILLUSTRATION_URLS["laptop"],
        "official": "https://www.asus.com/support/",
        "scenarios": (
            "connect laptop to wifi",
            "find downloaded file",
            "browser not loading",
            "restart laptop",
            "adjust volume",
            "adjust brightness",
            "open browser",
            "send screenshot",
        ),
    },
    {
        "device": "Cignal TV and common apps",
        "category": "apps",
        "tags": ("cignal", "tv", "youtube", "facebook", "messenger", "viber", "app", "video"),
        "image": ILLUSTRATION_URLS["tv"],
        "official": OFFICIAL_LINKS["cignal_support"],
        "scenarios": (
            "cignal no signal",
            "open youtube",
            "search youtube",
            "open facebook",
            "open messenger",
            "open viber",
            "send photo in messenger",
            "video not playing",
        ),
    },
    {
        "device": "Xiaomi Smart Band 8",
        "category": "wearable",
        "tags": ("xiaomi", "smart band 8", "wearable", "band", "bluetooth", "pair", "sync", "charge"),
        "image": ILLUSTRATION_URLS["wearable"],
        "official": OFFICIAL_LINKS["xiaomi_smart_band_8"],
        "scenarios": (
            "charge smart band",
            "pair smart band",
            "sync smart band",
            "bluetooth reconnect",
            "change watch face",
            "battery check",
            "wear band",
            "restart band",
        ),
    },
)


def build_media_catalog() -> list[MediaAsset]:
    assets: list[MediaAsset] = []
    for pack in SCENARIO_PACKS:
        device = str(pack["device"])
        category = str(pack["category"])
        tags = tuple(str(tag) for tag in pack["tags"])
        image = str(pack["image"])
        official = str(pack["official"])
        for index, scenario in enumerate(tuple(str(item) for item in pack["scenarios"]), start=1):
            slug = _slug(f"{device}-{scenario}")
            assets.extend(
                [
                    MediaAsset(
                        asset_id=f"{slug}-overview",
                        type="image",
                        url=image,
                        title=f"{device}: {scenario.title()}",
                        caption=f"Visual guide para sa {scenario}. Sundan muna ang unang step.",
                        device=device,
                        category=category,
                        language="taglish",
                        tags=tags + tuple(scenario.split()),
                        source="public",
                        safety_level="safe",
                        intended_use=f"Parent-friendly visual orientation for {scenario}.",
                    ),
                    MediaAsset(
                        asset_id=f"{slug}-official",
                        type="link",
                        url=official,
                        title=f"Official support: {device}",
                        caption="Official guide kung kailangan ng exact model instructions.",
                        device=device,
                        category=category,
                        language="en",
                        tags=tags + ("official", "manual", "support") + tuple(scenario.split()),
                        source="official",
                        safety_level="safe",
                        intended_use=f"Exact-source fallback for {scenario}.",
                    ),
                    MediaAsset(
                        asset_id=f"{slug}-step-{index}",
                        type="image",
                        url=image,
                        title=f"Step visual: {scenario.title()}",
                        caption="Tingnan ang picture, tapos gawin lang ang unang step. Pwede ring magtanong ulit.",
                        device=device,
                        category=category,
                        language="taglish",
                        tags=tags + ("step", "visual") + tuple(scenario.split()),
                        source="curated",
                        safety_level="safe",
                        intended_use=f"Simple one-step visual for {scenario}.",
                    ),
                ]
            )
    return assets


def plan_media_for_message(message: str, recent_chat: list[dict[str, str]] | None = None) -> MediaPlan:
    text = message.lower()
    intent = classify_media_intent(text)
    wants_visual = _wants_visual(text) or intent != "general"
    assets = select_media_assets(intent, text) if wants_visual else []
    generated_prompt = generated_prompt_for_message(intent, text, bool(assets))
    escalation_reason = escalation_reason_for_message(text, recent_chat or [])
    return MediaPlan(
        intent=intent,
        assets=assets,
        generated_prompt=generated_prompt,
        escalation_reason=escalation_reason,
    )


def classify_media_intent(text: str) -> str:
    category_terms = {
        "printer": ("printer", "canon", "g3010", "ink", "tinta", "paper", "print", "jam"),
        "wifi": ("wifi", "wi-fi", "internet", "pldt", "router", "modem", "fiber", "signal", "slow"),
        "wearable": ("smartband", "smart band", "band 8", "bluetooth", "pair", "sync", "watch"),
        "phone": ("phone", "samsung", "galaxy", "a16", "xiaomi", "redmi", "note 9", "android", "cellphone"),
        "laptop": ("laptop", "asus", "windows", "browser", "download", "file", "keyboard", "mouse"),
        "apps": ("facebook", "viber", "youtube", "messenger", "cignal", "tv", "app"),
    }
    for category, terms in category_terms.items():
        if any(term in text for term in terms):
            return category
    return "general"


def select_media_assets(intent: str, text: str, limit: int = 3) -> list[MediaAsset]:
    scored: list[tuple[int, MediaAsset]] = []
    words = set(re.findall(r"[a-z0-9]+", text))
    for asset in MEDIA_CATALOG:
        if intent != "general" and asset.category != intent:
            continue
        tag_matches = len(words.intersection(set(_normalize_tag(tag) for tag in asset.tags)))
        score = tag_matches
        if asset.category == intent:
            score += 5
        if asset.type == "image":
            score += 2
        if asset.source == "official":
            score += 1
        if score > 0:
            scored.append((score, asset))

    if not scored and _wants_visual(text):
        return [
            MediaAsset(
                asset_id="general-family-help",
                type="image",
                url=ILLUSTRATION_URLS["general"],
                title="General visual guide",
                caption="Sample visual para mas madaling sundan ang instructions.",
                device="General",
                category="general",
                language="taglish",
                tags=("general", "help", "visual"),
                source="public",
                safety_level="safe",
                intended_use="General family-help visual fallback.",
            )
        ]

    scored.sort(key=lambda item: item[0], reverse=True)
    selected: list[MediaAsset] = []
    seen_urls: set[str] = set()
    for _, asset in scored:
        if asset.url in seen_urls and asset.type == "image":
            continue
        selected.append(asset)
        seen_urls.add(asset.url)
        if len(selected) >= limit:
            break
    return selected


def generated_prompt_for_message(intent: str, text: str, has_curated_assets: bool) -> str | None:
    if not _wants_visual(text):
        return None
    risky_exact_terms = ("canon", "g3010", "router", "modem", "ink", "cignal", "smart band")
    if any(term in text for term in risky_exact_terms):
        return None
    if has_curated_assets and intent != "general":
        return None
    return (
        "Create a simple parent-friendly troubleshooting diagram with large labels, "
        "no tiny text, no exact brand internals, and one clear next step. "
        f"Topic: {text[:160]}"
    )


def escalation_reason_for_message(text: str, recent_chat: list[dict[str, str]]) -> str | None:
    frustration_terms = (
        "ayaw",
        "hindi gumagana",
        "di gumagana",
        "confusing",
        "nakakainis",
        "galit",
        "frustrated",
        "doesn't work",
        "dont work",
        "not working",
    )
    risky_terms = (
        "password",
        "otp",
        "bank",
        "payment",
        "reset",
        "factory reset",
        "admin",
        "account locked",
        "nasira",
        "smoke",
        "spark",
    )
    if any(term in text for term in risky_terms):
        return "risky_troubleshooting"
    if any(term in text for term in frustration_terms):
        return "user_frustrated"
    user_turns = [row for row in recent_chat[-6:] if row.get("role") == "user"]
    if len(user_turns) >= 3 and any(term in text for term in ("help", "tulong", "paulit", "again")):
        return "repeated_trouble"
    return None


def generate_and_store_diagram(prompt: str) -> MediaAsset | None:
    settings = get_settings()
    if not settings.openai_api_key or not settings.media_public_base_url:
        return None

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.images.generate(
            model=settings.openai_image_model,
            prompt=prompt,
            size="1024x1024",
            n=1,
        )
        image_data = response.data[0]
        if getattr(image_data, "b64_json", None):
            image_bytes = base64.b64decode(image_data.b64_json)
            public_url = store_media_bytes(image_bytes, "image/png")
        else:
            public_url = getattr(image_data, "url", None)
        if not public_url:
            return None
    except Exception:
        return None

    return MediaAsset(
        asset_id=f"generated-{uuid4().hex}",
        type="image",
        url=public_url,
        title="Generated helper diagram",
        caption="Generated diagram para mas madaling sundan. Kung iba ang itsura ng device, sabihin agad.",
        device="General",
        category="general",
        language="taglish",
        tags=("generated", "diagram", "visual"),
        source="generated",
        safety_level="safe_generic",
        intended_use="Generic parent-friendly troubleshooting diagram.",
    )


def store_media_bytes(image_bytes: bytes, content_type: str) -> str | None:
    settings = get_settings()
    if not (
        settings.r2_account_id
        and settings.r2_bucket_name
        and settings.r2_access_key_id
        and settings.r2_secret_access_key
        and settings.media_public_base_url
    ):
        return None

    try:
        import boto3
    except ImportError:
        return None

    key = f"generated/{uuid4().hex}.png"
    endpoint_url = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )
    client.put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=image_bytes,
        ContentType=content_type,
    )
    return f"{settings.media_public_base_url.rstrip('/')}/{key}"


def notify_john(escalation: dict[str, str]) -> None:
    settings = get_settings()
    if not settings.john_notify_webhook_url:
        return
    request = Request(
        settings.john_notify_webhook_url,
        data=json.dumps(escalation).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urlopen(request, timeout=5).read()
    except (OSError, URLError, ValueError):
        return


def _wants_visual(text: str) -> bool:
    return any(
        term in text
        for term in (
            "image",
            "images",
            "photo",
            "photos",
            "picture",
            "pictures",
            "larawan",
            "screenshot",
            "video",
            "visual",
            "show me",
            "send me",
            "paano",
            "how",
            "help",
            "tulong",
        )
    )


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _normalize_tag(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


MEDIA_CATALOG = build_media_catalog()

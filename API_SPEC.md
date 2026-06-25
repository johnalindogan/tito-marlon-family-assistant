# Tito Marlon Backend API Spec

## Health Check

### GET `/health`

Response:

```json
{
  "status": "ok"
}
```

## Process Message

### POST `/message`

Request:

```json
{
  "sender_id": "26741790695498132",
  "message": "Ano ang paborito kong pagkain?",
  "image_urls": [],
  "messenger_profile": {
    "first_name": "Nelon",
    "last_name": "Alindogan",
    "profile_pic": "https://example.com/profile.jpg",
    "locale": "en_US",
    "timezone": 8
  }
}
```

`message` may be blank when `image_urls` contains at least one image URL. The
backend accepts up to 3 image URLs per request.

Response:

```json
{
  "reply": "Paborito mong pagkain ay Sinigang.",
  "memories_saved": [],
  "outbound_image_urls": [],
  "outbound_media": [
    {
      "type": "image",
      "url": "https://example.com/media/printer-ink.png",
      "title": "Canon G3010: Refill Ink",
      "caption": "Visual guide para sa refill ink. Sundan muna ang unang step.",
      "source": "curated"
    }
  ],
  "escalation_request": {
    "reason": "user_frustrated",
    "summary": "Parent may need help with: Ayaw gumana ang printer",
    "urgency": "normal",
    "suggested_action": "Notify John first with this context; ask him to call if needed."
  },
  "identified_family_member": {
    "member_key": "nelon_alindogan",
    "full_name": "Nelon Alindogan",
    "preferred_name": "Papa Nelon",
    "relationship_label": "Papa Nelon / Grandpa Nelon",
    "aliases": ["Papa Nelon", "Grandpa Nelon", "Granpa Nelon", "Nelon"],
    "facebook_url": "https://www.facebook.com/leaderalindogan"
  },
  "messenger_contact": {
    "sender_id": "26741790695498132",
    "first_name": "Nelon",
    "last_name": "Alindogan",
    "profile_pic": "https://example.com/profile.jpg",
    "locale": "en_US",
    "timezone": 8,
    "family_member_key": "nelon_alindogan"
  }
}
```

`messenger_profile` is optional. When supplied by n8n from Meta's profile lookup, the backend caches it in `messenger_contacts`.

`identified_family_member` is `null` until the Messenger contact exact-name matches a seeded family member or is manually linked.

`outbound_image_urls` remains for the current n8n Messenger image attachment nodes. `outbound_media` is the richer media contract for images, links, videos, and generated diagrams.

`escalation_request` is optional. When present, n8n should notify John first and keep the parent-facing conversation calm.

## Media Behavior

The backend uses a hybrid media planner:

- curated assets first for known parent devices and apps
- generated diagrams only for safe generic visuals
- official links as exact-source fallbacks
- early escalation for frustration, risky account/password/reset flows, or repeated trouble

Configured launch devices include Canon G3010, PLDT Fiber internet, Samsung Galaxy A16, Xiaomi Redmi Note 9, Asus laptop/Windows basics, Cignal/YouTube/Facebook/Messenger/Viber, and Xiaomi Smart Band 8.

Generated image support is optional. Set `OPENAI_IMAGE_MODEL`, `MEDIA_PUBLIC_BASE_URL`, and R2 credentials before expecting generated images to be hosted and sent through Messenger.

## Error Handling

Return `400` if:
- `sender_id` missing
- both `message` and `image_urls` are missing or blank
- `message` is not text
- an image URL is not `http` or `https`

Return `500` for server/internal errors.

Avoid returning stack traces in production.

## Notes

The backend should be independent of Facebook payload format. n8n should convert Facebook payload to backend request format.

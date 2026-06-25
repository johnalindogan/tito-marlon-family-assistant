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
  "image_urls": []
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
  "identified_family_member": {
    "member_key": "nelon_alindogan",
    "full_name": "Nelon Alindogan",
    "preferred_name": "Papa Nelon",
    "relationship_label": "Papa Nelon / Grandpa Nelon",
    "aliases": ["Papa Nelon", "Grandpa Nelon", "Granpa Nelon", "Nelon"],
    "facebook_url": "https://www.facebook.com/leaderalindogan"
  }
}
```

`identified_family_member` is `null` until the Messenger `sender_id` has been linked to a seeded family member.

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

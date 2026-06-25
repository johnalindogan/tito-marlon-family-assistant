from app import database
from app.ai import extract_memories, generate_reply
from app.media import (
    MediaAsset,
    generate_and_store_diagram,
    notify_john,
    plan_media_for_message,
)
from app.outbound_images import outbound_image_urls_for_message
from app.schemas import (
    EscalationRequest,
    FamilyMemberProfile,
    MessageRequest,
    MessageResponse,
    MessengerContactProfile,
    OutboundMedia,
)


def process_message(payload: MessageRequest) -> MessageResponse:
    memories_saved = extract_memories(payload.message) if payload.message else []
    legacy_image_urls = outbound_image_urls_for_message(payload.message)
    stored_user_message = payload.message
    if payload.image_urls:
        stored_user_message = f"{payload.message}\n[Photo attached]".strip()

    with database.session_scope() as session:
        family_member = None
        messenger_contact = None
        memory_identity_id = payload.sender_id
        if session is not None:
            if payload.messenger_profile is not None:
                messenger_contact = database.upsert_messenger_contact(
                    session,
                    payload.sender_id,
                    payload.messenger_profile.model_dump(),
                )
            else:
                messenger_contact = database.load_messenger_contact(session, payload.sender_id)

            family_member_key = (
                str(messenger_contact["family_member_key"])
                if messenger_contact and messenger_contact.get("family_member_key")
                else None
            )
            if family_member_key:
                family_member = database.load_family_member_by_key(session, family_member_key)
            if family_member is None:
                family_member = database.load_family_member_by_sender_id(session, payload.sender_id)
            if family_member is not None:
                memory_identity_id = str(family_member["member_key"])

            database.save_chat_message(session, payload.sender_id, "user", stored_user_message)
            for memory in memories_saved:
                database.upsert_memory(
                    session,
                    memory_identity_id,
                    memory.memory_key,
                    memory.memory_value,
                )
            recent_chat = database.load_recent_chat(session, payload.sender_id)
            memory = database.load_memory(session, memory_identity_id)
        else:
            recent_chat = []
            memory = {}
            family_member = None
            messenger_contact = None

        media_plan = plan_media_for_message(payload.message, recent_chat)
        media_assets = list(media_plan.assets)
        if media_plan.generated_prompt:
            generated_asset = generate_and_store_diagram(media_plan.generated_prompt)
            if generated_asset is not None:
                media_assets.insert(0, generated_asset)

        reply = generate_reply(
            payload.sender_id,
            payload.message,
            payload.image_urls,
            family_member,
            messenger_contact,
            recent_chat,
            memory,
        )

        if session is not None:
            database.save_chat_message(session, payload.sender_id, "assistant", reply)

    outbound_media = [_to_outbound_media(asset) for asset in media_assets]
    outbound_image_urls = _merge_image_urls(_image_urls(media_assets), legacy_image_urls)
    if outbound_image_urls:
        reply = _align_reply_with_outbound_images(reply)
    reply = _append_media_links_to_reply(reply, media_assets)

    escalation_request = _build_escalation_request(payload.message, media_plan.escalation_reason)
    if escalation_request is not None:
        notify_john(escalation_request.model_dump())
        reply = _align_reply_with_escalation(reply)

    return MessageResponse(
        reply=reply,
        memories_saved=memories_saved,
        outbound_image_urls=outbound_image_urls,
        outbound_media=outbound_media,
        escalation_request=escalation_request,
        identified_family_member=(
            FamilyMemberProfile.model_validate(family_member) if family_member is not None else None
        ),
        messenger_contact=(
            MessengerContactProfile.model_validate(messenger_contact)
            if messenger_contact is not None
            else None
        ),
    )


def _align_reply_with_outbound_images(reply: str) -> str:
    lowered = reply.lower()
    cannot_send_phrases = (
        "hindi ako makapag-send",
        "hindi po ako makapag-send",
        "hindi pa kaya",
        "cannot send",
        "can't send",
    )
    if any(phrase in lowered for phrase in cannot_send_phrases):
        return "Sige po, magpapadala ako ng ilang sample photos sa baba para may idea kayo."

    if "image" in lowered or "photo" in lowered or "larawan" in lowered:
        return reply

    return f"{reply}\n\nMagpapadala rin ako ng ilang sample photos sa baba para mas madaling makita."


def _to_outbound_media(asset: MediaAsset) -> OutboundMedia:
    return OutboundMedia(
        type=asset.type,
        url=asset.url,
        title=asset.title,
        caption=asset.caption,
        source=asset.source,
    )


def _image_urls(media_assets: list[MediaAsset]) -> list[str]:
    urls: list[str] = []
    for asset in media_assets:
        if asset.type == "image" and asset.url.startswith(("http://", "https://")):
            urls.append(asset.url)
        if len(urls) >= 3:
            break
    return urls


def _merge_image_urls(primary: list[str], fallback: list[str]) -> list[str]:
    merged: list[str] = []
    for url in [*primary, *fallback]:
        if url not in merged:
            merged.append(url)
        if len(merged) >= 3:
            break
    return merged


def _append_media_links_to_reply(reply: str, media_assets: list[MediaAsset]) -> str:
    link_assets = [
        asset
        for asset in media_assets
        if asset.type in {"link", "video"} and asset.url not in reply
    ]
    if not link_assets:
        return reply

    lines = ["Useful link:"]
    for asset in link_assets[:2]:
        lines.append(f"- {asset.title}: {asset.url}")
    return f"{reply}\n\n" + "\n".join(lines)


def _build_escalation_request(message: str, reason: str | None) -> EscalationRequest | None:
    if reason is None:
        return None
    urgency = "high" if reason == "risky_troubleshooting" else "normal"
    return EscalationRequest(
        reason=reason,
        summary=f"Parent may need help with: {message[:240]}",
        urgency=urgency,
        suggested_action="Notify John first with this context; ask him to call if needed.",
    )


def _align_reply_with_escalation(reply: str) -> str:
    escalation_text = "I-message ko muna si John para masigurado natin."
    if escalation_text.lower() in reply.lower():
        return reply
    return f"{reply}\n\n{escalation_text}"

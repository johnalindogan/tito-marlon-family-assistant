from app import database
from app.ai import extract_memories, generate_reply
from app.schemas import MessageRequest, MessageResponse


def process_message(payload: MessageRequest) -> MessageResponse:
    memories_saved = extract_memories(payload.message) if payload.message else []
    stored_user_message = payload.message
    if payload.image_urls:
        stored_user_message = f"{payload.message}\n[Photo attached]".strip()

    with database.session_scope() as session:
        if session is not None:
            database.save_chat_message(session, payload.sender_id, "user", stored_user_message)
            for memory in memories_saved:
                database.upsert_memory(
                    session,
                    payload.sender_id,
                    memory.memory_key,
                    memory.memory_value,
                )
            recent_chat = database.load_recent_chat(session, payload.sender_id)
            memory = database.load_memory(session, payload.sender_id)
        else:
            recent_chat = []
            memory = {}

        reply = generate_reply(
            payload.sender_id,
            payload.message,
            payload.image_urls,
            recent_chat,
            memory,
        )

        if session is not None:
            database.save_chat_message(session, payload.sender_id, "assistant", reply)

    return MessageResponse(reply=reply, memories_saved=memories_saved)

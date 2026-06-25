from app import database
from app.ai import extract_memories, generate_reply
from app.schemas import MessageRequest, MessageResponse


def process_message(payload: MessageRequest) -> MessageResponse:
    memories_saved = extract_memories(payload.message)

    with database.session_scope() as session:
        if session is not None:
            database.save_chat_message(session, payload.sender_id, "user", payload.message)
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

        reply = generate_reply(payload.sender_id, payload.message, recent_chat, memory)

        if session is not None:
            database.save_chat_message(session, payload.sender_id, "assistant", reply)

    return MessageResponse(reply=reply, memories_saved=memories_saved)

"""记忆管理 API — 查看和清除会话记忆、获取历史消息、列出会话"""

from fastapi import APIRouter, Request

from app.models.schemas import MemoryInfo, MemoryClearResponse, ChatHistoryResponse, SessionListItem

router = APIRouter(tags=["memory"])


@router.get("/memory/{session_id}", response_model=MemoryInfo)
async def get_memory(request: Request, session_id: str):
    """查看会话记忆状态"""
    app_state = request.app.state

    short_info = app_state.conversation_memory.get_info(session_id)
    long_facts = app_state.long_term_memory.get_facts(session_id)

    return MemoryInfo(
        session_id=session_id,
        short_term=short_info,
        long_term={
            "fact_count": len(long_facts),
            "facts": long_facts,
        },
    )


@router.get("/memory/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(request: Request, session_id: str):
    """获取会话的聊天历史记录（用于页面刷新后恢复）"""
    app_state = request.app.state
    messages = app_state.conversation_memory.get_history(session_id)
    return ChatHistoryResponse(
        session_id=session_id,
        messages=messages,
        count=len(messages),
    )


@router.get("/sessions", response_model=list[SessionListItem])
async def list_sessions(request: Request):
    """列出所有活跃会话"""
    app_state = request.app.state
    sessions = app_state.conversation_memory.list_sessions()
    return [
        SessionListItem(
            session_id=s["session_id"],
            turn_count=s["turn_count"],
            last_accessed=s.get("last_accessed_formatted", ""),
        )
        for s in sessions
    ]


@router.delete("/memory/{session_id}", response_model=MemoryClearResponse)
async def clear_memory(request: Request, session_id: str):
    """清除会话的全部记忆"""
    app_state = request.app.state

    app_state.conversation_memory.clear(session_id)
    app_state.long_term_memory.delete_session(session_id)

    return MemoryClearResponse(
        status="cleared",
        session_id=session_id,
    )

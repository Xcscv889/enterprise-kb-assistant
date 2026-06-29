"""聊天 API — SSE 流式端点"""

import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest
from app.rag.pipeline import RAGPipeline

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """发送消息，SSE 流式返回回答"""

    app_state = request.app.state

    # 构建 RAG 管道
    pipeline = RAGPipeline(
        vector_store=app_state.vector_store,
        embedding_service=app_state.embedding_service,
        llm_client=app_state.llm_client,
        conversation_memory=app_state.conversation_memory,
        long_term_memory=app_state.long_term_memory,
    )

    async def event_generator():
        try:
            async for event in pipeline.query_stream(body.query, body.session_id):
                event_type = event.get("type", "token")
                if event_type == "token":
                    # 流式 token
                    yield f"data: {json.dumps({'token': event['content']}, ensure_ascii=False)}\n\n"
                elif event_type == "done":
                    # 完成信号，附带来源
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

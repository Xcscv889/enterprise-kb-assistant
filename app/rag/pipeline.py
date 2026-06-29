"""RAG 管道编排器 — 检索→增强→生成 全流程"""

import json

from app.core.prompts import RAG_SYSTEM_PROMPT, NO_RESULTS_PROMPT
from config import settings


class RAGPipeline:
    """编排完整的 RAG 问答流程"""

    def __init__(self, vector_store, embedding_service, llm_client,
                 conversation_memory, long_term_memory):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.llm = llm_client
        self.conversation_memory = conversation_memory
        self.long_term_memory = long_term_memory

    async def query_stream(self, query: str, session_id: str):
        """处理用户查询，流式返回回答 token"""

        # ── Stage 1: 查询嵌入 ──
        query_embedding = self.embedding_service.encode_query(query)

        # ── Stage 2: 记忆检索 ──
        conversation_history = self.conversation_memory.get_history(session_id)
        long_term_facts = self.long_term_memory.retrieve_relevant(
            query_embedding, session_id
        )

        memory_context = ""
        if long_term_facts:
            memory_context = "## 用户相关记忆\n" + "\n".join(
                f"- {fact}" for fact in long_term_facts
            ) + "\n"

        # ── Stage 3: 文档检索 ──
        from app.rag.retriever import Retriever
        retriever = Retriever(self.vector_store, self.embedding_service)
        retrieved = retriever.retrieve(query)

        # ── Stage 4: 上下文组装 ──
        if retrieved:
            # 格式化检索结果
            context_parts = []
            for i, chunk in enumerate(retrieved, start=1):
                source = chunk.get("filename", "未知")
                context_parts.append(
                    f"[文档{i}] 来源: {source}\n{chunk['text']}"
                )
            retrieved_context = "## 检索到的相关文档内容\n\n" + "\n\n".join(context_parts)
            system_prompt = RAG_SYSTEM_PROMPT.format(
                memory_context=memory_context,
                retrieved_context=retrieved_context,
            )
        else:
            system_prompt = NO_RESULTS_PROMPT.format(
                memory_context=memory_context,
            )

        # 组装消息列表
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history:
            messages.append(msg)
        messages.append({"role": "user", "content": query})

        # ── Stage 5: 流式生成 ──
        full_response = ""
        async for token in self.llm.chat_stream(messages):
            full_response += token
            yield {"type": "token", "content": token}

        # ── 后处理: 更新记忆 ──
        self.conversation_memory.add_exchange(session_id, query, full_response)

        # 每 N 轮触发长期记忆合成
        turn_count = self.conversation_memory.get_turn_count(session_id)
        if turn_count > 0 and turn_count % settings.long_term_synthesis_interval == 0:
            recent = self.conversation_memory.get_recent_exchanges(
                session_id, settings.long_term_synthesis_interval
            )
            if recent:
                await self.long_term_memory.synthesize_and_store(session_id, recent)

        # 返回来源信息
        sources = [
            {
                "filename": c.get("filename", "未知"),
                "page": c.get("page"),
                "chunk_id": str(c.get("chunk_index", "")),
                "score": round(1 - c.get("distance", 0), 4),
            }
            for c in retrieved
        ]
        yield {"type": "done", "sources": sources, "session_id": session_id}

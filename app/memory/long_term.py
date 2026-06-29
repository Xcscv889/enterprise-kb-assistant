"""长期记忆 — ChromaDB 持久化 + LLM 事实提取"""

import json
import re

from app.core.prompts import MEMORY_SYNTHESIS_PROMPT
from config import settings


class LongTermMemory:
    """存储在 ChromaDB 中的持久化记忆"""

    def __init__(self, vector_store, embedding_service, llm_client):
        self.store = vector_store
        self.embedding_service = embedding_service
        self.llm = llm_client
        self.synthesis_interval = settings.long_term_synthesis_interval

    def retrieve_relevant(self, query_embedding, session_id: str) -> list[str]:
        """检索与当前查询相关的长期记忆"""
        results = self.store.query_memory(query_embedding, session_id, n_results=3)
        facts = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]

        relevant = []
        for fact, dist in zip(facts, distances):
            if dist <= 0.7:  # 稍宽松的阈值
                relevant.append(fact)
        return relevant

    async def synthesize_and_store(self, session_id: str, recent_exchanges: list[dict]):
        """让 LLM 从最近对话中提取事实并存储"""
        history_text = "\n".join(
            f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
            for m in recent_exchanges
        )

        prompt = MEMORY_SYNTHESIS_PROMPT.format(conversation_history=history_text)

        messages = [
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.llm.chat(messages)

            # 解析 JSON 数组
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                facts = json.loads(json_match.group())
                for fact in facts:
                    if fact and len(fact) > 5:
                        self.store.add_memory_fact(fact, session_id)
        except Exception:
            pass  # 记忆合成失败不影响主流程

    def delete_session(self, session_id: str) -> int:
        """删除某会话的全部长期记忆"""
        return self.store.delete_memory_by_session(session_id)

    def get_facts(self, session_id: str) -> list[str]:
        """获取某会话已存储的所有事实"""
        try:
            results = self.store.memory_collection.get(
                where={"session_id": session_id},
                include=["documents"],
            )
            return results.get("documents", []) or []
        except Exception:
            return []

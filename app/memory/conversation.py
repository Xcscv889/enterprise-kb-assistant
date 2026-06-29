"""短期记忆 — 会话级滑动窗口"""

import time
from collections import defaultdict

from config import settings


class ConversationMemory:
    """内存中的会话历史管理"""

    def __init__(self):
        self._store: dict[str, dict] = defaultdict(lambda: {
            "messages": [],
            "last_accessed": time.time(),
            "turn_count": 0,
        })
        self.max_messages = settings.short_term_max_messages
        self.ttl_seconds = settings.short_term_ttl_seconds

    def get_history(self, session_id: str) -> list[dict]:
        """获取会话的最近消息历史"""
        session = self._store[session_id]
        session["last_accessed"] = time.time()
        return list(session["messages"])

    def get_recent_exchanges(self, session_id: str, n: int) -> list[dict]:
        """获取最近 n 轮对话"""
        session = self._store[session_id]
        session["last_accessed"] = time.time()
        all_msgs = session["messages"]
        return all_msgs[-(n * 2):]  # n 轮 = 2n 条消息

    def add_exchange(self, session_id: str, user_msg: str, assistant_msg: str):
        """存储一轮对话"""
        session = self._store[session_id]
        session["messages"].append({"role": "user", "content": user_msg})
        session["messages"].append({"role": "assistant", "content": assistant_msg})
        session["turn_count"] += 1
        session["last_accessed"] = time.time()

        # 滑动窗口裁剪
        if len(session["messages"]) > self.max_messages:
            session["messages"] = session["messages"][-self.max_messages:]

    def get_turn_count(self, session_id: str) -> int:
        return self._store[session_id]["turn_count"]

    def get_info(self, session_id: str) -> dict:
        session = self._store[session_id]
        return {
            "message_count": len(session["messages"]),
            "turn_count": session["turn_count"],
            "last_accessed": session["last_accessed"],
        }

    def list_sessions(self) -> list[dict]:
        """列出所有活跃会话（非过期）"""
        now = time.time()
        result = []
        for sid, s in self._store.items():
            last = s["last_accessed"]
            if now - last < self.ttl_seconds:
                result.append({
                    "session_id": sid,
                    "turn_count": s["turn_count"],
                    "last_accessed": last,
                    "last_accessed_formatted": time.strftime(
                        "%Y-%m-%d %H:%M", time.localtime(last)
                    ),
                })
        # 按最近访问时间倒序
        result.sort(key=lambda x: x["last_accessed"], reverse=True)
        return result

    def clear(self, session_id: str):
        self._store.pop(session_id, None)

    def cleanup_expired(self):
        """清理超时会话"""
        now = time.time()
        expired = [
            sid for sid, s in self._store.items()
            if now - s["last_accessed"] > self.ttl_seconds
        ]
        for sid in expired:
            del self._store[sid]

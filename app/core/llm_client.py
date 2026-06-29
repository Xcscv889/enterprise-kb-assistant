"""DeepSeek LLM 客户端 — OpenAI 兼容 SDK"""

from openai import AsyncOpenAI

from config import settings


class LLMClient:
    """通过 OpenAI 兼容接口调用 DeepSeek API"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        self.model = settings.deepseek_model
        self.temperature = settings.deepseek_temperature
        self.max_tokens = settings.deepseek_max_tokens

    async def chat_stream(self, messages: list[dict]):
        """流式聊天补全，逐 token yield"""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    async def chat(self, messages: list[dict]) -> str:
        """非流式聊天补全，返回完整回复"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False,
        )
        return response.choices[0].message.content or ""

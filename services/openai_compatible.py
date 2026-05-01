"""
OpenAI 兼容接口实现
支持任意 OpenAI API 兼容的大模型服务（DeepSeek、OpenAI、Moonshot 等）
"""

import logging
from typing import Dict, List, Optional, Generator

from .interface.llm_interface import LLMInterface, Message, ChatResponse

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(LLMInterface):

    def __init__(
        self,
        model_name: str = "deepseek-chat",
        api_key: str = "",
        base_url: str = "https://api.deepseek.com/v1"
    ):
        self._default_base_url = base_url
        super().__init__(model_name, api_key, base_url)

    def _get_default_base_url(self) -> str:
        return self._default_base_url

    def _get_client(self):
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> ChatResponse:
        client = self._get_client()
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        logger.info(
            "OpenAI-compatible chat request model=%s messages=%s stream=%s max_tokens=%s",
            self.model_name,
            len(openai_messages),
            stream,
            max_tokens
        )

        response = client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        content = response.choices[0].message.content
        usage = (
            {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            if response.usage
            else None
        )
        logger.info(
            "OpenAI-compatible chat response model=%s chars=%s finish_reason=%s usage=%s",
            self.model_name,
            len(content or ""),
            response.choices[0].finish_reason,
            usage or {}
        )

        return ChatResponse(
            content=content,
            model=self.model_name,
            usage=usage,
            finish_reason=response.choices[0].finish_reason
        )

    def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Generator[str, None, None]:
        client = self._get_client()
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        logger.info(
            "OpenAI-compatible stream request model=%s messages=%s max_tokens=%s",
            self.model_name,
            len(openai_messages),
            max_tokens
        )

        response = client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        chunk_count = 0
        char_count = 0
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                if delta.content:
                    chunk_count += 1
                    char_count += len(delta.content)
                    yield delta.content
        logger.info(
            "OpenAI-compatible stream response model=%s chunks=%s chars=%s",
            self.model_name,
            chunk_count,
            char_count
        )

    def get_model_info(self) -> Dict:
        return {
            "model": self.model_name,
            "base_url": self.base_url,
            "supports_streaming": True,
            "provider": "openai-compatible"
        }

    def test_connection(self) -> Dict:
        try:
            logger.info("OpenAI-compatible test_connection start model=%s", self.model_name)
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            logger.info("OpenAI-compatible test_connection success model=%s", self.model_name)
            return {
                "success": True,
                "model": self.model_name,
                "message": "Connection successful"
            }
        except Exception as e:
            logger.exception("OpenAI-compatible test_connection failed model=%s error=%s", self.model_name, e)
            return {
                "success": False,
                "model": self.model_name,
                "message": str(e)
            }

"""
大语言模型接口定义
用于定义统一的 LLM 接口，支持未来切换不同模型提供商
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Generator
from dataclasses import dataclass


@dataclass
class Message:
    """消息数据结构"""
    role: str  # 'system', 'user', 'assistant'
    content: str


@dataclass
class ChatResponse:
    """聊天响应数据结构"""
    content: str
    model: str
    usage: Optional[Dict] = None
    finish_reason: Optional[str] = None


class LLMInterface(ABC):
    """
    大语言模型接口抽象基类
    所有 LLM 提供商必须实现此接口
    """

    def __init__(self, model_name: str, api_key: str, base_url: str = ""):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url or self._get_default_base_url()

    @abstractmethod
    def _get_default_base_url(self) -> str:
        """获取默认 API 基础地址"""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> ChatResponse:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            temperature: 创造性参数 (0-1)
            max_tokens: 最大输出 token 数
            stream: 是否流式输出

        Returns:
            ChatResponse: 响应对象
        """
        pass

    @abstractmethod
    def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Generator[str, None, None]:
        """
        流式发送聊天请求

        Args:
            messages: 消息列表
            temperature: 创造性参数 (0-1)
            max_tokens: 最大输出 token 数

        Yields:
            str: 逐段生成的内容
        """
        pass

    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            "model": self.model_name,
            "base_url": self.base_url,
            "supports_streaming": True
        }

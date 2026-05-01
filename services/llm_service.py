"""
大模型服务混合模式
支持用户配置的大模型接入，自动降级到规则引擎
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Generator

from .interface.llm_interface import LLMInterface, Message, ChatResponse
from .openai_compatible import OpenAICompatibleProvider
from .prompt_engine import PromptBuilder, MoodContext

logger = logging.getLogger(__name__)

DEFAULT_LLM_CONFIG = {
    "enabled": False,
    "base_url": "",
    "api_key": "",
    "model": "deepseek-chat",
    "temperature": 0.7
}


class LLMService:

    def __init__(self):
        self._provider_cache: Dict[str, LLMInterface] = {}

    def is_llm_configured(self, user_llm_config: Optional[Dict] = None) -> bool:
        config = self._merge_config(user_llm_config)
        return config.get("enabled", False) and bool(config.get("api_key")) and bool(config.get("base_url"))

    def _merge_config(self, user_config: Optional[Dict] = None) -> Dict:
        config = dict(DEFAULT_LLM_CONFIG)
        if user_config:
            config.update({k: v for k, v in user_config.items() if v is not None})
        if not config.get("base_url"):
            config["base_url"] = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        if not config.get("api_key"):
            config["api_key"] = os.getenv("DEEPSEEK_API_KEY", "")
        if not config.get("model"):
            config["model"] = os.getenv("LLM_MODEL", "deepseek-chat")
        if not config.get("temperature"):
            try:
                config["temperature"] = float(os.getenv("LLM_TEMPERATURE", "0.7"))
            except (ValueError, TypeError):
                config["temperature"] = 0.7
        return config

    def _get_cache_key(self, config: Dict) -> str:
        return f"{config.get('base_url', '')}|{config.get('api_key', '')}|{config.get('model', '')}"

    def _get_provider(self, user_config: Optional[Dict] = None) -> LLMInterface:
        config = self._merge_config(user_config)
        cache_key = self._get_cache_key(config)
        if cache_key not in self._provider_cache:
            self._provider_cache[cache_key] = OpenAICompatibleProvider(
                model_name=config["model"],
                api_key=config["api_key"],
                base_url=config["base_url"]
            )
        return self._provider_cache[cache_key]

    def chat(
        self,
        messages: List[Message],
        user_config: Optional[Dict] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1024
    ) -> Tuple[bool, Optional[ChatResponse], Optional[str]]:
        config = self._merge_config(user_config)
        provider = self._get_provider(user_config)
        temp = temperature if temperature is not None else config.get("temperature", 0.7)
        try:
            response = provider.chat(
                messages,
                temperature=temp,
                max_tokens=max_tokens,
                stream=False
            )
            logger.info(f"LLM response: {len(response.content)} chars, model={response.model}")
            return True, response, None
        except Exception as e:
            error_msg = f"LLM call failed: {e}"
            logger.error(error_msg)
            return False, None, error_msg

    def chat_with_fallback(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        mood_context: Optional[MoodContext] = None,
        user_config: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> Tuple[bool, str, str]:
        if not self.is_llm_configured(user_config):
            return False, "", "rule_engine"

        config = self._merge_config(user_config)
        prompt_builder = PromptBuilder(
            preferences=prompt_engine_prefs_from_dict(user_preferences) if user_preferences else None
        )

        system_prompt = prompt_builder.build_system_prompt()
        user_msg = prompt_builder.build_user_message(
            user_message,
            conversation_history,
            mood_context
        )

        messages = [
            Message(role="system", content=system_prompt),
        ]
        if conversation_history:
            for msg in conversation_history[-10:]:
                messages.append(Message(role=msg["role"], content=msg["content"]))
        messages.append(Message(role="user", content=user_msg))

        success, response, error = self.chat(messages, user_config=user_config)
        if success and response:
            return True, response.content, "llm"
        else:
            logger.warning(f"LLM failed, falling back to rule engine: {error}")
            return False, "", "rule_engine"

    def chat_stream(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        mood_context=None,
        user_config: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> Generator[str, None, None]:
        """流式对话，逐 token 返回"""
        if not self.is_llm_configured(user_config):
            return

        config = self._merge_config(user_config)
        from .prompt_engine import PromptBuilder
        prompt_builder = PromptBuilder(
            preferences=prompt_engine_prefs_from_dict(user_preferences) if user_preferences else None
        )

        system_prompt = prompt_builder.build_system_prompt()
        user_msg = prompt_builder.build_user_message(
            user_message, conversation_history, mood_context
        )

        messages = [Message(role="system", content=system_prompt)]
        if conversation_history:
            for msg in conversation_history[-10:]:
                messages.append(Message(role=msg["role"], content=msg["content"]))
        messages.append(Message(role="user", content=user_msg))

        provider = self._get_provider(user_config)
        temp = config.get("temperature", 0.7)
        try:
            for chunk in provider.chat_stream(messages, temperature=temp, max_tokens=1024):
                yield chunk
        except Exception as e:
            logger.error(f"LLM stream failed: {e}")
            return

    def test_connection(self, user_config: Optional[Dict] = None) -> Dict:
        config = self._merge_config(user_config)
        if not config.get("api_key") or not config.get("base_url"):
            return {
                "success": False,
                "message": "API Key and Base URL are required"
            }
        provider = OpenAICompatibleProvider(
            model_name=config["model"],
            api_key=config["api_key"],
            base_url=config["base_url"]
        )
        return provider.test_connection()

    def clear_cache(self):
        self._provider_cache.clear()


def prompt_engine_prefs_from_dict(d: Dict):
    from .prompt_engine import UserPreferences
    return UserPreferences(
        response_style=d.get("response_style", "warm"),
        response_length=d.get("response_length", "medium"),
        use_emoji=d.get("use_emoji", True),
        pet_name=d.get("pet_name", "亲爱的")
    )


def parse_llm_config(raw: Optional[str]) -> Dict:
    if not raw:
        return dict(DEFAULT_LLM_CONFIG)
    try:
        config = json.loads(raw)
        merged = dict(DEFAULT_LLM_CONFIG)
        merged.update(config)
        return merged
    except (json.JSONDecodeError, TypeError):
        return dict(DEFAULT_LLM_CONFIG)


def serialize_llm_config(config: Dict) -> str:
    return json.dumps(config, ensure_ascii=False)

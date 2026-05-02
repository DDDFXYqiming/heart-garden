"""
大模型服务混合模式
支持用户配置的大模型接入，自动降级到规则引擎
"""

import os
import json
import logging
import re
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Generator

from .interface.llm_interface import LLMInterface, Message, ChatResponse
from .openai_compatible import OpenAICompatibleProvider
from .prompt_engine import PromptBuilder, MoodContext
from .security import sanitize_output

logger = logging.getLogger(__name__)

DEFAULT_LLM_CONFIG = {
    "enabled": False,
    "base_url": "",
    "api_key": "",
    "model": "deepseek-chat",
    "temperature": 0.7
}

MOOD_LABELS = {'开心', '平静', '中性', '焦虑', '悲伤'}
TREND_LABELS = {'上升', '平稳', '下降'}
MOOD_SCORE_RANGES = {
    '开心': (75.0, 100.0, 82.0),
    '平静': (60.0, 74.9, 67.0),
    '中性': (40.0, 59.9, 50.0),
    '焦虑': (25.0, 39.9, 32.0),
    '悲伤': (0.0, 24.9, 18.0),
}
MOOD_LABEL_ALIASES = {
    '快乐': '开心',
    '高兴': '开心',
    '喜悦': '开心',
    '兴奋': '开心',
    '满足': '开心',
    '成就': '开心',
    '积极': '开心',
    '平和': '平静',
    '放松': '平静',
    '安定': '平静',
    '轻松': '平静',
    '普通': '中性',
    '一般': '中性',
    '平淡': '中性',
    '中立': '中性',
    '紧张': '焦虑',
    '担心': '焦虑',
    '害怕': '焦虑',
    '压力': '焦虑',
    '烦躁': '焦虑',
    '愤怒': '焦虑',
    '难过': '悲伤',
    '伤心': '悲伤',
    '失落': '悲伤',
    '沮丧': '悲伤',
    '孤独': '悲伤',
}

LLM_MOOD_SYSTEM_PROMPT = """你是心语花园的中文情绪分析器。只分析用户当前这句话的情绪，不要安慰，不要聊天。
必须只返回一个 JSON 对象，不要 Markdown，不要代码块，不要额外说明。
JSON 字段：
- mood_label: 只能是 开心、平静、中性、焦虑、悲伤 之一
- mood_score: 0 到 100 的数字；明显开心/成就/兴奋 >=75；平静 60-74；中性 40-59；焦虑 25-39；悲伤 0-24
- keywords: 命中的关键词数组，最多 5 个中文短词
- trend: 只能是 上升、平稳、下降 之一
- reason: 20 字以内的判断依据
注意：像“太好了”“太开心了”“完成了很多项目”属于明显积极/成就表达，应判为 开心。"""


class LLMService:

    _MAX_CACHE = 10

    def __init__(self):
        self._provider_cache: OrderedDict[str, LLMInterface] = OrderedDict()

    def is_llm_configured(self, user_llm_config: Optional[Dict] = None) -> bool:
        config = self._merge_config(user_llm_config)
        configured = (
            bool(config.get("enabled", False))
            and bool(config.get("api_key"))
            and bool(config.get("base_url"))
        )
        logger.info(
            "LLM configured=%s enabled=%s api_key_set=%s base_url_set=%s model=%s",
            configured,
            bool(config.get("enabled", False)),
            bool(config.get("api_key")),
            bool(config.get("base_url")),
            config.get("model") or "-"
        )
        return configured

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
            if len(self._provider_cache) >= self._MAX_CACHE:
                self._provider_cache.popitem(last=False)  # LRU 淘汰
            self._provider_cache[cache_key] = OpenAICompatibleProvider(
                model_name=config["model"],
                api_key=config["api_key"],
                base_url=config["base_url"]
            )
            logger.info(
                "LLM provider created model=%s base_url_set=%s cache_size=%s",
                config.get("model") or "-",
                bool(config.get("base_url")),
                len(self._provider_cache)
            )
        else:
            self._provider_cache.move_to_end(cache_key)
            logger.debug(
                "LLM provider cache hit model=%s cache_size=%s",
                config.get("model") or "-",
                len(self._provider_cache)
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
        logger.info(
            "LLM chat start messages=%s temperature=%s max_tokens=%s",
            len(messages),
            temp,
            max_tokens
        )
        try:
            response = provider.chat(
                messages,
                temperature=temp,
                max_tokens=max_tokens,
                stream=False
            )
            if response and response.content:
                response.content = sanitize_output(response.content)
            content_len = len(response.content or "")
            logger.info(
                "LLM chat success chars=%s finish_reason=%s usage=%s",
                content_len,
                response.finish_reason,
                response.usage or {}
            )
            return True, response, None
        except Exception as e:
            error_msg = f"LLM call failed: {e}"
            logger.exception("LLM chat failed error=%s", e)
            return False, None, error_msg

    def analyze_mood(
        self,
        user_message: str,
        user_config: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Use the configured LLM to analyze the user's current mood.

        Returns (success, mood_result, error). The caller should fall back to
        the rule analyzer whenever success is False.
        """
        if not self.is_llm_configured(user_config):
            logger.info("LLM mood analysis skipped reason=not_configured")
            return False, None, "not_configured"

        text = (user_message or "").strip()
        if not text:
            logger.info("LLM mood analysis skipped reason=empty_text")
            return False, None, "empty_text"

        messages = [
            Message(role="system", content=LLM_MOOD_SYSTEM_PROMPT),
            Message(
                role="user",
                content=json.dumps({"text": text}, ensure_ascii=False)
            ),
        ]
        logger.info("LLM mood analysis start chars=%s", len(text))
        success, response, error = self.chat(
            messages,
            user_config=user_config,
            temperature=0.1,
            max_tokens=220,
        )
        if not success or not response or not response.content:
            logger.warning("LLM mood analysis failed error=%s", error or "empty_response")
            return False, None, error or "empty_response"

        try:
            result = self._parse_mood_analysis(response.content)
        except ValueError as exc:
            logger.warning(
                "LLM mood analysis invalid_json error=%s raw_chars=%s",
                exc,
                len(response.content or ""),
            )
            return False, None, str(exc)

        logger.info(
            "LLM mood analysis success mood=%s score=%s trend=%s keywords=%s",
            result['mood_label'],
            result['mood_score'],
            result.get('trend'),
            len(result.get('keywords', [])),
        )
        return True, result, None

    def _parse_mood_analysis(self, content: str) -> Dict:
        raw = (content or "").strip()
        if not raw:
            raise ValueError("empty LLM mood response")

        # Accept accidental Markdown fences, but only parse the JSON object.
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        start = raw.find('{')
        end = raw.rfind('}')
        if start == -1 or end == -1 or end <= start:
            raise ValueError("no JSON object found")
        raw = raw[start:end + 1]

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("LLM mood response must be an object")

        mood_label = self._normalize_mood_label(data.get('mood_label'))
        mood_score = self._normalize_mood_score(data.get('mood_score'), mood_label)
        keywords = self._normalize_keywords(data.get('keywords'))
        trend = str(data.get('trend') or '平稳').strip()
        if trend not in TREND_LABELS:
            trend = '平稳'

        reason = str(data.get('reason') or '').strip()
        return {
            'mood_score': mood_score,
            'mood_label': mood_label,
            'keywords': keywords,
            'trend': trend,
            'positive_count': 0,
            'negative_count': 0,
            'analysis_source': 'llm',
            'reason': reason[:40],
        }

    def _normalize_mood_label(self, value) -> str:
        label = str(value or '').strip()
        if label in MOOD_LABELS:
            return label
        if label in MOOD_LABEL_ALIASES:
            return MOOD_LABEL_ALIASES[label]
        for alias, normalized in MOOD_LABEL_ALIASES.items():
            if alias and alias in label:
                return normalized
        raise ValueError(f"unsupported mood_label: {label or '-'}")

    def _normalize_mood_score(self, value, mood_label: str) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            score = MOOD_SCORE_RANGES[mood_label][2]
        score = max(0.0, min(100.0, score))
        min_score, max_score, default_score = MOOD_SCORE_RANGES[mood_label]
        if score < min_score or score > max_score:
            score = default_score
        return round(score, 1)

    def _normalize_keywords(self, value) -> List[str]:
        if isinstance(value, str):
            parts = re.split(r"[，,、；;\s]+", value)
        elif isinstance(value, list):
            parts = value
        else:
            parts = []

        keywords = []
        for item in parts:
            word = str(item or '').strip()
            if word and word not in keywords:
                keywords.append(word[:12])
            if len(keywords) >= 5:
                break
        return keywords

    def chat_with_fallback(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        mood_context: Optional[MoodContext] = None,
        user_config: Optional[Dict] = None,
        user_preferences: Optional[Dict] = None
    ) -> Tuple[bool, str, str]:
        if not self.is_llm_configured(user_config):
            logger.info("LLM fallback skipped reason=not_configured")
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
            logger.info("LLM fallback result=llm chars=%s", len(response.content or ""))
            return True, response.content, "llm"
        else:
            logger.warning("LLM failed, falling back to rule engine: %s", error)
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
            logger.info("LLM stream skipped reason=not_configured")
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
        chunk_count = 0
        char_count = 0
        logger.info(
            "LLM stream start messages=%s temperature=%s max_tokens=%s",
            len(messages),
            temp,
            1024
        )
        try:
            for chunk in provider.chat_stream(messages, temperature=temp, max_tokens=1024):
                if chunk:
                    chunk = sanitize_output(chunk)
                chunk_count += 1
                char_count += len(chunk or "")
                yield chunk
            logger.info(
                "LLM stream success chunks=%s chars=%s",
                chunk_count,
                char_count
            )
        except Exception as e:
            logger.exception("LLM stream failed error=%s", e)
            return

    def test_connection(self, user_config: Optional[Dict] = None) -> Dict:
        config = self._merge_config(user_config)
        logger.info(
            "LLM test_connection start api_key_set=%s base_url_set=%s model=%s",
            bool(config.get("api_key")),
            bool(config.get("base_url")),
            config.get("model") or "-"
        )
        if not config.get("api_key") or not config.get("base_url"):
            logger.warning("LLM test_connection failed reason=missing_config")
            return {
                "success": False,
                "message": "API Key and Base URL are required"
            }
        provider = OpenAICompatibleProvider(
            model_name=config["model"],
            api_key=config["api_key"],
            base_url=config["base_url"]
        )
        result = provider.test_connection()
        logger.info(
            "LLM test_connection result success=%s message=%s",
            result.get("success"),
            result.get("message")
        )
        return result

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
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("LLM config parse failed error=%s", e)
        return dict(DEFAULT_LLM_CONFIG)


def serialize_llm_config(config: Dict) -> str:
    return json.dumps(config, ensure_ascii=False)

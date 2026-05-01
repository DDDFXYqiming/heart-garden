"""
心语花园 - 服务模块
包含情绪分析、AI 陪伴、大模型服务等
"""

from .mood_analyzer import MoodAnalyzer
from .ai_companion import AICompanion
from .llm_service import LLMService, parse_llm_config, serialize_llm_config
from .openai_compatible import OpenAICompatibleProvider
from .prompt_engine import PromptBuilder, UserPreferences, MoodContext

__all__ = [
    'MoodAnalyzer',
    'AICompanion',
    'LLMService',
    'OpenAICompatibleProvider',
    'PromptBuilder',
    'UserPreferences',
    'MoodContext',
    'parse_llm_config',
    'serialize_llm_config'
]

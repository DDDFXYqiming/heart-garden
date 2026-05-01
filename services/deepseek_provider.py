"""
DeepSeek 服务商兼容层
已迁移至 openai_compatible.py，此文件仅保留向后兼容
"""

from .openai_compatible import OpenAICompatibleProvider

DeepSeekProvider = OpenAICompatibleProvider

__all__ = ['DeepSeekProvider']

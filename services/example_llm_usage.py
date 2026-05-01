"""
大模型混合模式 - 使用示例

本文件演示如何在项目中使用新的混合模式架构。
在实际使用中，主要通过 /api/chat 端点自动调用，无需手动处理。
"""

from services import LLMService, OpenAICompatibleProvider, PromptBuilder, MoodContext
from services.llm_service import parse_llm_config, serialize_llm_config


def example_hybrid_chat():
    llm_service = LLMService()
    user_llm_config = {
        "enabled": True,
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "sk-your-key-here",
        "model": "deepseek-chat",
        "temperature": 0.7
    }
    user_message = "我今天工作很顺利，完成了所有任务！"
    mood_context = MoodContext(mood_label="开心", mood_score=85.0)

    success, response, source = llm_service.chat_with_fallback(
        user_message=user_message,
        mood_context=mood_context,
        user_config=user_llm_config
    )

    if success:
        print(f"LLM response ({source}): {response}")
    else:
        print("LLM failed, use rule engine fallback")


def example_config_persistence():
    config = {
        "enabled": True,
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "sk-xxxxx",
        "model": "deepseek-chat",
        "temperature": 0.7
    }
    json_str = serialize_llm_config(config)
    restored = parse_llm_config(json_str)
    print(f"Serialized: {json_str}")
    print(f"Restored: {restored}")


def example_user_specific_provider():
    provider = OpenAICompatibleProvider(
        model_name="deepseek-chat",
        api_key="sk-your-key",
        base_url="https://api.deepseek.com/v1"
    )
    print(f"Provider info: {provider.get_model_info()}")


if __name__ == "__main__":
    example_config_persistence()
    print("\nAll examples completed.")

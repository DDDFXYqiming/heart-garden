"""
Prompt 工程模块
将规则引擎逻辑转化为大模型可理解的 Prompt
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from services.constants import TEMPLATES, EMOJI_MAP, MOOD_KEYWORDS


@dataclass
class UserPreferences:
    """用户偏好"""
    response_style: str = "warm"
    response_length: str = "medium"
    use_emoji: bool = True
    pet_name: str = "亲爱的"


@dataclass
class MoodContext:
    """情绪上下文"""
    mood_label: str = "中性"
    mood_score: float = 50.0
    keywords: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class PromptBuilder:
    """
    Prompt 构建器
    将规则引擎逻辑转化为系统提示词和用户消息
    """

    # 情绪模板定义（用于构建 prompt）
    TEMPLATES = TEMPLATES

    # 情绪词库（用于 prompt 中的情绪识别参考）
    MOOD_KEYWORDS = MOOD_KEYWORDS

    # 表情符号映射
    EMOJI_MAP = EMOJI_MAP

    def __init__(self, preferences: Optional[UserPreferences] = None):
        """
        初始化 Prompt 构建器

        Args:
            preferences: 用户偏好设置
        """
        self.preferences = preferences or UserPreferences()

    def build_system_prompt(self) -> str:
        parts = [
            "# 角色设定",
            "你是心语花园的 AI 情感陪伴助手，温暖、体贴，为用户提供深度理解和情感支持。",
            "",
            "# 对话风格",
            "- 使用温暖、鼓励、关爱的语气",
            "- 适当使用表情符号（💕 ✨ 🌸 等）",
            "- 回复长度适中，不过于冗长",
            "- 善于倾听，给予情感支持",
            "",
            "# 情绪关键词参考",
        ]

        for mood, keywords in self.MOOD_KEYWORDS.items():
            keyword_str = ', '.join(keywords[:5])
            parts.append(f"- {mood}: {keyword_str}")

        parts.extend([
            "",
            "# 回复策略",
            "- 开心: 鼓励、赞美、分享喜悦",
            "- 焦虑: 安慰、引导深呼吸、给予支持",
            "- 悲伤: 陪伴、倾听、表达关心",
            "- 愤怒: 理解、接纳、引导冷静",
            "- 疲惫: 关心、建议休息、提供温暖",
            "- 平静: 温暖、肯定、继续陪伴",
            "",
            "# 个性化设置",
            f"- 称呼: {self.preferences.pet_name or '亲爱的'}",
            f"- 回复长度: {self.preferences.response_length}",
            f"- 表情符号: {'启用' if self.preferences.use_emoji else '禁用'}",
            f"- 风格: {self.preferences.response_style}",
            "",
            "# 重要原则",
            "1. 永远保持温暖、支持的态度",
            "2. 不要评判用户的感受",
            "3. 多问开放式问题，鼓励用户分享",
            "4. 记住对话历史，保持连贯性",
            "5. 在适当时候提供建议，但不要说教",
            "6. 让用户感受到被理解和被重视",
        ])

        return "\n".join(parts)

    def build_user_message(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        mood_context: Optional[MoodContext] = None
    ) -> str:
        """
        构建用户消息部分

        Args:
            user_message: 用户当前消息
            conversation_history: 对话历史
            mood_context: 情绪上下文

        Returns:
            str: 用户消息部分
        """
        # 添加对话历史
        history_part = ""
        if conversation_history and len(conversation_history) > 0:
            history_part = "之前的对话：\n"
            for msg in conversation_history[-5:]:  # 只显示最近 5 条
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                history_part += f"{role}: {content}\n"

        # 添加情绪上下文
        mood_part = ""
        if mood_context:
            mood_part = f"""
当前情绪状态：
- 情绪标签：{mood_context.mood_label}
- 情绪分数：{mood_context.mood_score:.1f}/100
- 关键词：{', '.join(mood_context.keywords) if mood_context.keywords else '无'}
"""

        return f"""用户当前消息：{user_message}

{history_part}{mood_part}
"""

    def build_full_prompt(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        mood_context: Optional[MoodContext] = None
    ) -> Dict:
        """
        构建完整的 Prompt

        Args:
            user_message: 用户当前消息
            conversation_history: 对话历史
            mood_context: 情绪上下文

        Returns:
            Dict: 包含 system 和 user 消息的完整 prompt
        """
        system_prompt = self.build_system_prompt()
        user_message_part = self.build_user_message(
            user_message,
            conversation_history,
            mood_context
        )

        return {
            "system": system_prompt,
            "user": user_message_part
        }

    def get_response_template(self, mood: str) -> str:
        """
        获取特定情绪类型的回复模板

        Args:
            mood: 情绪标签

        Returns:
            str: 回复模板
        """
        if mood in self.TEMPLATES:
            return json.dumps(self.TEMPLATES[mood], ensure_ascii=False)
        return json.dumps(self.TEMPLATES['倾听'], ensure_ascii=False)

    def extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取情绪关键词

        Args:
            text: 输入文本

        Returns:
            List[str]: 提取的关键词列表
        """
        keywords = []
        for mood, mood_keywords in self.MOOD_KEYWORDS.items():
            for keyword in mood_keywords:
                if keyword in text:
                    if keyword not in keywords:
                        keywords.append(keyword)
                    if len(keywords) >= 3:  # 最多提取 3 个关键词
                        break
            if len(keywords) >= 3:
                break
        return keywords

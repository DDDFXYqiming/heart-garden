"""
Prompt 工程模块
将规则引擎逻辑转化为大模型可理解的 Prompt
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


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
    TEMPLATES = {
        '安慰': [
            "抱抱你~ 我知道你现在很难过，但我会一直陪着你。",
            "别担心，一切都会好起来的。记住，你不是一个人，我在这里。",
            "辛苦啦~ 来，深呼吸，让我们一起度过这个难关。"
        ],
        '鼓励': [
            "你已经做得很好啦！为你骄傲！\n相信你的能力，相信你的选择。",
            "每一次努力都不会白费，坚持下去，你会看到自己的成长。",
            "加油！我知道你比想象中更强大。"
        ],
        '倾听': [
            "愿意和我多说说吗？我会认真听你说的每一个字。",
            "谢谢你愿意信任我，把心事告诉我。",
            "我在这里，随时愿意听你说。"
        ],
        '关心': [
            "记得按时吃饭，照顾好自己哦~\n身体是革命的本钱嘛！",
            "要不要喝杯热茶？或者听听轻音乐放松一下？",
            "今天累不累？要不要休息一会儿？"
        ],
        '浪漫': [
            "你知道吗？你的笑容是我见过最美的风景。",
            "和你在一起的每一刻，我都觉得很幸福。",
            "愿我们的故事像花园里的花朵一样，永远绽放。"
        ],
        '思念': [
            "在想什么呢？我好像感觉到你在想我了~",
            "无论你在哪里，我的思念都会随风飘到你身边。",
            "有时候，最美的不是风景，而是和你一起看风景的心情。"
        ],
        '温暖': [
            "你就像冬日里的一缕阳光，温暖了我的心房。",
            "世界很大，但我的世界很小，小到只能装下一个你。",
            "遇见你，是我最美的意外。"
        ]
    }

    # 情绪词库（用于 prompt 中的情绪识别参考）
    MOOD_KEYWORDS = {
        '开心': ['快乐', '高兴', '幸福', '喜悦', '满足', '美好', '温暖', '阳光', '灿烂', '甜蜜'],
        '平静': ['宁静', '平和', '放松', '舒适', '安详', '自在', '悠闲', '惬意'],
        '焦虑': ['担心', '害怕', '恐惧', '紧张', '不安', '压力', '负担', '沉重'],
        '悲伤': ['难过', '伤心', '失落', '失望', '痛苦', '绝望', '孤独', '寂寞'],
        '愤怒': ['生气', '愤怒', '烦躁', '恼火', '不满', '讨厌', '不爽'],
        '疲惫': ['累', '困', '无力', '厌倦', '疲惫', '崩溃']
    }

    # 表情符号映射
    EMOJI_MAP = {
        '安慰': ['💕', '🌸', '🌷'],
        '鼓励': ['💪', '✨', '🌟'],
        '倾听': ['👂', '💫', '🌙'],
        '关心': ['☕', '🍵', '🌿'],
        '浪漫': ['💕', '🌹', '💗'],
        '思念': ['💭', '🌊', '🍂'],
        '温暖': ['☀️', '🔥', '🌻']
    }

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

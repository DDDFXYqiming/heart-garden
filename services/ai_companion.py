"""
AI 陪伴服务
生成温暖的回复，提供情感支持
"""

import json
import random
from typing import Dict, List, Optional

from services.constants import TEMPLATES, EMOJI_MAP

DEFAULT_PREFERENCES = {
    'response_style': 'warm',
    'response_length': 'medium',
    'use_emoji': True,
    'pet_name': '亲爱的'
}

STYLE_TEMPLATE_MAP = {
    'warm': ['鼓励', '关心', '温暖', '倾听'],
    'gentle': ['安慰', '倾听', '关心'],
    'poetic': ['浪漫', '思念', '温暖'],
    'simple': ['倾听', '鼓励']
}

class AICompanion:
    """AI 陪伴者"""

    TEMPLATES = TEMPLATES
    EMOJI_MAP = EMOJI_MAP
    PET_NAMES = ['亲爱的', '宝', '朋友', '']

    def __init__(self):
        self.user_profile = {}
        self.conversation_memory = {}

    def analyze_diary(self, content: str, mood_result: Dict, preferences: Optional[Dict] = None) -> str:
        mood_label = mood_result.get('mood_label', '中性')
        score = mood_result.get('mood_score', 50)
        prefs = {**DEFAULT_PREFERENCES, **(preferences or {})}

        if mood_label == '开心':
            return self._generate_happy_response(content, score, prefs)
        elif mood_label == '焦虑':
            return self._generate_anxiety_response(content, score, prefs)
        elif mood_label == '悲伤':
            return self._generate_sad_response(content, score, prefs)
        else:
            return self._generate_neutral_response(content, score, prefs)

    def _pick_template(self, mood_label: str, prefs: Dict) -> str:
        style = prefs.get('response_style', 'warm')
        allowed = STYLE_TEMPLATE_MAP.get(style, STYLE_TEMPLATE_MAP['warm'])
        return random.choice(self.TEMPLATES.get(mood_label, self.TEMPLATES['倾听']))

    def _apply_emoji(self, text: str, template_type: str, prefs: Dict) -> str:
        if not prefs.get('use_emoji', True):
            return text
        emojis = self.EMOJI_MAP.get(template_type, ['✨'])
        emoji = random.choice(emojis)
        return f"{text} {emoji}"

    def _apply_pet_name(self, text: str, prefs: Dict) -> str:
        name = prefs.get('pet_name', '')
        if not name or name == '无' or name == '':
            return text
        return text.replace('亲爱的', name) if '亲爱的' in text else text

    def _apply_length(self, base: str, personal_note: str, prefs: Dict) -> str:
        length = prefs.get('response_length', 'medium')
        if length == 'short':
            return base
        elif length == 'long':
            extra = random.choice([
                "我会一直在这里，无论何时。",
                "记住，你永远值得被温柔以待。",
                "新的一天，新的希望，我们一起加油。"
            ])
            return f"{base}\n\n{personal_note}\n\n{extra}"
        else:
            return f"{base}\n\n{personal_note}"

    def _generate_happy_response(self, content: str, score: float, prefs: Dict) -> str:
        template = self._pick_template('鼓励', prefs)
        note = f"看到你这么开心，我也跟着开心起来啦！你的笑容就像阳光一样温暖。"
        result = self._apply_length(template, note, prefs)
        result = self._apply_emoji(result, '鼓励', prefs)
        return self._apply_pet_name(result, prefs)

    def _generate_anxiety_response(self, content: str, score: float, prefs: Dict) -> str:
        template = self._pick_template('安慰', prefs)
        pname = prefs.get('pet_name', '亲爱的') or ''
        note = f"{pname}，别担心~ 焦虑的时候，试着深呼吸，慢慢来。我会一直陪着你。" if pname else f"别担心~ 焦虑的时候，试着深呼吸，慢慢来。我会一直陪着你。"
        result = self._apply_length(template, note, prefs)
        result = self._apply_emoji(result, '安慰', prefs)
        return self._apply_pet_name(result, prefs)

    def _generate_sad_response(self, content: str, score: float, prefs: Dict) -> str:
        template = self._pick_template('安慰', prefs)
        note = f"我知道你现在很难过... 但请记住，你的感受很重要，我会一直在这里陪着你。"
        result = self._apply_length(template, note, prefs)
        result = self._apply_emoji(result, '安慰', prefs)
        return self._apply_pet_name(result, prefs)

    def _generate_neutral_response(self, content: str, score: float, prefs: Dict) -> str:
        template = self._pick_template('倾听', prefs)
        note = f"谢谢你愿意和我分享。你的每句话都值得被认真对待。"
        result = self._apply_length(template, note, prefs)
        result = self._apply_emoji(result, '倾听', prefs)
        return self._apply_pet_name(result, prefs)

    def generate_response(
        self,
        user_message: str,
        history: Optional[List[Dict]] = None,
        mood: str = 'neutral',
        preferences: Optional[Dict] = None
    ) -> str:
        history = history or []
        prefs = {**DEFAULT_PREFERENCES, **(preferences or {})}
        turn_count = len([h for h in history if h['role'] == 'user'])

        response_type = self._determine_response_type(mood, user_message)
        base_response = self._pick_template(response_type, prefs)

        context_note = self._build_context_note(history, user_message, turn_count)
        if context_note:
            result = f"{base_response}\n\n{context_note}"
        else:
            personalized = self._personalize_response(base_response, user_message, mood)
            result = personalized

        result = self._apply_emoji(result, response_type, prefs)
        return self._apply_pet_name(result, prefs)

    def _determine_response_type(self, mood: str, message: str) -> str:
        mood_map = {
            '开心': '鼓励',
            '平静': '温暖',
            '期待': '鼓励',
            '爱': '浪漫',
            '感激': '温暖',
            '焦虑': '安慰',
            '悲伤': '安慰',
            '愤怒': '安慰',
            '疲惫': '关心'
        }

        if mood in mood_map:
            return mood_map[mood]

        question_words = ['吗', '什么', '怎么', '为什么', '如何', '是否', '能不能']
        if any(w in message for w in question_words):
            return '倾听'

        gratitude_words = ['谢谢', '感谢', '感恩']
        if any(w in message for w in gratitude_words):
            return '温暖'

        longing_words = ['想', '思念', '怀念', '牵挂']
        if any(w in message for w in longing_words):
            return '思念'

        return '倾听'

    def _build_context_note(
        self,
        history: List[Dict],
        current_message: str,
        turn_count: int
    ) -> Optional[str]:
        if turn_count <= 1:
            return None

        user_messages = [h['content'] for h in history if h['role'] == 'user']

        if len(user_messages) >= 2:
            prev_topic = self._extract_topic(user_messages[-2])
            current_topic = self._extract_topic(current_message)

            if prev_topic and current_topic and prev_topic == current_topic:
                return f"你刚才提到的「{prev_topic}」，我想再和你多聊聊这个。能告诉我更多你的想法吗？"

            if prev_topic:
                return f"从刚才的「{prev_topic}」到现在说的「{current_topic}」，感觉你心里有很多话想说呢～我都在听哦。"

            return "我感觉到你还在继续分享你的心情，真好～我会一直在这里陪着你。"

        return None

    def _extract_topic(self, text: str) -> Optional[str]:
        topic_markers = ['关于', '说到', '提到', '今天', '最近', '昨天', '明天']
        for marker in topic_markers:
            if marker in text:
                idx = text.find(marker)
                return text[idx:idx + 15]

        if len(text) >= 4:
            keywords = self._extract_keywords(text)
            if keywords:
                return keywords[0]

        return None

    def _personalize_response(self, template: str, message: str, mood: str) -> str:
        keywords = self._extract_keywords(message)

        if keywords:
            if mood in ('焦虑', '悲伤', '疲惫'):
                return f"{template}\n\n我注意到你提到了「{keywords[0]}」，想和我多说一些吗？我在这里听着呢。"
            elif mood in ('开心', '爱', '感激'):
                return f"{template}\n\n说到「{keywords[0]}」，我能感受到你此刻的心情，真为你开心！"
            else:
                return f"{template}\n\n你提到了「{keywords[0]}」，感觉这对你很重要呢。可以和我多分享一些吗？"

        return template

    def _extract_keywords(self, text: str) -> List[str]:
        keywords = []

        positive_words = ['开心', '快乐', '幸福', '美好', '温暖', '爱', '喜欢', '感谢']
        negative_words = ['难过', '累', '压力', '担心', '害怕', '孤独', '寂寞', '焦虑']

        for word in positive_words:
            if word in text:
                keywords.append(word)

        for word in negative_words:
            if word in text:
                keywords.append(word)

        return keywords[:3]

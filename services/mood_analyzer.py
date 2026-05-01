"""
情绪分析服务
分析用户文本的情绪状态、关键词、趋势等
"""

import re
from typing import Dict, List, Optional

class MoodAnalyzer:
    """情绪分析器"""

    POSITIVE_WORDS = {
        '开心': ['快乐', '高兴', '幸福', '喜悦', '满足', '美好', '温暖', '阳光', '灿烂', '甜蜜'],
        '平静': ['宁静', '平和', '放松', '舒适', '安详', '自在', '悠闲', '惬意'],
        '期待': ['希望', '期待', '向往', '憧憬', '梦想', '未来', '可能', '机会'],
        '爱': ['爱', '喜欢', '珍惜', '在乎', '关心', '思念', '牵挂', '温柔'],
        '感激': ['感谢', '谢谢', '感恩', '感动', '温暖', '幸福', '幸运']
    }

    NEGATIVE_WORDS = {
        '焦虑': ['担心', '害怕', '恐惧', '紧张', '不安', '压力', '负担', '沉重'],
        '悲伤': ['难过', '伤心', '失落', '失望', '痛苦', '绝望', '孤独', '寂寞'],
        '愤怒': ['生气', '愤怒', '烦躁', '恼火', '不满', '讨厌', '不爽'],
        '疲惫': ['累', '困', '无力', '厌倦', '疲惫', '崩溃']
    }

    MOOD_SCORE_MAP = {
        '开心': (75, 100),
        '平静': (60, 75),
        '中性': (40, 60),
        '焦虑': (25, 40),
        '悲伤': (0, 25)
    }

    ALL_MOODS = ['开心', '平静', '中性', '焦虑', '悲伤']

    def __init__(self):
        self.positive_count = 0
        self.negative_count = 0

    def analyze(self, text: str, custom_words: Optional[List[Dict]] = None) -> Dict:
        custom_words = custom_words or []

        self.positive_count = 0
        self.negative_count = 0
        active_positive = {}
        active_negative = {}
        keywords = []

        # 单遍扫描: 内置词 + 自定义词一次性匹配
        for mood, words in self.POSITIVE_WORDS.items():
            active_positive[mood] = list(words)
            for word in words:
                if word in text:
                    self.positive_count += 1
                    if word not in keywords:
                        keywords.append(word)

        for mood, words in self.NEGATIVE_WORDS.items():
            active_negative[mood] = list(words)
            for word in words:
                if word in text:
                    self.negative_count += 1
                    if word not in keywords:
                        keywords.append(word)

        for cw in custom_words:
            word = cw['word']
            word_type = cw['type']
            if word in text:
                if word_type == 'positive':
                    self.positive_count += 1
                    if '自定义' not in active_positive:
                        active_positive['自定义'] = []
                    active_positive['自定义'].append(word)
                else:
                    self.negative_count += 1
                    if '自定义' not in active_negative:
                        active_negative['自定义'] = []
                    active_negative['自定义'].append(word)
                if word not in keywords:
                    keywords.append(word)

        mood_score = self._calculate_mood_score()
        mood_label = self._determine_mood_label(mood_score)
        trend = self._determine_trend(text, custom_words)

        return {
            'mood_score': mood_score,
            'mood_label': mood_label,
            'keywords': keywords[:5],
            'trend': trend,
            'positive_count': self.positive_count,
            'negative_count': self.negative_count
        }

    def _calculate_mood_score(self) -> float:
        total = self.positive_count + self.negative_count

        if total == 0:
            return 50.0

        positive_ratio = self.positive_count / total
        score = positive_ratio * 100
        score = max(20, min(80, score))

        return round(score, 1)

    def _determine_mood_label(self, score: float) -> str:
        if score >= 75:
            return '开心'
        elif score >= 60:
            return '平静'
        elif score >= 40:
            return '中性'
        elif score >= 25:
            return '焦虑'
        else:
            return '悲伤'

    def _determine_trend(self, text: str, custom_words: Optional[List[Dict]] = None) -> str:
        custom_words = custom_words or []
        positive_words = 0
        negative_words = 0

        for words in self.POSITIVE_WORDS.values():
            for w in words:
                if w in text:
                    positive_words += 1

        for words in self.NEGATIVE_WORDS.values():
            for w in words:
                if w in text:
                    negative_words += 1

        for cw in custom_words:
            if cw['word'] in text:
                if cw['type'] == 'positive':
                    positive_words += 1
                else:
                    negative_words += 1

        if positive_words > negative_words + 2:
            return '上升'
        elif negative_words > positive_words + 2:
            return '下降'
        else:
            return '平稳'

    def add_custom_word(self, word: str, word_type: str, category: str = '自定义'):
        if word_type == 'positive':
            if '自定义' not in self.POSITIVE_WORDS:
                self.POSITIVE_WORDS['自定义'] = []
            if word not in self.POSITIVE_WORDS['自定义']:
                self.POSITIVE_WORDS['自定义'].append(word)
        else:
            if '自定义' not in self.NEGATIVE_WORDS:
                self.NEGATIVE_WORDS['自定义'] = []
            if word not in self.NEGATIVE_WORDS['自定义']:
                self.NEGATIVE_WORDS['自定义'].append(word)

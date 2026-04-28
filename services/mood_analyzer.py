"""
情绪分析服务
分析用户文本的情绪状态、关键词、趋势等
"""

import re
from typing import Dict, List

class MoodAnalyzer:
    """情绪分析器"""
    
    # 情绪关键词库
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
        '愤怒': ['生气', '愤怒', '烦躁', '恼火', '不满', '讨厌', '讨厌', '不爽'],
        '疲惫': ['累', '困', ' exhaustion', '无力', '厌倦', '疲惫', '崩溃']
    }
    
    def __init__(self):
        self.positive_count = 0
        self.negative_count = 0
    
    def analyze(self, text: str) -> Dict:
        """
        分析文本情绪
        
        Args:
            text: 用户输入的文本
            
        Returns:
            情绪分析报告
        """
        # 预处理
        text = text.lower()
        
        # 统计情绪词
        self.positive_count = 0
        self.negative_count = 0
        
        for mood, words in self.POSITIVE_WORDS.items():
            for word in words:
                if word in text:
                    self.positive_count += 1
        
        for mood, words in self.NEGATIVE_WORDS.items():
            for word in words:
                if word in text:
                    self.negative_count += 1
        
        # 计算情绪分数
        mood_score = self._calculate_mood_score()
        
        # 确定情绪标签
        mood_label = self._determine_mood_label(mood_score)
        
        # 提取关键词
        keywords = self._extract_keywords(text)
        
        # 判断趋势
        trend = self._determine_trend(text)
        
        return {
            'mood_score': mood_score,
            'mood_label': mood_label,
            'keywords': keywords,
            'trend': trend,
            'positive_count': self.positive_count,
            'negative_count': self.negative_count
        }
    
    def _calculate_mood_score(self) -> float:
        """计算情绪分数 (0-100)"""
        total = self.positive_count + self.negative_count
        
        if total == 0:
            return 50.0  # 中性
        
        positive_ratio = self.positive_count / total
        
        # 映射到 0-100
        score = positive_ratio * 100
        
        # 平滑处理
        score = max(20, min(80, score))
        
        return round(score, 1)
    
    def _determine_mood_label(self, score: float) -> str:
        """根据分数确定情绪标签"""
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
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取情绪关键词"""
        keywords = []
        
        # 查找情绪词
        for mood, words in self.POSITIVE_WORDS.items():
            for word in words:
                if word in text and word not in keywords:
                    keywords.append(word)
        
        for mood, words in self.NEGATIVE_WORDS.items():
            for word in words:
                if word in text and word not in keywords:
                    keywords.append(word)
        
        # 限制数量
        return keywords[:5]
    
    def _determine_trend(self, text: str) -> str:
        """判断情绪趋势"""
        positive_words = sum(1 for words in self.POSITIVE_WORDS.values() 
                           for w in words if w in text)
        negative_words = sum(1 for words in self.NEGATIVE_WORDS.values() 
                           for w in words if w in text)
        
        if positive_words > negative_words + 2:
            return '上升'
        elif negative_words > positive_words + 2:
            return '下降'
        else:
            return '平稳'

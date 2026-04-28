"""
AI 陪伴服务
生成温暖的回复，提供情感支持
"""

import json
from typing import Dict

class AICompanion:
    """AI 陪伴者"""
    
    # 回复模板库
    TEMPLATES = {
        '安慰': [
            "亲爱的，抱抱你~ (发送拥抱动画)\n我知道你现在很难过，但我会一直陪着你。",
            "别担心，一切都会好起来的。记住，你不是一个人，我在这里。",
            "辛苦啦~ 来，深呼吸，让我们一起度过这个难关。"
        ],
        '鼓励': [
            "你已经做得很好啦！为你骄傲！💪\n相信你的能力，相信你的选择。",
            "每一次努力都不会白费，坚持下去，你会看到自己的成长。",
            "加油！我知道你比想象中更强大。"
        ],
        '倾听': [
            "愿意和我多说说吗？我会认真听你说的每一个字。",
            "谢谢你愿意信任我，把心事告诉我。",
            "我在这里，随时愿意听你说。"
        ],
        '关心': [
            "记得按时吃饭，照顾好自己哦~\n身体是革命的本钱嘛！💕",
            "要不要喝杯热茶？或者听听轻音乐放松一下？",
            "今天累不累？要不要休息一会儿？"
        ],
        '浪漫': [
            "你知道吗？你的笑容是我见过最美的风景。",
            "和你在一起的每一刻，我都觉得很幸福。",
            "愿我们的故事像花园里的花朵一样，永远绽放。"
        ]
    }
    
    def __init__(self):
        self.user_profile = {}
    
    def analyze_diary(self, content: str, mood_result: Dict) -> str:
        """
        分析日记内容，生成 AI 评论
        
        Args:
            content: 日记内容
            mood_result: 情绪分析结果
            
        Returns:
            AI 分析评论
        """
        mood_label = mood_result.get('mood_label', '中性')
        score = mood_result.get('mood_score', 50)
        
        # 根据情绪生成回复
        if mood_label == '开心':
            return self._generate_happy_response(content, score)
        elif mood_label == '焦虑':
            return self._generate_anxiety_response(content, score)
        elif mood_label == '悲伤':
            return self._generate_sad_response(content, score)
        else:
            return self._generate_neutral_response(content, score)
    
    def _generate_happy_response(self, content: str, score: float) -> str:
        """生成开心情绪的回复"""
        templates = self.TEMPLATES['鼓励']
        template = templates[0]
        
        # 个性化
        personal_note = f"看到你这么开心，我也跟着开心起来啦！✨\n你的笑容就像阳光一样温暖。"
        
        return f"{template}\n\n{personal_note}"
    
    def _generate_anxiety_response(self, content: str, score: float) -> str:
        """生成焦虑情绪的回复"""
        templates = self.TEMPLATES['安慰']
        template = templates[0]
        
        # 个性化
        personal_note = f"亲爱的，别担心~\n焦虑的时候，试着深呼吸，慢慢来。我会一直陪着你。"
        
        return f"{template}\n\n{personal_note}"
    
    def _generate_sad_response(self, content: str, score: float) -> str:
        """生成悲伤情绪的回复"""
        templates = self.TEMPLATES['安慰']
        template = templates[0]
        
        # 个性化
        personal_note = f"我知道你现在很难过...💔\n但请记住，你的感受很重要，我会一直在这里陪着你。"
        
        return f"{template}\n\n{personal_note}"
    
    def _generate_neutral_response(self, content: str, score: float) -> str:
        """生成中性情绪的回复"""
        templates = self.TEMPLATES['倾听']
        template = templates[0]
        
        # 个性化
        personal_note = f"谢谢你愿意和我分享。你的每句话都值得被认真对待。"
        
        return f"{template}\n\n{personal_note}"
    
    def generate_response(self, user_message: str, context: Dict = None, mood: str = 'neutral') -> str:
        """
        生成 AI 回复
        
        Args:
            user_message: 用户消息
            context: 上下文信息
            mood: 当前情绪状态
            
        Returns:
            AI 生成的回复
        """
        mood_label = mood if mood else 'neutral'
        
        # 根据情绪选择回复类型
        if mood_label == '开心':
            response_type = '鼓励'
        elif mood_label == '焦虑':
            response_type = '安慰'
        elif mood_label == '悲伤':
            response_type = '安慰'
        else:
            response_type = '倾听'
        
        # 选择模板
        templates = self.TEMPLATES[response_type]
        response = templates[0]
        
        # 个性化处理
        response = self._personalize_response(response, user_message)
        
        return response
    
    def _personalize_response(self, template: str, message: str) -> str:
        """个性化回复"""
        # 提取关键词
        keywords = self._extract_keywords(message)
        
        # 添加个性化元素
        if keywords:
            personal_note = f"说到 {keywords[0]}，我特别想告诉你..."
            return template + "\n\n" + personal_note
        
        return template
    
    def _extract_keywords(self, text: str) -> str:
        """提取关键词"""
        # 简单的情感关键词提取
        keywords = []
        
        positive_words = ['开心', '快乐', '幸福', '美好', '温暖']
        negative_words = ['难过', '累', '压力', '担心', '害怕']
        
        for word in positive_words:
            if word in text:
                keywords.append(word)
        
        for word in negative_words:
            if word in text:
                keywords.append(word)
        
        return keywords[0] if keywords else '心事'

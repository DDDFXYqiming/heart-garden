"""mood_analyzer 单元测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.mood_analyzer import MoodAnalyzer


class TestMoodAnalyzer:
    def setup_method(self):
        self.analyzer = MoodAnalyzer()

    def test_positive_text(self):
        result = self.analyzer.analyze("今天天气真好，我很开心快乐")
        assert result['mood_score'] > 50
        assert result['mood_label'] in ('开心', '平静')
        assert result['positive_count'] > 0

    def test_negative_text(self):
        result = self.analyzer.analyze("我很担心害怕，心情很低落难过")
        assert result['mood_score'] < 50
        assert result['mood_label'] in ('焦虑', '悲伤')
        assert result['negative_count'] > 0

    def test_neutral_text(self):
        result = self.analyzer.analyze("今天吃了个面包")
        assert result['mood_score'] == 50.0
        assert result['mood_label'] == '中性'

    def test_keywords_extraction(self):
        result = self.analyzer.analyze("我很开心，感到幸福和温暖")
        assert len(result['keywords']) > 0
        assert len(result['keywords']) <= 5

    def test_custom_words_positive(self):
        custom = [{'word': '太棒了', 'type': 'positive'}]
        result = self.analyzer.analyze("今天太棒了", custom)
        assert result['positive_count'] >= 1
        assert '太棒了' in result['keywords']

    def test_custom_words_negative(self):
        custom = [{'word': '倒霉', 'type': 'negative'}]
        result = self.analyzer.analyze("今天真倒霉", custom)
        assert result['negative_count'] >= 1
        assert '倒霉' in result['keywords']

    def test_empty_text(self):
        result = self.analyzer.analyze("")
        assert result['mood_score'] == 50.0
        assert result['keywords'] == []

    def test_mood_score_range(self):
        result = self.analyzer.analyze("开心快乐幸福美好")
        assert 20 <= result['mood_score'] <= 80

    def test_colloquial_positive_chat_text(self):
        result = self.analyzer.analyze("太好了太开心了，今天完成了很多项目！！！")
        assert result['mood_label'] == '开心'
        assert result['mood_score'] >= 75
        assert result['positive_count'] >= 2

    def test_good_weather_positive_text(self):
        result = self.analyzer.analyze("今天天气真好呀")
        assert result['mood_label'] == '开心'
        assert result['mood_score'] >= 75

    def test_trend_detection(self):
        result = self.analyzer.analyze("开心快乐幸福美好希望期待")
        assert result['trend'] in ('上升', '平稳')

    def test_add_custom_word(self):
        self.analyzer.add_custom_word('超赞', 'positive')
        assert '超赞' in self.analyzer.POSITIVE_WORDS.get('自定义', [])

    def test_keywords_limit(self):
        text = "快乐高兴幸福喜悦满足美好温暖阳光灿烂甜蜜"
        result = self.analyzer.analyze(text)
        assert len(result['keywords']) <= 5

"""prompt_engine 单元测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.prompt_engine import PromptBuilder, MoodContext, UserPreferences


class TestPromptBuilder:
    def setup_method(self):
        self.builder = PromptBuilder()

    def test_build_system_prompt(self):
        prompt = self.builder.build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert '心语花园' in prompt or '陪伴' in prompt

    def test_build_user_message(self):
        msg = self.builder.build_user_message("今天心情不错")
        assert isinstance(msg, str)
        assert '今天心情不错' in msg

    def test_build_with_mood_context(self):
        ctx = MoodContext(mood_label='开心', mood_score=75, keywords=['快乐'])
        msg = self.builder.build_user_message("我很开心", mood_context=ctx)
        assert isinstance(msg, str)

    def test_build_with_history(self):
        history = [
            {'role': 'user', 'content': '你好'},
            {'role': 'assistant', 'content': '你好呀~'}
        ]
        msg = self.builder.build_user_message("继续聊", conversation_history=history)
        assert isinstance(msg, str)

    def test_build_with_preferences(self):
        prefs = UserPreferences(
            response_style='warm',
            response_length='short',
            use_emoji=True,
            pet_name='宝贝'
        )
        builder = PromptBuilder(preferences=prefs)
        prompt = builder.build_system_prompt()
        assert isinstance(prompt, str)

    def test_build_with_all_params(self):
        ctx = MoodContext(mood_label='平静', mood_score=60, keywords=[])
        history = [{'role': 'user', 'content': 'hi'}]
        prefs = UserPreferences(
            response_style='warm',
            response_length='medium',
            use_emoji=False,
            pet_name='亲爱的'
        )
        builder = PromptBuilder(preferences=prefs)
        msg = builder.build_user_message(
            "今天过得怎么样",
            conversation_history=history,
            mood_context=ctx
        )
        assert isinstance(msg, str)
        assert '今天过得怎么样' in msg

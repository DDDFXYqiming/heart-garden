"""LLM 情绪判定解析测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.llm_service import LLMService


class TestLLMMoodAnalysis:
    def setup_method(self):
        self.service = LLMService()

    def test_parse_llm_mood_json(self):
        result = self.service._parse_mood_analysis('''
        {"mood_label":"开心","mood_score":93,"keywords":["开心","完成项目"],"trend":"上升","reason":"完成很多项目"}
        ''')

        assert result['mood_label'] == '开心'
        assert result['mood_score'] == 93.0
        assert result['keywords'] == ['开心', '完成项目']
        assert result['trend'] == '上升'
        assert result['analysis_source'] == 'llm'

    def test_parse_llm_mood_allows_markdown_fence_and_alias(self):
        result = self.service._parse_mood_analysis('''```json
        {"mood_label":"高兴","mood_score":66,"keywords":"高兴，顺利","trend":"明显上升"}
        ```''')

        assert result['mood_label'] == '开心'
        assert result['mood_score'] == 82.0
        assert result['keywords'] == ['高兴', '顺利']
        assert result['trend'] == '平稳'

    def test_parse_llm_mood_rejects_unsupported_label(self):
        try:
            self.service._parse_mood_analysis('{"mood_label":"复杂","mood_score":50}')
        except ValueError as exc:
            assert 'unsupported mood_label' in str(exc)
        else:
            raise AssertionError('unsupported mood_label should raise ValueError')

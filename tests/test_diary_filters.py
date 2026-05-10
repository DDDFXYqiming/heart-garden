"""日记搜索/筛选 API 集成测试"""
import sys
import os
import json
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ['JWT_SECRET'] = 'test-secret-key-for-testing'
os.environ['DEV_MODE'] = 'true'

from app.main import app


def _unique():
    return uuid.uuid4().hex[:8]


class TestDiaryFilters:
    def setup_method(self):
        self.client = app.test_client()
        suffix = _unique()

        # 注册 / 登录唯一用户
        self.username = f'filter_{suffix}'
        self.email = f'filter_{suffix}@test.com'
        self.client.post('/api/auth/register', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        login_resp = self.client.post('/api/auth/login', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        self.token = json.loads(login_resp.data)['data']['token']

        # 创建三篇不同标题 / 内容 / 情绪的日记
        self.diary_ids = []
        entries = [
            ('开心的一天', '今天真是开心快乐的一天啊'),
            ('难过的一天', '今天真是难过伤心的一天'),
            ('普通的一天', '今天星期一'),
        ]
        for title, content in entries:
            resp = self.client.post('/api/diaries', json={
                'title': title, 'content': content
            }, headers=self._auth())
            data = json.loads(resp.data)
            assert data['success'] is True
            self.diary_ids.append(data['data']['id'])

    def _auth(self):
        return {'Authorization': f'Bearer {self.token}'}

    def test_filter_by_keyword_title_match(self):
        """q 参数按 title 匹配"""
        resp = self.client.get('/api/diaries?q=开心', headers=self._auth())
        data = json.loads(resp.data)
        assert data['success'] is True
        ids = [item['id'] for item in data['data']['items']]
        assert self.diary_ids[0] in ids  # 开心的一天
        assert self.diary_ids[1] not in ids  # 难过的一天
        assert self.diary_ids[2] not in ids  # 普通的一天

    def test_filter_by_keyword_content_match(self):
        """q 参数按 content 匹配"""
        resp = self.client.get('/api/diaries?q=难过', headers=self._auth())
        data = json.loads(resp.data)
        assert data['success'] is True
        ids = [item['id'] for item in data['data']['items']]
        assert self.diary_ids[0] not in ids
        assert self.diary_ids[1] in ids
        assert self.diary_ids[2] not in ids

    def test_filter_by_mood(self):
        """mood 参数按 mood_label 筛选"""
        resp = self.client.get('/api/diaries?mood=中性', headers=self._auth())
        data = json.loads(resp.data)
        assert data['success'] is True
        ids = [item['id'] for item in data['data']['items']]
        assert self.diary_ids[0] not in ids
        assert self.diary_ids[1] not in ids
        assert self.diary_ids[2] in ids

    def test_filter_by_keyword_and_mood_combined(self):
        """q + mood 组合筛选"""
        resp = self.client.get('/api/diaries?q=开心&mood=开心', headers=self._auth())
        data = json.loads(resp.data)
        assert data['success'] is True
        ids = [item['id'] for item in data['data']['items']]
        assert self.diary_ids[0] in ids
        assert self.diary_ids[1] not in ids

    def test_filter_keyword_and_mood_no_match(self):
        """组合条件无匹配时返回空列表"""
        resp = self.client.get('/api/diaries?q=开心&mood=悲伤', headers=self._auth())
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['data']['items'] == []
        assert data['data']['total'] == 0

    def test_response_metadata_preserved(self):
        """筛选后的响应仍包含 total / page / per_page / items 字段"""
        resp = self.client.get('/api/diaries?q=开心', headers=self._auth())
        data = json.loads(resp.data)
        assert 'total' in data['data']
        assert 'page' in data['data']
        assert 'per_page' in data['data']
        assert 'items' in data['data']
        assert data['data']['page'] == 1
        assert data['data']['per_page'] == 10

    def test_keyword_search_treats_like_wildcards_as_literal_text(self):
        """q 参数中的 % / _ 应按普通字符搜索，不能变成 LIKE 通配符。"""
        special_resp = self.client.post('/api/diaries', json={
            'title': '百分比%符号', 'content': '这里有 literal_percent_marker'
        }, headers=self._auth())
        special_id = json.loads(special_resp.data)['data']['id']

        percent_resp = self.client.get('/api/diaries?q=%', headers=self._auth())
        percent_data = json.loads(percent_resp.data)
        percent_ids = [item['id'] for item in percent_data['data']['items']]
        assert percent_ids == [special_id]

        underscore_resp = self.client.get('/api/diaries?q=literal_percent_marker', headers=self._auth())
        underscore_data = json.loads(underscore_resp.data)
        underscore_ids = [item['id'] for item in underscore_data['data']['items']]
        assert underscore_ids == [special_id]

    def test_no_filter_returns_all(self):
        """无筛选参数时返回全部日记"""
        resp = self.client.get('/api/diaries', headers=self._auth())
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['data']['total'] == 3
        assert len(data['data']['items']) == 3

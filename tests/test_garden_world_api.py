"""记忆花园 world 接口测试"""
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ['JWT_SECRET'] = 'test-secret-key-for-testing'
os.environ['DEV_MODE'] = 'true'

from app.main import app


def _unique():
    return uuid.uuid4().hex[:8]


class TestGardenWorldAPI:
    def setup_method(self):
        self.client = app.test_client()
        suffix = _unique()
        self.username = f'garden_{suffix}'
        self.email = f'garden_{suffix}@test.com'
        self.client.post('/api/auth/register', json={
            'username': self.username,
            'email': self.email,
            'password': 'test123',
        })
        login_resp = self.client.post('/api/auth/login', json={
            'username': self.username,
            'email': self.email,
            'password': 'test123',
        })
        self.token = json.loads(login_resp.data)['data']['token']

    def _auth(self):
        return {'Authorization': f'Bearer {self.token}'}

    def test_garden_world_requires_auth(self):
        resp = self.client.get('/api/garden/world')
        assert resp.status_code == 401

    def test_empty_garden_world_contract(self):
        resp = self.client.get('/api/garden/world', headers=self._auth())
        data = json.loads(resp.data)

        assert resp.status_code == 200
        assert data['success'] is True
        assert data['data']['items'] == []
        assert data['data']['overview']['total_count'] == 0
        assert data['data']['themes'] == []
        assert data['data']['landmarks'] == []

    def test_garden_world_returns_themes_and_landmarks(self):
        samples = [
            ('工作压力', '今天项目会议很多，压力很大，但我还是完成了汇报。'),
            ('公园散步', '出门去公园看到了很好的风景，心里放松了一些。'),
            ('目标完成', '坚持练习以后终于完成了目标，这段经历很重要。' * 4),
        ]
        for title, content in samples:
            self.client.post('/api/diaries', json={
                'title': title,
                'content': content,
            }, headers=self._auth())

        resp = self.client.get('/api/garden/world', headers=self._auth())
        data = json.loads(resp.data)
        world = data['data']

        assert resp.status_code == 200
        assert data['success'] is True
        assert len(world['items']) == 3
        assert {'items', 'overview', 'themes', 'landmarks'} <= set(world.keys())
        assert {'id', 'title', 'content', 'content_preview', 'mood_score', 'mood_label', 'tags', 'ai_analysis', 'created_at', 'theme'} <= set(world['items'][0].keys())
        assert world['overview']['total_count'] == 3
        assert float(world['overview']['avg_score']) >= 0
        assert world['overview']['active_days'] >= 1
        assert any(theme['key'] == 'work' for theme in world['themes'])
        assert all({'type', 'source_id', 'date', 'theme', 'mood_score'} <= set(landmark.keys()) for landmark in world['landmarks'])

    def test_legacy_garden_endpoint_remains_compatible(self):
        self.client.post('/api/diaries', json={
            'title': '兼容旧接口',
            'content': '旧接口仍然只需要基础花园字段。',
        }, headers=self._auth())

        resp = self.client.get('/api/garden', headers=self._auth())
        data = json.loads(resp.data)

        assert resp.status_code == 200
        assert data['success'] is True
        assert len(data['data']) >= 1
        assert {'id', 'title', 'content', 'mood_score', 'created_at'} <= set(data['data'][0].keys())

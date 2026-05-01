"""API 端点集成测试"""
import sys
import os
import json
import tempfile
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 配置测试环境
os.environ['JWT_SECRET'] = 'test-secret-key-for-testing'
os.environ['DEV_MODE'] = 'true'

from app.main import app


def _unique():
    return uuid.uuid4().hex[:8]


class TestHealthAPI:
    def setup_method(self):
        self.client = app.test_client()

    def test_health_check(self):
        resp = self.client.get('/api/health')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data.get('ok') is True or data.get('success') is True


class TestAuthAPI:
    def setup_method(self):
        self.client = app.test_client()
        suffix = _unique()
        self.username = f'user_{suffix}'
        self.email = f'{suffix}@test.com'
        self.password = 'testpass123'

    def test_register_and_login(self):
        # 注册
        resp = self.client.post('/api/auth/register', json={
            'username': self.username,
            'email': self.email,
            'password': self.password
        })
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        token = data['data']['token']
        assert token

        # 登录
        resp = self.client.post('/api/auth/login', json={
            'username': self.username,
            'email': self.email,
            'password': self.password
        })
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['data']['token']

    def test_login_wrong_password(self):
        self.client.post('/api/auth/register', json={
            'username': self.username, 'email': self.email, 'password': self.password
        })
        resp = self.client.post('/api/auth/login', json={
            'username': self.username, 'email': self.email, 'password': 'wrong'
        })
        assert resp.status_code == 401

    def test_me_endpoint(self):
        self.client.post('/api/auth/register', json={
            'username': self.username, 'email': self.email, 'password': self.password
        })
        login_resp = self.client.post('/api/auth/login', json={
            'username': self.username, 'email': self.email, 'password': self.password
        })
        token = json.loads(login_resp.data)['data']['token']
        resp = self.client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True

    def test_me_no_token_returns_401(self):
        # IS_TESTING=true → DEV_MODE disabled → no token → 401
        resp = self.client.get('/api/auth/me')
        assert resp.status_code == 401


class TestDiaryAPI:
    def setup_method(self):
        self.client = app.test_client()
        suffix = _unique()
        self.username = f'diary_{suffix}'
        self.email = f'diary_{suffix}@test.com'
        self.client.post('/api/auth/register', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        login_resp = self.client.post('/api/auth/login', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        self.token = json.loads(login_resp.data)['data']['token']

    def _auth(self):
        return {'Authorization': f'Bearer {self.token}'}

    def test_create_diary(self):
        resp = self.client.post('/api/diaries', json={
            'title': '测试日记', 'content': '今天是个好日子'
        }, headers=self._auth())
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert 'id' in data['data']

    def test_get_diaries_list(self):
        self.client.post('/api/diaries', json={
            'title': '列表测试', 'content': 'content'
        }, headers=self._auth())
        resp = self.client.get('/api/diaries', headers=self._auth())
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['data']['total'] >= 1

    def test_get_diary_by_id(self):
        create_resp = self.client.post('/api/diaries', json={
            'title': '单条测试', 'content': '详情内容'
        }, headers=self._auth())
        diary_id = json.loads(create_resp.data)['data']['id']

        resp = self.client.get(f'/api/diaries/{diary_id}', headers=self._auth())
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['data']['title'] == '单条测试'

    def test_get_diary_not_found(self):
        resp = self.client.get('/api/diaries/nonexistent-id', headers=self._auth())
        assert resp.status_code == 404

    def test_update_diary(self):
        create_resp = self.client.post('/api/diaries', json={
            'title': '原标题', 'content': '原内容'
        }, headers=self._auth())
        diary_id = json.loads(create_resp.data)['data']['id']

        resp = self.client.put(f'/api/diaries/{diary_id}', json={
            'title': '新标题', 'content': '新内容'
        }, headers=self._auth())
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True

    def test_delete_diary(self):
        create_resp = self.client.post('/api/diaries', json={
            'title': '待删除', 'content': '内容'
        }, headers=self._auth())
        diary_id = json.loads(create_resp.data)['data']['id']

        resp = self.client.delete(f'/api/diaries/{diary_id}', headers=self._auth())
        assert resp.status_code == 200


class TestStatsAPI:
    def setup_method(self):
        self.client = app.test_client()
        suffix = _unique()
        self.username = f'stats_{suffix}'
        self.email = f'stats_{suffix}@test.com'
        self.client.post('/api/auth/register', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        login_resp = self.client.post('/api/auth/login', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        self.token = json.loads(login_resp.data)['data']['token']

    def _auth(self):
        return {'Authorization': f'Bearer {self.token}'}

    def test_stats_overview(self):
        resp = self.client.get('/api/stats/overview', headers=self._auth())
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        d = data['data']
        assert 'total_diaries' in d
        assert 'total_mood_records' in d
        assert 'total_conversations' in d
        assert 'avg_mood_score' in d
        assert 'last_7_days' in d


class TestMoodAPI:
    def setup_method(self):
        self.client = app.test_client()
        suffix = _unique()
        self.username = f'mood_{suffix}'
        self.email = f'mood_{suffix}@test.com'
        self.client.post('/api/auth/register', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        login_resp = self.client.post('/api/auth/login', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        self.token = json.loads(login_resp.data)['data']['token']

    def _auth(self):
        return {'Authorization': f'Bearer {self.token}'}

    def test_analyze_mood(self):
        resp = self.client.post('/api/mood/analyze', json={
            'text': '今天很开心'
        }, headers=self._auth())
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert 'mood_score' in data['data']
        assert 'mood_label' in data['data']


class TestConversationAPI:
    def setup_method(self):
        self.client = app.test_client()
        suffix = _unique()
        self.username = f'conv_{suffix}'
        self.email = f'conv_{suffix}@test.com'
        self.client.post('/api/auth/register', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        login_resp = self.client.post('/api/auth/login', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        self.token = json.loads(login_resp.data)['data']['token']

    def _auth(self):
        return {'Authorization': f'Bearer {self.token}'}

    def test_conversations_list_empty(self):
        resp = self.client.get('/api/conversations', headers=self._auth())
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_chat_creates_conversation(self):
        resp = self.client.post('/api/chat', json={
            'message': '你好'
        }, headers=self._auth())
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert 'conversation_id' in data['data']
        assert data['data']['response']

    def test_conversation_detail(self):
        chat_resp = self.client.post('/api/chat', json={
            'message': '测试对话'
        }, headers=self._auth())
        conv_id = json.loads(chat_resp.data)['data']['conversation_id']

        resp = self.client.get(f'/api/conversations/{conv_id}', headers=self._auth())
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert len(data['data']['messages']) >= 2  # user + assistant

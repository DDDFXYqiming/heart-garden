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

    def test_custom_words_temporarily_disabled(self):
        get_resp = self.client.get('/api/mood/words', headers=self._auth())
        get_data = json.loads(get_resp.data)
        assert get_resp.status_code == 200
        assert get_data['success'] is True
        assert get_data['data'] == []
        assert get_data['feature_enabled'] is False

        post_resp = self.client.post('/api/mood/words', json={
            'word': '超开心', 'category': '自定义', 'word_type': 'positive'
        }, headers=self._auth())
        post_data = json.loads(post_resp.data)
        assert post_resp.status_code == 403
        assert post_data['success'] is False


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

    def _enable_llm_config(self):
        resp = self.client.post('/api/llm/config', json={
            'enabled': True,
            'base_url': 'https://api.deepseek.com/v1',
            'api_key': 'unit-test-chat-llm-key',
            'model': 'deepseek-chat',
            'temperature': 0.7
        }, headers=self._auth())
        assert resp.status_code == 200

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

    def test_chat_positive_message_records_mood_stats(self):
        resp = self.client.post('/api/chat', json={
            'message': '太好了太开心了，今天完成了很多项目！！！'
        }, headers=self._auth())
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['data']['mood'] == '开心'

        trend_resp = self.client.get('/api/mood/trend?days=7', headers=self._auth())
        trend_data = json.loads(trend_resp.data)
        assert trend_resp.status_code == 200
        assert any(r['label'] == '开心' and r['score'] >= 75 for r in trend_data['data'])

        dist_resp = self.client.get('/api/mood/distribution?days=7', headers=self._auth())
        dist_data = json.loads(dist_resp.data)
        assert dist_resp.status_code == 200
        assert dist_data['data']['开心'] >= 1

    def test_chat_stream_positive_message_records_mood_stats(self):
        resp = self.client.post('/api/chat/stream', json={
            'message': '今天天气真好呀'
        }, headers=self._auth(), buffered=True)
        body = resp.data.decode('utf-8')
        assert resp.status_code == 200
        assert '"type": "done"' in body
        assert '"mood": "开心"' in body

        dist_resp = self.client.get('/api/mood/distribution?days=7', headers=self._auth())
        dist_data = json.loads(dist_resp.data)
        assert dist_resp.status_code == 200
        assert dist_data['data']['开心'] >= 1

    def test_chat_uses_llm_mood_when_configured(self, monkeypatch):
        self._enable_llm_config()
        captured = {}

        def fake_analyze_mood(message, user_config=None):
            captured['message'] = message
            captured['api_key_set'] = bool((user_config or {}).get('api_key'))
            return True, {
                'mood_score': 92.0,
                'mood_label': '开心',
                'keywords': ['完成项目', '开心'],
                'trend': '上升',
                'positive_count': 0,
                'negative_count': 0,
                'analysis_source': 'llm'
            }, None

        def fake_chat_with_fallback(**kwargs):
            return True, 'LLM 陪伴回复', 'llm'

        monkeypatch.setattr(app.llm_service, 'analyze_mood', fake_analyze_mood)
        monkeypatch.setattr(app.llm_service, 'chat_with_fallback', fake_chat_with_fallback)

        resp = self.client.post('/api/chat', json={
            'message': '今天终于把复杂项目推进完了'
        }, headers=self._auth())
        data = json.loads(resp.data)

        assert resp.status_code == 200
        assert data['success'] is True
        assert data['data']['mood'] == '开心'
        assert data['data']['mood_source'] == 'llm'
        assert data['data']['response_mode'] == 'llm'
        assert captured['message'] == '今天终于把复杂项目推进完了'
        assert captured['api_key_set'] is True

        dist_resp = self.client.get('/api/mood/distribution?days=7', headers=self._auth())
        dist_data = json.loads(dist_resp.data)
        assert dist_resp.status_code == 200
        assert dist_data['data']['开心'] >= 1

    def test_chat_falls_back_to_rule_mood_when_llm_mood_fails(self, monkeypatch):
        self._enable_llm_config()

        def fake_analyze_mood(message, user_config=None):
            return False, None, 'invalid_json'

        def fake_chat_with_fallback(**kwargs):
            return True, 'LLM 陪伴回复', 'llm'

        monkeypatch.setattr(app.llm_service, 'analyze_mood', fake_analyze_mood)
        monkeypatch.setattr(app.llm_service, 'chat_with_fallback', fake_chat_with_fallback)

        resp = self.client.post('/api/chat', json={
            'message': '太好了太开心了，今天完成了很多项目！！！'
        }, headers=self._auth())
        data = json.loads(resp.data)

        assert resp.status_code == 200
        assert data['success'] is True
        assert data['data']['mood'] == '开心'
        assert data['data']['mood_source'] == 'rule_engine'
        assert data['data']['response_mode'] == 'llm'

    def test_chat_stream_uses_llm_mood_when_configured(self, monkeypatch):
        self._enable_llm_config()

        def fake_analyze_mood(message, user_config=None):
            return True, {
                'mood_score': 33.0,
                'mood_label': '焦虑',
                'keywords': ['压力', '担心'],
                'trend': '下降',
                'positive_count': 0,
                'negative_count': 0,
                'analysis_source': 'llm'
            }, None

        def fake_chat_stream(**kwargs):
            yield '我在，慢慢说。'

        monkeypatch.setattr(app.llm_service, 'analyze_mood', fake_analyze_mood)
        monkeypatch.setattr(app.llm_service, 'chat_stream', fake_chat_stream)

        resp = self.client.post('/api/chat/stream', json={
            'message': '这个项目让我有点担心'
        }, headers=self._auth(), buffered=True)
        body = resp.data.decode('utf-8')

        assert resp.status_code == 200
        assert '"type": "done"' in body
        assert '"mood": "焦虑"' in body
        assert '"mood_source": "llm"' in body
        assert '"response_mode": "llm"' in body

        dist_resp = self.client.get('/api/mood/distribution?days=7', headers=self._auth())
        dist_data = json.loads(dist_resp.data)
        assert dist_resp.status_code == 200
        assert dist_data['data']['焦虑'] >= 1

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


class TestLLMConfigAPI:
    def setup_method(self):
        self.client = app.test_client()
        suffix = _unique()
        self.username = f'llm_{suffix}'
        self.email = f'llm_{suffix}@test.com'
        self.client.post('/api/auth/register', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        login_resp = self.client.post('/api/auth/login', json={
            'username': self.username, 'email': self.email, 'password': 'test123'
        })
        self.token = json.loads(login_resp.data)['data']['token']

    def _auth(self):
        return {'Authorization': f'Bearer {self.token}'}

    def _save_real_config(self, api_key='unit-test-api-key-v304'):
        resp = self.client.post('/api/llm/config', json={
            'enabled': True,
            'base_url': 'https://api.deepseek.com/v1',
            'api_key': api_key,
            'model': 'deepseek-chat',
            'temperature': 0.7
        }, headers=self._auth())
        assert resp.status_code == 200
        return api_key

    def test_llm_config_get_does_not_leak_real_api_key(self):
        real_key = self._save_real_config()

        resp = self.client.get('/api/llm/config', headers=self._auth())
        data = json.loads(resp.data)

        assert resp.status_code == 200
        assert data['success'] is True
        assert real_key not in json.dumps(data, ensure_ascii=False)
        assert data['data']['api_key'] == ''
        assert data['data']['api_key_saved'] is True
        assert data['data']['api_key_preview'].endswith('****')

    def test_save_llm_config_preserves_saved_api_key_when_omitted_or_masked(self, monkeypatch):
        real_key = self._save_real_config()

        for api_key_payload in [None, 'unit-test****', '••••••••']:
            payload = {
                'enabled': True,
                'base_url': 'https://api.deepseek.com/v1',
                'model': 'deepseek-chat',
                'temperature': 0.8
            }
            if api_key_payload is not None:
                payload['api_key'] = api_key_payload

            save_resp = self.client.post('/api/llm/config', json=payload, headers=self._auth())
            assert save_resp.status_code == 200

            captured = {}

            def fake_test_connection(config):
                captured.update(config)
                return {'success': True, 'model': config['model'], 'message': 'ok'}

            monkeypatch.setattr(app.llm_service, 'test_connection', fake_test_connection)
            test_resp = self.client.post('/api/llm/test', json={
                'base_url': 'https://api.deepseek.com/v1',
                'model': 'deepseek-chat'
            }, headers=self._auth())
            test_data = json.loads(test_resp.data)

            assert test_resp.status_code == 200
            assert test_data['data']['success'] is True
            assert captured['api_key'] == real_key

    def test_llm_test_uses_new_unsaved_api_key_when_provided(self, monkeypatch):
        self._save_real_config(api_key='saved-unit-test-key')
        captured = {}

        def fake_test_connection(config):
            captured.update(config)
            return {'success': True, 'model': config['model'], 'message': 'ok'}

        monkeypatch.setattr(app.llm_service, 'test_connection', fake_test_connection)
        resp = self.client.post('/api/llm/test', json={
            'base_url': 'https://api.deepseek.com/v1',
            'api_key': 'unsaved-unit-test-key',
            'model': 'deepseek-chat'
        }, headers=self._auth())
        data = json.loads(resp.data)

        assert resp.status_code == 200
        assert data['data']['success'] is True
        assert captured['api_key'] == 'unsaved-unit-test-key'

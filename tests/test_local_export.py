"""Local Data Export API Integration Tests"""
import sys
import os
import json
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 配置测试环境
os.environ['JWT_SECRET'] = 'test-secret-key-for-testing'
os.environ['DEV_MODE'] = 'true'

from app.main import app


def _unique():
    return uuid.uuid4().hex[:8]


class TestLocalExport:
    def setup_method(self):
        self.client = app.test_client()
        suffix = _unique()
        self.username = f'export_{suffix}'
        self.email = f'export_{suffix}@test.com'
        self.password = 'testpass123'

        # Register
        self.client.post('/api/auth/register', json={
            'username': self.username,
            'email': self.email,
            'password': self.password
        })
        # Login
        login_resp = self.client.post('/api/auth/login', json={
            'username': self.username,
            'email': self.email,
            'password': self.password
        })
        data = json.loads(login_resp.data)
        self.token = data['data']['token']

        # Enable LLM config so chat works
        self.client.post('/api/llm/config', json={
            'enabled': True,
            'base_url': 'https://api.deepseek.com/v1',
            'api_key': 'unit-test-chat-llm-key',
            'model': 'deepseek-chat',
            'temperature': 0.7
        }, headers=self._auth())

    def _auth(self):
        return {'Authorization': f'Bearer {self.token}'}

    def test_export_requires_auth(self):
        """No-token request returns 401."""
        resp = self.client.get('/api/export')
        assert resp.status_code == 401
        data = json.loads(resp.data)
        assert data['success'] is False

    def test_export_route_does_not_use_dev_mode_auth_bypass(self):
        """Export route must require explicit JWT instead of the global DEV_MODE bypass."""
        from pathlib import Path
        source = Path('app/routes/export_routes.py').read_text(encoding='utf-8')
        assert '@require_explicit_auth' in source
        assert '@require_auth' not in source
        assert 'verify_token(token)' in source

    def test_export_returns_all_categories_with_safe_fields(self):
        """Full export test: create diary + chat, export, verify structure and safe fields."""
        # --- Create a diary ---
        diary_resp = self.client.post('/api/diaries', json={
            'title': '导出测试日记',
            'content': '今天测试数据导出功能'
        }, headers=self._auth())
        diary_data = json.loads(diary_resp.data)
        assert diary_resp.status_code == 200
        diary_id = diary_data['data']['id']

        # --- Create a chat/conversation ---
        chat_resp = self.client.post('/api/chat', json={
            'message': '今天心情不错，测试导出功能'
        }, headers=self._auth())
        chat_data = json.loads(chat_resp.data)
        assert chat_resp.status_code == 200
        conversation_id = chat_data['data']['conversation_id']

        # --- Export ---
        resp = self.client.get('/api/export', headers=self._auth())
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True

        export = data['data']

        # Verify top-level structure
        assert 'exported_at' in export
        assert 'diaries' in export
        assert 'mood_records' in export
        assert 'conversations' in export

        # Verify diary belongs to current user (diary exists)
        assert len(export['diaries']) >= 1
        diary_ids = [d['id'] for d in export['diaries']]
        assert diary_id in diary_ids

        # Verify the diary export contains safe fields only
        exported_diary = next(d for d in export['diaries'] if d['id'] == diary_id)
        assert 'title' in exported_diary
        assert 'content' in exported_diary
        assert 'mood_score' in exported_diary
        assert 'mood_label' in exported_diary
        assert 'tags' in exported_diary
        assert 'ai_analysis' in exported_diary
        assert 'created_at' in exported_diary
        assert 'updated_at' in exported_diary
        # password_hash must NOT be in diaries
        assert 'password_hash' not in exported_diary

        # Verify conversations
        assert len(export['conversations']) >= 1
        conv_ids = [c['id'] for c in export['conversations']]
        assert conversation_id in conv_ids

        # Verify conversation has nested messages
        exported_conv = next(c for c in export['conversations'] if c['id'] == conversation_id)
        assert 'id' in exported_conv
        assert 'title' in exported_conv
        assert 'created_at' in exported_conv
        assert 'updated_at' in exported_conv
        assert 'messages' in exported_conv
        assert len(exported_conv['messages']) >= 1
        for msg in exported_conv['messages']:
            assert 'role' in msg
            assert 'content' in msg
            assert 'mood_label' in msg
            assert 'created_at' in msg

        # Verify mood_records
        assert len(export['mood_records']) >= 1
        for mr in export['mood_records']:
            assert 'id' in mr
            assert 'mood_score' in mr
            assert 'mood_label' in mr
            assert 'timestamp' in mr
            # password_hash must NOT be in mood_records
            assert 'password_hash' not in mr

        # --- Sensitive field leak detection ---
        body_str = json.dumps(data, ensure_ascii=False)

        # password_hash must NEVER appear anywhere in the response
        assert 'password_hash' not in body_str, "password_hash leaked in export!"

        # llm_config must not appear
        assert 'llm_config' not in body_str, "llm_config leaked in export!"

        # api_key must not appear (the test api_key value)
        assert 'unit-test-chat-llm-key' not in body_str, "api_key leaked in export!"

        # JWT_SECRET must not appear
        assert 'test-secret-key-for-testing' not in body_str, "JWT_SECRET leaked in export!"

        # The test password must not appear
        assert self.password not in body_str, "User password leaked in export!"

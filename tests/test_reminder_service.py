"""
测试提醒服务 reminder_service.py
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
import uuid
from services import reminder_service
from app import create_app


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


def _unique():
    return uuid.uuid4().hex[:8]


@pytest.fixture
def auth_headers(client):
    """获取认证头"""
    # 使用唯一用户名，避免重复注册
    suffix = _unique()
    username = f'testuser_{suffix}'
    email = f'test_{suffix}@example.com'
    
    # 先注册
    client.post('/api/auth/register', json={
        'username': username,
        'email': email,
        'password': 'Test123!'
    })
    
    # 登录获取token
    res = client.post('/api/auth/login', json={
        'username': username,
        'password': 'Test123!'
    })
    
    token = res.get_json()['data']['token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def setup_test_data(app, auth_headers, client):
    """设置测试数据"""
    with app.app_context():
        # 获取用户ID
        res = client.get('/api/auth/me', headers=auth_headers)
        user_id = res.get_json()['data']['user_id']
        
        # 添加测试情绪记录
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 插入3条低分情绪记录（使用唯一ID）
        test_id = _unique()
        for i in range(3):
            cursor.execute('''
                INSERT INTO mood_records (id, user_id, mood_score, mood_label, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                f'test-mood-{test_id}-{i}',
                user_id,
                30.0,  # 低于40，应该触发预警
                '悲伤',
                (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        conn.commit()
        conn.close()
        
        return user_id


class TestCheckMoodAlert:
    """测试情绪预警检查"""
    
    def test_check_mood_alert_triggers(self, app, setup_test_data):
        """测试情绪分数低时触发预警"""
        user_id = setup_test_data
        with app.app_context():
            result = reminder_service.check_mood_alert(user_id)
            assert result == True
    
    def test_check_mood_alert_no_trigger(self, app, auth_headers, client):
        """测试情绪分数高时不触发预警"""
        # 获取用户ID
        res = client.get('/api/auth/me', headers=auth_headers)
        user_id = res.get_json()['data']['user_id']
        
        with app.app_context():
            # 添加高分情绪记录（使用唯一ID）
            test_id = _unique()
            conn = sqlite3.connect(app.config['DATABASE'])
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO mood_records (id, user_id, mood_score, mood_label, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (f'test-mood-high-{test_id}', user_id, 80.0, '开心', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            
            result = reminder_service.check_mood_alert(user_id)
            assert result == False


class TestGetReminderSettings:
    """测试获取提醒设置"""
    
    def test_get_reminder_settings_default(self, app, setup_test_data):
        """测试获取默认提醒设置"""
        user_id = setup_test_data
        with app.app_context():
            settings = reminder_service.get_reminder_settings(user_id)
            assert len(settings) == 2
            assert settings[0]['reminder_type'] in ['mood_alert', 'daily_care']
            assert settings[1]['reminder_type'] in ['mood_alert', 'daily_care']


class TestUpdateReminderSettings:
    """测试更新提醒设置"""
    
    def test_update_reminder_settings(self, app, setup_test_data):
        """测试更新提醒设置"""
        user_id = setup_test_data
        with app.app_context():
            # 先获取默认设置
            settings = reminder_service.get_reminder_settings(user_id)
            
            # 修改设置
            settings[0]['enabled'] = False
            settings[0]['threshold_score'] = 50.0
            
            # 更新
            result = reminder_service.update_reminder_settings(user_id, settings)
            assert result == True
            
            # 验证更新
            updated = reminder_service.get_reminder_settings(user_id)
            assert updated[0]['enabled'] == False
            assert updated[0]['threshold_score'] == 50.0


class TestNotifications:
    """测试通知相关功能"""
    
    def test_get_notifications_empty(self, app, setup_test_data):
        """测试获取空通知列表"""
        user_id = setup_test_data
        with app.app_context():
            result = reminder_service.get_notifications(user_id)
            assert result['notifications'] == []
            assert result['unread_count'] == 0
    
    def test_send_and_get_notification(self, app, setup_test_data):
        """测试发送并获取通知"""
        user_id = setup_test_data
        with app.app_context():
            # 发送通知
            notification_id = reminder_service.send_notification(
                user_id, 'test', '测试标题', '测试内容'
            )
            assert notification_id is not None
            
            # 获取通知
            result = reminder_service.get_notifications(user_id)
            assert len(result['notifications']) == 1
            assert result['unread_count'] == 1
            
            # 标记已读
            success = reminder_service.mark_notification_read(notification_id, user_id)
            assert success == True
            
            # 验证已读
            result = reminder_service.get_notifications(user_id)
            assert result['unread_count'] == 0
    
    def test_mark_all_read(self, app, setup_test_data):
        """测试全部标记已读"""
        user_id = setup_test_data
        with app.app_context():
            # 发送多条通知
            for i in range(3):
                reminder_service.send_notification(
                    user_id, 'test', f'标题{i}', f'内容{i}'
                )
            
            # 全部标记已读
            count = reminder_service.mark_all_read(user_id)
            assert count == 3
            
            # 验证
            result = reminder_service.get_notifications(user_id)
            assert result['unread_count'] == 0


class TestGenerateCareMessage:
    """测试生成关怀消息"""
    
    def test_generate_care_message(self, app, setup_test_data):
        """测试生成关怀消息"""
        user_id = setup_test_data
        with app.app_context():
            # 这个函数可能会调用LLM，如果失败则返回默认消息
            message = reminder_service.generate_care_message(user_id)
            assert message is not None
            assert len(message) > 0

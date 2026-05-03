"""
测试社区服务 community_service.py
"""

import pytest
import sqlite3
import uuid
from app import create_app
from services import community_service


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
    suffix = _unique()
    username = f'testuser_{suffix}'
    email = f'test_{suffix}@example.com'
    
    client.post('/api/auth/register', json={
        'username': username,
        'email': email,
        'password': 'Test123!'
    })
    
    res = client.post('/api/auth/login', json={
        'username': username,
        'password': 'Test123!'
    })
    
    token = res.get_json()['data']['token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def user_id(app, auth_headers, client):
    """获取当前用户ID"""
    with app.app_context():
        res = client.get('/api/auth/me', headers=auth_headers)
        return res.get_json()['data']['user_id']


class TestCreatePost:
    """测试创建帖子"""
    
    def test_create_post_anonymous(self, app, user_id):
        """测试匿名发布帖子"""
        with app.app_context():
            post_id = community_service.create_post(
                user_id, '测试匿名帖子内容', '开心', 80.0, True
            )
            assert post_id is not None
            assert len(post_id) > 0
    
    def test_create_post_not_anonymous(self, app, user_id):
        """测试实名发布帖子"""
        with app.app_context():
            post_id = community_service.create_post(
                user_id, '测试实名帖子内容', '平静', 65.0, False
            )
            assert post_id is not None
            
            conn = sqlite3.connect(app.config['DATABASE'])
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM community_posts WHERE id = ?', (post_id,))
            row = cursor.fetchone()
            conn.close()
            
            assert row is not None
            assert row['is_anonymous'] == 0


class TestGetPosts:
    """测试获取帖子列表"""
    
    def setup_method(self):
        """每个测试前清理 community_posts 表"""
        app = create_app()
        with app.app_context():
            conn = sqlite3.connect(app.config['DATABASE'])
            cursor = conn.cursor()
            cursor.execute('DELETE FROM community_posts')
            cursor.execute('DELETE FROM post_likes')
            cursor.execute('DELETE FROM post_comments')
            conn.commit()
            conn.close()
    
    def test_get_posts_empty(self, app):
        """测试空列表"""
        with app.app_context():
            result = community_service.get_posts(page=1)
            assert result['total'] == 0
            assert len(result['posts']) == 0
    
    def test_get_posts_with_data(self, app, user_id):
        """测试有数据时的列表"""
        with app.app_context():
            # 创建几个测试帖子
            for i in range(3):
                community_service.create_post(
                    user_id, f'测试帖子{i}', '开心', 80.0, True
                )
            
            result = community_service.get_posts(page=1, per_page=10)
            assert result['total'] == 3
            assert len(result['posts']) == 3
            assert result['page'] == 1
    
    def test_get_posts_pagination(self, app, user_id):
        """测试分页功能"""
        with app.app_context():
            # 创建15个帖子
            for i in range(15):
                community_service.create_post(
                    user_id, f'测试帖子{i}', '开心', 80.0, True
                )
            
            # 第一页
            result = community_service.get_posts(page=1, per_page=10)
            assert len(result['posts']) == 10
            assert result['total_pages'] == 2
            
            # 第二页
            result = community_service.get_posts(page=2, per_page=10)
            assert len(result['posts']) == 5
    
    def test_get_posts_mood_filter(self, app, user_id):
        """测试情绪筛选"""
        with app.app_context():
            # 创建不同情绪的帖子
            community_service.create_post(user_id, '开心帖子', '开心', 80.0, True)
            community_service.create_post(user_id, '悲伤帖子', '悲伤', 20.0, True)
            
            # 筛选开心
            result = community_service.get_posts(mood_filter='开心')
            assert result['total'] == 1
            assert result['posts'][0]['mood_label'] == '开心'
            
            # 筛选悲伤
            result = community_service.get_posts(mood_filter='悲伤')
            assert result['total'] == 1
            assert result['posts'][0]['mood_label'] == '悲伤'

"""
认证 API 路由
"""

import uuid
from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from ..db import query_db, execute_db
from ..auth import require_auth, create_token
from .. import logger, limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '请求体不能为空'}
        }), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '用户名、邮箱和密码不能为空'}
        }), 400

    if len(username) < 2 or len(username) > 50:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '用户名长度需要在 2-50 个字符之间'}
        }), 400

    if len(password) < 6:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '密码长度不能少于 6 个字符'}
        }), 400

    existing = query_db('SELECT id FROM users WHERE username = ? OR email = ?',
                      (username, email), one=True)
    if existing:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '用户名或邮箱已被注册'}
        }), 400

    user_id = str(uuid.uuid4())
    password_hash = generate_password_hash(password)

    execute_db('''
    INSERT INTO users (id, username, email, password_hash)
    VALUES (?, ?, ?, ?)
    ''', (user_id, username, email, password_hash))

    token = create_token(user_id)

    logger.info(f"User registered: {username}")
    return jsonify({
        'success': True,
        'data': {
            'user_id': user_id,
            'username': username,
            'email': email,
            'token': token
        }
    })


@auth_bp.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '请求体不能为空'}
        }), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not password:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '密码不能为空'}
        }), 400

    if not username and not email:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '用户名或邮箱不能为空'}
        }), 400

    user = query_db(
        'SELECT id, username, email, password_hash FROM users WHERE username = ? OR email = ?',
        (username or email, email or username), one=True
    )

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({
            'success': False,
            'error': {'code': 401, 'message': '用户名或密码错误'}
        }), 401

    token = create_token(user['id'])

    logger.info(f"User logged in: {user['username']}")
    return jsonify({
        'success': True,
        'data': {
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'token': token
        }
    })


@auth_bp.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    user = query_db(
        'SELECT id, username, email, created_at FROM users WHERE id = ?',
        (g.current_user_id,), one=True
    )
    if not user:
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '用户不存在'}
        }), 404

    diary_count = query_db(
        'SELECT COUNT(*) as count FROM diaries WHERE user_id = ?',
        (g.current_user_id,), one=True
    )

    return jsonify({
        'success': True,
        'data': {
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at'],
            'diary_count': diary_count['count'] if diary_count else 0
        }
    })

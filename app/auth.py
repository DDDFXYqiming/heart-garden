"""
JWT 认证与辅助工具模块
"""

import jwt as pyjwt
from datetime import datetime, timedelta
from functools import wraps
from flask import g, request, current_app, jsonify

from . import DEV_MODE, logger


def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=current_app.config['JWT_EXPIRATION_HOURS']),
        'iat': datetime.utcnow()
    }
    return pyjwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')


def verify_token(token):
    try:
        payload = pyjwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload['user_id']
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            user_id = verify_token(token)
            if user_id:
                g.current_user_id = user_id
                return f(*args, **kwargs)
        if DEV_MODE:
            g.current_user_id = 'dev-user'
            return f(*args, **kwargs)
        if not token:
            return jsonify({
                'success': False,
                'error': {'code': 401, 'message': '未提供认证令牌'}
            }), 401
        return jsonify({
            'success': False,
            'error': {'code': 401, 'message': '令牌无效或已过期'}
        }), 401
    return decorated


def _error_details(msg: str) -> str | None:
    """Return detailed error info only in debug/dev mode."""
    return msg if current_app.debug or DEV_MODE else None


def _analyze_with_custom_words(user_id, text):
    """Query custom_words from DB and analyze text with them."""
    from .db import query_db
    mood_analyzer = current_app.mood_analyzer
    rows = query_db(
        'SELECT word, word_type FROM custom_words WHERE user_id = ?',
        (user_id,)
    )
    return mood_analyzer.analyze(
        text,
        custom_words=[{'word': w['word'], 'type': w['word_type']} for w in rows]
    )

"""
Local Data Export API - returns safe JSON export of user data.
"""
from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, g, request

from ..db import query_db
from ..auth import verify_token
from .. import logger

export_bp = Blueprint('export', __name__)


def require_explicit_auth(f):
    """Require a valid JWT even when global DEV_MODE bypass is enabled.

    Local export returns a full copy of personal diaries and conversations, so it
    should never be exposed through the convenience development bypass.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({
                'success': False,
                'error': {'code': 401, 'message': '未提供认证令牌'}
            }), 401

        user_id = verify_token(token)
        if not user_id:
            return jsonify({
                'success': False,
                'error': {'code': 401, 'message': '令牌无效或已过期'}
            }), 401

        g.current_user_id = user_id
        return f(*args, **kwargs)

    return decorated


@export_bp.route('/api/export', methods=['GET'])
@require_explicit_auth
def export_data():
    """Return all user data (diaries, mood_records, conversations) as JSON.

    Only safe fields are included — no password_hash, llm_config, or API keys.
    """
    user_id = g.current_user_id

    # --- Diaries: safe fields only ---
    diaries = query_db(
        '''SELECT id, title, content, mood_score, mood_label, tags, ai_analysis,
                  created_at, updated_at
           FROM diaries
           WHERE user_id = ?
           ORDER BY created_at DESC''',
        (user_id,)
    )

    # --- Mood records: safe fields only ---
    mood_records = query_db(
        '''SELECT id, diary_id, mood_score, mood_label, keywords, trend,
                  source_type, source_id, timestamp
           FROM mood_records
           WHERE user_id = ?
           ORDER BY timestamp DESC''',
        (user_id,)
    )

    # --- Conversations with nested messages ---
    conversations = query_db(
        '''SELECT id, title, created_at, updated_at
           FROM conversations
           WHERE user_id = ?
           ORDER BY updated_at DESC''',
        (user_id,)
    )

    export_convs = []
    for conv in conversations:
        messages = query_db(
            '''SELECT role, content, mood_label, created_at
               FROM chat_history
               WHERE conversation_id = ?
               ORDER BY created_at ASC''',
            (conv['id'],)
        )
        export_convs.append({
            'id': conv['id'],
            'title': conv['title'],
            'created_at': conv['created_at'],
            'updated_at': conv['updated_at'],
            'messages': [
                {
                    'role': m['role'],
                    'content': m['content'],
                    'mood_label': m['mood_label'],
                    'created_at': m['created_at']
                }
                for m in messages
            ]
        })

    result = {
        'exported_at': datetime.utcnow().isoformat() + 'Z',
        'diaries': [
            {
                'id': d['id'],
                'title': d['title'],
                'content': d['content'],
                'mood_score': d['mood_score'],
                'mood_label': d['mood_label'],
                'tags': d['tags'],
                'ai_analysis': d['ai_analysis'],
                'created_at': d['created_at'],
                'updated_at': d['updated_at']
            }
            for d in diaries
        ],
        'mood_records': [
            {
                'id': m['id'],
                'diary_id': m['diary_id'],
                'mood_score': m['mood_score'],
                'mood_label': m['mood_label'],
                'keywords': m['keywords'],
                'trend': m['trend'],
                'source_type': m['source_type'],
                'source_id': m['source_id'],
                'timestamp': m['timestamp']
            }
            for m in mood_records
        ],
        'conversations': export_convs,
    }

    logger.info(
        "Data export user=%s diaries=%d mood_records=%d conversations=%d",
        user_id,
        len(result['diaries']),
        len(result['mood_records']),
        len(result['conversations']),
    )

    return jsonify({'success': True, 'data': result})

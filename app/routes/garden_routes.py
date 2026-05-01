"""
记忆花园 API 路由
"""

from flask import Blueprint, jsonify, g
from ..db import query_db
from ..auth import require_auth
from .. import logger

garden_bp = Blueprint('garden', __name__)


@garden_bp.route('/api/garden', methods=['GET'])
@require_auth
def get_garden():
    rows = query_db('''
    SELECT id, title, content, mood_score, created_at
    FROM diaries
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT 50
    ''', (g.current_user_id,))

    logger.info(f"Get garden: {len(rows)} diaries, user: {g.current_user_id}")
    return jsonify({
        'success': True,
        'data': [
            {
                'id': r['id'],
                'title': r['title'],
                'content': r['content'],
                'mood_score': r['mood_score'],
                'created_at': r['created_at']
            }
            for r in rows
        ]
    })

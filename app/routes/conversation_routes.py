"""
对话 API 路由
"""

import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from ..db import query_db, execute_db
from ..auth import require_auth
from .. import logger

conversation_bp = Blueprint('conversation', __name__)


@conversation_bp.route('/api/conversations', methods=['POST'])
@require_auth
def create_conversation():
    data = request.json
    conversation_id = str(uuid.uuid4())
    title = data.get('title', '新对话')

    execute_db('''
    INSERT INTO conversations (id, user_id, title)
    VALUES (?, ?, ?)
    ''', (conversation_id, g.current_user_id, title))

    logger.info(f"Conversation created: {conversation_id}, user: {g.current_user_id}")
    return jsonify({
        'success': True,
        'data': {
            'id': conversation_id,
            'title': title,
            'created_at': datetime.now().isoformat()
        }
    })


@conversation_bp.route('/api/conversations', methods=['GET'])
@require_auth
def get_conversations():
    rows = query_db('''
    SELECT c.id, c.title, c.created_at, lm.content as last_message
    FROM conversations c
    LEFT JOIN (
        SELECT conversation_id, content
        FROM chat_history
        WHERE id IN (
            SELECT MAX(id) FROM chat_history GROUP BY conversation_id
        )
    ) lm ON lm.conversation_id = c.id
    WHERE c.user_id = ?
    ORDER BY c.updated_at DESC
    ''', (g.current_user_id,))

    return jsonify({
        'success': True,
        'data': [
            {
                'id': r['id'],
                'title': r['title'],
                'last_message': r['last_message'],
                'created_at': r['created_at']
            }
            for r in rows
        ]
    })


@conversation_bp.route('/api/conversations/<conversation_id>', methods=['GET'])
@require_auth
def get_conversation(conversation_id):
    conv = query_db(
        'SELECT id, title, created_at FROM conversations WHERE id = ? AND user_id = ?',
        (conversation_id, g.current_user_id), one=True
    )
    if not conv:
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '对话不存在'}
        }), 404

    messages = query_db('''
    SELECT id, role, content, mood_label, created_at
    FROM chat_history
    WHERE conversation_id = ?
    ORDER BY created_at ASC
    ''', (conversation_id,))

    return jsonify({
        'success': True,
        'data': {
            'id': conv['id'],
            'title': conv['title'],
            'created_at': conv['created_at'],
            'messages': [
                {
                    'id': m['id'],
                    'role': m['role'],
                    'content': m['content'],
                    'mood_label': m['mood_label'],
                    'created_at': m['created_at']
                }
                for m in messages
            ]
        }
    })


@conversation_bp.route('/api/conversations/<conversation_id>', methods=['DELETE'])
@require_auth
def delete_conversation(conversation_id):
    existing = query_db(
        'SELECT id FROM conversations WHERE id = ? AND user_id = ?',
        (conversation_id, g.current_user_id), one=True
    )
    if not existing:
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '对话不存在'}
        }), 404

    execute_db('DELETE FROM chat_history WHERE conversation_id = ?', (conversation_id,))
    execute_db('DELETE FROM mood_records WHERE source_type = ? AND source_id = ? AND user_id = ?',
              ('chat', conversation_id, g.current_user_id))
    execute_db('DELETE FROM conversations WHERE id = ? AND user_id = ?',
              (conversation_id, g.current_user_id))

    return jsonify({'success': True, 'data': None})

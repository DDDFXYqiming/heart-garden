"""
日记 API 路由
"""

import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g, current_app
from ..db import query_db, execute_db
from ..auth import require_auth, _analyze_with_custom_words
from ..mood_records import record_mood
from .. import logger

diary_bp = Blueprint('diary', __name__)


def _escape_like(term):
    """Escape SQLite LIKE wildcards so diary search treats user text literally."""
    return term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


@diary_bp.route('/api/diaries', methods=['POST'])
@require_auth
def create_diary():
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '请求体不能为空'}
        }), 400

    diary_id = str(uuid.uuid4())
    title = data.get('title', '无题')
    content = data.get('content', '')
    tags = data.get('tags')

    if not content:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '日记内容不能为空'}
        }), 400

    mood_result = _analyze_with_custom_words(g.current_user_id, content)

    ai_analysis = current_app.ai_companion.analyze_diary(content, mood_result)

    execute_db('''
    INSERT INTO diaries (id, user_id, title, content, mood_score, mood_label, tags, ai_analysis)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (diary_id, g.current_user_id, title, content, mood_result['mood_score'],
          mood_result['mood_label'], str(tags) if tags else None, ai_analysis))

    record_mood(
        g.current_user_id,
        mood_result,
        source_type='diary',
        source_id=diary_id,
        diary_id=diary_id,
    )

    logger.info(f"Diary created: {diary_id}, mood: {mood_result['mood_label']}, user: {g.current_user_id}")
    return jsonify({
        'success': True,
        'data': {
            'id': diary_id,
            'title': title,
            'mood_score': mood_result['mood_score'],
            'mood_label': mood_result['mood_label']
        }
    })


@diary_bp.route('/api/diaries', methods=['GET'])
@require_auth
def get_diaries():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    q = request.args.get('q', '').strip()
    mood = request.args.get('mood', '').strip()

    where_clauses = ['user_id = ?']
    params = [g.current_user_id]

    if q:
        like_pattern = f'%{_escape_like(q)}%'
        where_clauses.append("(title LIKE ? ESCAPE '\\' OR content LIKE ? ESCAPE '\\')")
        params.append(like_pattern)
        params.append(like_pattern)

    if mood:
        where_clauses.append('mood_label = ?')
        params.append(mood)

    where_sql = ' AND '.join(where_clauses)

    total = query_db(
        f'SELECT COUNT(*) as count FROM diaries WHERE {where_sql}',
        tuple(params), one=True
    )

    rows = query_db(f'''
    SELECT id, title, content, mood_score, mood_label, ai_analysis, created_at
    FROM diaries
    WHERE {where_sql}
    ORDER BY created_at DESC
    LIMIT ? OFFSET ?
    ''', tuple(params + [per_page, (page - 1) * per_page]))

    logger.debug(f"Get diaries: page={page}, total={total['count']}, user={g.current_user_id}")
    return jsonify({
        'success': True,
        'data': {
            'total': total['count'] if total else 0,
            'page': page,
            'per_page': per_page,
            'items': [
                {
                    'id': r['id'],
                    'title': r['title'],
                    'content': r['content'],
                    'mood_score': r['mood_score'],
                    'mood_label': r['mood_label'],
                    'ai_analysis': r['ai_analysis'],
                    'created_at': r['created_at']
                }
                for r in rows
            ]
        }
    })


@diary_bp.route('/api/diaries/<diary_id>', methods=['GET'])
@require_auth
def get_diary(diary_id):
    row = query_db('''
    SELECT id, title, content, mood_score, mood_label, ai_analysis, created_at
    FROM diaries WHERE id = ? AND user_id = ?
    ''', (diary_id, g.current_user_id), one=True)

    if not row:
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '日记不存在'}
        }), 404

    return jsonify({
        'success': True,
        'data': {
            'id': row['id'],
            'title': row['title'],
            'content': row['content'],
            'mood_score': row['mood_score'],
            'mood_label': row['mood_label'],
            'ai_analysis': row['ai_analysis'],
            'created_at': row['created_at']
        }
    })


@diary_bp.route('/api/diaries/<diary_id>', methods=['PUT'])
@require_auth
def update_diary(diary_id):
    data = request.json
    title = data.get('title')
    content = data.get('content')
    tags = data.get('tags')

    existing = query_db(
        'SELECT id FROM diaries WHERE id = ? AND user_id = ?',
        (diary_id, g.current_user_id), one=True
    )
    if not existing:
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '日记不存在'}
        }), 404

    mood_result = None
    ai_analysis = None
    if content:
        mood_result = _analyze_with_custom_words(g.current_user_id, content)
        ai_analysis = current_app.ai_companion.analyze_diary(content, mood_result)

    if mood_result:
        execute_db('''
        UPDATE diaries
        SET title = COALESCE(?, title),
            content = COALESCE(?, content),
            mood_score = ?,
            mood_label = ?,
            tags = COALESCE(?, tags),
            ai_analysis = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
        ''', (title, content, mood_result['mood_score'], mood_result['mood_label'],
              tags, ai_analysis, diary_id, g.current_user_id))
    else:
        execute_db('''
        UPDATE diaries
        SET title = COALESCE(?, title),
            content = COALESCE(?, content),
            tags = COALESCE(?, tags),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
        ''', (title, content, tags, diary_id, g.current_user_id))

    logger.info(f"Diary updated: {diary_id}, user: {g.current_user_id}")
    return jsonify({
        'success': True,
        'data': {
            'id': diary_id,
            'title': title,
            'updated_at': datetime.now().isoformat()
        }
    })


@diary_bp.route('/api/diaries/<diary_id>', methods=['DELETE'])
@require_auth
def delete_diary(diary_id):
    existing = query_db(
        'SELECT id FROM diaries WHERE id = ? AND user_id = ?',
        (diary_id, g.current_user_id), one=True
    )
    if not existing:
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '日记不存在'}
        }), 404

    execute_db('DELETE FROM mood_records WHERE diary_id = ?', (diary_id,))
    execute_db('DELETE FROM diaries WHERE id = ? AND user_id = ?',
              (diary_id, g.current_user_id))

    logger.info(f"Diary deleted: {diary_id}, user: {g.current_user_id}")
    return jsonify({
        'success': True,
        'data': None
    })

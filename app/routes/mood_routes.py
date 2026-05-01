"""
情绪分析 API 路由 (分析、趋势、分布、自定义词库)
"""

import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g, current_app
from ..db import query_db, execute_db
from ..auth import require_auth, _analyze_with_custom_words
from .. import logger

mood_bp = Blueprint('mood', __name__)


@mood_bp.route('/api/mood/analyze', methods=['POST'])
@require_auth
def analyze_text_mood():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '文本不能为空'}
        }), 400

    mood_result = _analyze_with_custom_words(g.current_user_id, text)

    return jsonify({
        'success': True,
        'data': mood_result
    })


@mood_bp.route('/api/mood/trend', methods=['GET'])
@require_auth
def get_mood_trend():
    days = request.args.get('days', 7, type=int)
    days = min(days, 90)

    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    rows = query_db('''
    SELECT mood_score, mood_label, timestamp
    FROM mood_records
    WHERE user_id = ? AND timestamp >= ?
    ORDER BY timestamp DESC
    ''', (g.current_user_id, cutoff))

    logger.info(f"Get mood trend: days={days}, records={len(rows)}, user={g.current_user_id}")
    return jsonify({
        'success': True,
        'data': [
            {
                'score': r['mood_score'],
                'label': r['mood_label'],
                'timestamp': r['timestamp']
            }
            for r in rows
        ]
    })


@mood_bp.route('/api/mood/distribution', methods=['GET'])
@require_auth
def get_mood_distribution():
    days = request.args.get('days', 7, type=int)
    days = min(days, 90)

    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    rows = query_db('''
    SELECT mood_label, COUNT(*) as count
    FROM mood_records
    WHERE user_id = ? AND timestamp >= ?
    GROUP BY mood_label
    ORDER BY count DESC
    ''', (g.current_user_id, cutoff))

    distribution = {r['mood_label']: r['count'] for r in rows}
    all_moods = ['开心', '平静', '中性', '焦虑', '悲伤']
    for mood in all_moods:
        if mood not in distribution:
            distribution[mood] = 0

    return jsonify({
        'success': True,
        'data': distribution
    })


@mood_bp.route('/api/mood/words', methods=['GET'])
@require_auth
def get_custom_words():
    rows = query_db('''
    SELECT id, word, category, word_type, created_at
    FROM custom_words
    WHERE user_id = ?
    ORDER BY created_at DESC
    ''', (g.current_user_id,))

    return jsonify({
        'success': True,
        'data': [
            {
                'id': r['id'],
                'word': r['word'],
                'category': r['category'],
                'word_type': r['word_type'],
                'created_at': r['created_at']
            }
            for r in rows
        ]
    })


@mood_bp.route('/api/mood/words', methods=['POST'])
@require_auth
def add_custom_word():
    data = request.json
    word = data.get('word', '').strip()
    category = data.get('category', '自定义')
    word_type = data.get('word_type', 'positive')

    if not word:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '词语不能为空'}
        }), 400

    if word_type not in ('positive', 'negative'):
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '词语类型必须是 positive 或 negative'}
        }), 400

    existing = query_db(
        'SELECT id FROM custom_words WHERE user_id = ? AND word = ?',
        (g.current_user_id, word), one=True
    )
    if existing:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '该词语已存在'}
        }), 400

    word_id = str(uuid.uuid4())
    execute_db('''
    INSERT INTO custom_words (id, user_id, word, category, word_type)
    VALUES (?, ?, ?, ?, ?)
    ''', (word_id, g.current_user_id, word, category, word_type))

    current_app.mood_analyzer.add_custom_word(word, word_type, category)

    logger.info(f"Custom word added: {word} ({word_type}), user: {g.current_user_id}")
    return jsonify({
        'success': True,
        'data': {
            'id': word_id,
            'word': word,
            'category': category,
            'word_type': word_type
        }
    })


@mood_bp.route('/api/mood/words/<word_id>', methods=['DELETE'])
@require_auth
def delete_custom_word(word_id):
    existing = query_db(
        'SELECT id, word FROM custom_words WHERE id = ? AND user_id = ?',
        (word_id, g.current_user_id), one=True
    )
    if not existing:
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '词语不存在'}
        }), 404

    execute_db('DELETE FROM custom_words WHERE id = ? AND user_id = ?',
              (word_id, g.current_user_id))

    logger.info(f"Custom word deleted: {existing['word']}, user: {g.current_user_id}")
    return jsonify({'success': True, 'data': None})

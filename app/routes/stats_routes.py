"""
统计分析 API 路由
"""

from datetime import datetime, timedelta
from flask import Blueprint, jsonify, g
from ..db import query_db
from ..auth import require_auth

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/api/stats/overview', methods=['GET'])
@require_auth
def get_stats_overview():
    # 合并查询1: 日记总数 + 对话总数
    counts = query_db('''
    SELECT
        (SELECT COUNT(*) FROM diaries WHERE user_id = ?) as diary_count,
        (SELECT COUNT(*) FROM conversations WHERE user_id = ?) as conv_count,
        (SELECT COUNT(*) FROM mood_records WHERE user_id = ?) as mood_count
    ''', (g.current_user_id, g.current_user_id, g.current_user_id), one=True)

    # 合并查询2: 情绪统计（平均分、最常见标签、7天趋势）
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    mood_stats = query_db('''
    SELECT AVG(mood_score) as avg_score,
           mood_label, COUNT(*) as label_count
    FROM mood_records WHERE user_id = ?
    GROUP BY mood_label ORDER BY label_count DESC LIMIT 1
    ''', (g.current_user_id,))

    # 合并查询3: 7天内数据（平均分 + 趋势）
    week_data = query_db('''
    SELECT AVG(mood_score) as avg_score,
           MIN(mood_score) as min_score,
           MAX(mood_score) as max_score,
           COUNT(*) as count
    FROM mood_records
    WHERE user_id = ? AND timestamp >= ?
    ''', (g.current_user_id, week_ago), one=True)

    recent_scores = query_db('''
    SELECT mood_score FROM mood_records
    WHERE user_id = ? AND timestamp >= ?
    ORDER BY timestamp ASC
    ''', (g.current_user_id, week_ago))

    trend = '平稳'
    if recent_scores and len(recent_scores) >= 2:
        scores = [r['mood_score'] for r in recent_scores]
        if scores[-1] > scores[0] + 5:
            trend = '上升'
        elif scores[-1] < scores[0] - 5:
            trend = '下降'

    total_diaries = counts['diary_count'] if counts else 0
    total_moods = counts['mood_count'] if counts else 0
    total_conversations = counts['conv_count'] if counts else 0

    avg_val = mood_stats[0]['avg_score'] if mood_stats else None
    most_common = mood_stats[0] if mood_stats else None

    return jsonify({
        'success': True,
        'data': {
            'total_diaries': total_diaries or 0,
            'total_mood_records': total_moods or 0,
            'total_conversations': total_conversations or 0,
            'avg_mood_score': round(avg_val, 1) if avg_val else 50.0,
            'most_common_mood': most_common['mood_label'] if most_common else '中性',
            'last_7_days': {
                'avg_score': round(week_data['avg_score'], 1) if week_data and week_data['avg_score'] else 50.0,
                'trend': trend
            }
        }
    })

"""
统计分析 API 路由
"""

from datetime import datetime, timedelta
from flask import Blueprint, jsonify, g
from ..db import query_db
from ..auth import require_auth

stats_bp = Blueprint('stats', __name__)


def _round_score(value, default=50.0):
    return round(float(value), 1) if value is not None else default


def _day_payload(row):
    if not row:
        return None
    return {
        'date': row['day'],
        'avg_score': _round_score(row['avg_score'], 0.0),
        'count': row['count'] or 0,
    }


def _streak_days(day_values):
    days = {d for d in day_values if d}
    current = datetime.utcnow().date()
    streak = 0
    while current.isoformat() in days:
        streak += 1
        current = current - timedelta(days=1)
    return streak


def _mood_balance(label_rows):
    balance = {'positive': 0, 'neutral': 0, 'negative': 0}
    positive = {'开心', '平静'}
    negative = {'焦虑', '悲伤'}
    for row in label_rows:
        label = row['mood_label']
        count = row['count'] or 0
        if label in positive:
            balance['positive'] += count
        elif label in negative:
            balance['negative'] += count
        else:
            balance['neutral'] += count
    return balance


def _build_insight(total_moods, avg_score, trend, daily_rows, label_rows):
    active_days = len(daily_rows)
    best_day = _day_payload(max(daily_rows, key=lambda r: r['avg_score']) if daily_rows else None)
    lowest_day = _day_payload(min(daily_rows, key=lambda r: r['avg_score']) if daily_rows else None)
    mood_balance = _mood_balance(label_rows)
    streak = _streak_days([r['day'] for r in daily_rows])

    if total_moods == 0:
        summary = '还没有足够的情绪记录，花园正在等待第一颗种子。'
        suggestion = '今天先写下三句话：发生了什么、你的感受、接下来想怎样照顾自己。'
    elif avg_score >= 70:
        summary = '最近的情绪整体明亮，花园里正在开出很有生命力的花。'
        suggestion = '把让你感觉被点亮的人和事标记下来，以后低落时可以回来取暖。'
    elif avg_score < 40:
        summary = '最近的情绪有些吃力，花园需要一点慢慢的浇水和遮阴。'
        suggestion = '先做一件很小的照顾自己的事：喝水、伸展、散步五分钟，或把压力写下来。'
    else:
        summary = '最近的情绪比较平稳，花园在安静地生长。'
        suggestion = '继续保持记录节奏，试着写下每天一个让你安心的小细节。'

    return {
        'summary': summary,
        'suggestion': suggestion,
        'active_days': active_days,
        'streak_days': streak,
        'best_day': best_day,
        'lowest_day': lowest_day,
        'mood_balance': mood_balance,
        'window_days': 30,
    }


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
    month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
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

    daily_rows = query_db('''
    SELECT date(timestamp) as day,
           AVG(mood_score) as avg_score,
           COUNT(*) as count
    FROM mood_records
    WHERE user_id = ? AND timestamp >= ?
    GROUP BY date(timestamp)
    ORDER BY day ASC
    ''', (g.current_user_id, month_ago))

    label_rows = query_db('''
    SELECT mood_label, COUNT(*) as count
    FROM mood_records
    WHERE user_id = ? AND timestamp >= ?
    GROUP BY mood_label
    ''', (g.current_user_id, month_ago))

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
    avg_score = _round_score(avg_val)

    return jsonify({
        'success': True,
        'data': {
            'total_diaries': total_diaries or 0,
            'total_mood_records': total_moods or 0,
            'total_conversations': total_conversations or 0,
            'avg_mood_score': avg_score,
            'most_common_mood': most_common['mood_label'] if most_common else '中性',
            'last_7_days': {
                'avg_score': _round_score(week_data['avg_score']) if week_data else 50.0,
                'trend': trend
            },
            'insight': _build_insight(total_moods or 0, avg_score, trend, daily_rows, label_rows)
        }
    })

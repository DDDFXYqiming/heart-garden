"""
记忆花园 API 路由
"""

import ast
import math
from datetime import datetime

from flask import Blueprint, jsonify, g
from ..db import query_db
from ..auth import require_auth
from .. import logger

garden_bp = Blueprint('garden', __name__)


THEME_RULES = [
    {
        'key': 'work',
        'label': '工作压力',
        'keywords': ['工作', '项目', '会议', '压力', '加班', '任务', '同事', '客户', '汇报', '考试', '学习'],
    },
    {
        'key': 'relationship',
        'label': '亲密关系',
        'keywords': ['朋友', '家人', '妈妈', '爸爸', '喜欢', '关系', '恋人', '爱', '陪伴', '聊天', '同学'],
    },
    {
        'key': 'growth',
        'label': '自我成长',
        'keywords': ['成长', '坚持', '目标', '计划', '练习', '完成', '进步', '反思', '勇气', '改变'],
    },
    {
        'key': 'rest',
        'label': '休息修复',
        'keywords': ['休息', '睡觉', '疲惫', '累', '放松', '治愈', '安静', '散步', '冥想', '恢复'],
    },
    {
        'key': 'travel',
        'label': '远方见闻',
        'keywords': ['旅行', '出门', '城市', '风景', '公园', '路上', '远方', '车站', '海', '山'],
    },
]

DEFAULT_THEME = {'key': 'daily', 'label': '日常微光', 'keywords': []}


def _stable_seed(value):
    seed = 0
    for char in str(value):
        seed = ((seed << 5) - seed) + ord(char)
        seed &= 0xFFFFFFFF
    return max(1, seed)


def _truncate_preview(content, max_len=64):
    if not content:
        return ''
    return content if len(content) <= max_len else content[:max_len] + '...'


def _parse_tags(tags):
    if not tags:
        return []
    if isinstance(tags, list):
        return tags
    text = str(tags)
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except (SyntaxError, ValueError):
        pass
    return [part.strip() for part in text.replace(',', ' ').split() if part.strip()]


def _parse_date(value):
    if not value:
        return None
    text = str(value).replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return datetime.strptime(str(value)[:10], '%Y-%m-%d')
        except ValueError:
            return None


def _theme_for_row(row):
    text = ' '.join(
        str(value or '') for value in [
            row['title'],
            row['content'],
            row['mood_label'],
            row['ai_analysis'],
            ' '.join(_parse_tags(row['tags'])),
        ]
    )
    for rule in THEME_RULES:
        if any(keyword in text for keyword in rule['keywords']):
            return rule
    return DEFAULT_THEME


def _overview(items):
    if not items:
        return {
            'total_count': 0,
            'avg_score': '0.0',
            'volatility': '0.0',
            'first_date': '',
            'last_date': '',
            'active_days': 0,
        }

    scores = [float(item['mood_score'] or 0) for item in items]
    avg = sum(scores) / len(scores)
    variance = sum((score - avg) ** 2 for score in scores) / len(scores) if len(scores) > 1 else 0
    date_keys = sorted({str(item['created_at'])[:10] for item in items if item.get('created_at')})

    return {
        'total_count': len(items),
        'avg_score': f'{avg:.1f}',
        'volatility': f'{math.sqrt(variance):.1f}',
        'first_date': date_keys[0] if date_keys else '',
        'last_date': date_keys[-1] if date_keys else '',
        'active_days': len(date_keys),
    }


def _themes(items):
    grouped = {}
    for item in items:
        theme = item['theme']
        entry = grouped.setdefault(theme['key'], {
            'key': theme['key'],
            'label': theme['label'],
            'count': 0,
            'score_total': 0,
            'recent_date': '',
        })
        entry['count'] += 1
        entry['score_total'] += float(item['mood_score'] or 0)
        if str(item['created_at']) > entry['recent_date']:
            entry['recent_date'] = str(item['created_at'])

    result = []
    for entry in grouped.values():
        avg = entry['score_total'] / entry['count'] if entry['count'] else 0
        result.append({
            'key': entry['key'],
            'label': entry['label'],
            'count': entry['count'],
            'avg_score': f'{avg:.1f}',
            'recent_date': entry['recent_date'],
            'seed': _stable_seed(f"{entry['key']}:{entry['count']}:{entry['recent_date']}"),
        })

    return sorted(result, key=lambda item: (-item['count'], item['key']))


def _landmark_type(item, anchor_date):
    created_at = _parse_date(item.get('created_at'))
    age_days = (anchor_date - created_at).days if anchor_date and created_at else 0
    score = float(item['mood_score'] or 0)
    content_len = len(item.get('content') or '')

    if score >= 82:
        return 'glowing_tree'
    if age_days >= 30:
        return 'memory_stone'
    if content_len >= 140:
        return 'journal_bench'
    if score <= 28:
        return 'quiet_pond'
    return ''


def _landmarks(items):
    dates = [_parse_date(item.get('created_at')) for item in items]
    anchor_date = max([date for date in dates if date] or [None])
    landmarks = []

    for item in items:
        landmark_type = _landmark_type(item, anchor_date)
        if not landmark_type:
            continue
        landmarks.append({
            'type': landmark_type,
            'source_id': item['id'],
            'title': item['title'],
            'date': item['created_at'],
            'theme': item['theme']['key'],
            'mood_score': item['mood_score'],
        })

    return landmarks[:8]


def _garden_rows(limit=200):
    return query_db('''
    SELECT id, title, content, mood_score, mood_label, tags, ai_analysis, created_at
    FROM diaries
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT ?
    ''', (g.current_user_id, limit))


def _row_to_item(row):
    theme = _theme_for_row(row)
    return {
        'id': row['id'],
        'title': row['title'],
        'content': row['content'],
        'content_preview': _truncate_preview(row['content']),
        'mood_score': row['mood_score'],
        'mood_label': row['mood_label'],
        'tags': _parse_tags(row['tags']),
        'ai_analysis': row['ai_analysis'],
        'created_at': row['created_at'],
        'theme': {'key': theme['key'], 'label': theme['label']},
    }


@garden_bp.route('/api/garden', methods=['GET'])
@require_auth
def get_garden():
    rows = _garden_rows(limit=50)

    logger.info(f"Get garden: {len(rows)} diaries, user: {g.current_user_id}")
    return jsonify({
        'success': True,
        'data': [
            {
                'id': r['id'],
                'title': r['title'],
                'content': r['content'],
                'mood_score': r['mood_score'],
                'mood_label': r['mood_label'],
                'created_at': r['created_at']
            }
            for r in rows
        ]
    })


@garden_bp.route('/api/garden/world', methods=['GET'])
@require_auth
def get_garden_world():
    rows = _garden_rows(limit=200)
    items = [_row_to_item(row) for row in rows]

    logger.info(f"Get garden world: {len(rows)} diaries, user: {g.current_user_id}")
    return jsonify({
        'success': True,
        'data': {
            'items': items,
            'overview': _overview(items),
            'themes': _themes(items),
            'landmarks': _landmarks(items),
        }
    })

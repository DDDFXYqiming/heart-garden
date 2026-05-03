"""
社区服务
社区帖子、点赞、评论相关功能
"""

import sqlite3
from pathlib import Path
from flask import current_app
import uuid


def get_db():
    database_path = Path(current_app.config['DATABASE'])
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_post(user_id: str, content: str, mood_label: str = None, mood_score: float = None, is_anonymous: bool = True) -> str:
    post_id = uuid.uuid4().hex
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO community_posts (id, user_id, content, mood_label, mood_score, is_anonymous)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (post_id, user_id, content, mood_label, mood_score, is_anonymous)
    )

    conn.commit()
    conn.close()
    return post_id


def get_posts(page: int = 1, mood_filter: str = None, per_page: int = 20) -> dict:
    offset = (page - 1) * per_page
    conn = get_db()
    cursor = conn.cursor()

    where_clause = ""
    params = []
    if mood_filter:
        where_clause = "WHERE mood_label = ?"
        params.append(mood_filter)

    cursor.execute(
        f"""SELECT cp.*,
        CASE WHEN cp.is_anonymous = 1 THEN '匿名用户' ELSE
            (SELECT username FROM users WHERE id = cp.user_id)
        END as display_name
        FROM community_posts cp
        {where_clause}
        ORDER BY cp.created_at DESC
        LIMIT ? OFFSET ?""",
        (*params, per_page, offset)
    )
    rows = cursor.fetchall()

    cursor.execute(
        f"SELECT COUNT(*) as total FROM community_posts {where_clause}",
        params
    )
    total = cursor.fetchone()['total']

    conn.close()

    posts = [dict(row) for row in rows]
    return {
        'posts': posts,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }

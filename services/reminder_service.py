"""
智能提醒服务
根据情绪状态自动提醒，提供定期关怀和个性化建议
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from flask import current_app


def get_db():
    """获取数据库连接"""
    database_path = Path(current_app.config['DATABASE'])
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn


def check_mood_alert(user_id: str) -> bool:
    """检查最近3条情绪记录，平均分 < 40 则触发预警"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT AVG(mood_score) as avg_score
        FROM (
            SELECT mood_score
            FROM mood_records
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 3
        )""",
        (user_id,)
    )
    
    result = cursor.fetchone()
    conn.close()
    
    if not result or result['avg_score'] is None:
        return False
    
    return result['avg_score'] < 40


def get_reminder_settings(user_id: str) -> list:
    """获取用户的提醒设置"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM reminder_settings WHERE user_id = ?",
        (user_id,)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return [
            {
                'id': '',
                'user_id': user_id,
                'reminder_type': 'mood_alert',
                'enabled': True,
                'threshold_score': 40.0,
                'quiet_hours_start': '22:00',
                'quiet_hours_end': '08:00',
                'last_sent': None
            },
            {
                'id': '',
                'user_id': user_id,
                'reminder_type': 'daily_care',
                'enabled': True,
                'threshold_score': 0,
                'quiet_hours_start': '22:00',
                'quiet_hours_end': '08:00',
                'last_sent': None
            }
        ]
    
    return [dict(row) for row in rows]


def update_reminder_settings(user_id: str, settings: list) -> bool:
    """更新用户的提醒设置"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM reminder_settings WHERE user_id = ?', (user_id,))
        
        for setting in settings:
            cursor.execute(
                """INSERT INTO reminder_settings (id, user_id, reminder_type, enabled, threshold_score, quiet_hours_start, quiet_hours_end)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    setting.get('id') or __import__('uuid').uuid4().hex,
                    user_id,
                    setting['reminder_type'],
                    setting.get('enabled', True),
                    setting.get('threshold_score', 40.0),
                    setting.get('quiet_hours_start', '22:00'),
                    setting.get('quiet_hours_end', '08:00')
                )
            )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_notifications(user_id: str, page: int = 1, per_page: int = 20, unread_only: bool = False) -> dict:
    """获取用户的通知列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    
    query = 'SELECT * FROM notifications WHERE user_id = ?'
    params = [user_id]
    
    if unread_only:
        query += ' AND is_read = 0'
    
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    cursor.execute(
        "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0",
        (user_id,)
    )
    unread_count = cursor.fetchone()['count']
    
    conn.close()
    
    return {
        'notifications': [dict(row) for row in rows],
        'unread_count': unread_count,
        'page': page,
        'per_page': per_page
    }


def mark_notification_read(notification_id: str, user_id: str) -> bool:
    """标记通知为已读"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
        (notification_id, user_id)
    )
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    return affected > 0


def mark_all_read(user_id: str) -> int:
    """全部标记已读，返回更新的数量"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
        (user_id,)
    )
    
    count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return count


def send_notification(user_id: str, notification_type: str, title: str, content: str) -> str:
    """发送通知（写入数据库）"""
    conn = get_db()
    cursor = conn.cursor()
    
    notification_id = __import__('uuid').uuid4().hex
    
    cursor.execute(
        "INSERT INTO notifications (id, user_id, notification_type, title, content) VALUES (?, ?, ?, ?, ?)",
        (notification_id, user_id, notification_type, title, content)
    )
    
    conn.commit()
    conn.close()
    
    return notification_id


def generate_care_message(user_id: str) -> str:
    """生成关怀消息（复用 ai_companion 或 llm_service）"""
    try:
        from services.ai_companion import AICompanion
        companion = AICompanion()
        return companion.generate_response(
            "我今天情绪不太好，需要一些关心",
            mood="悲伤",
            preferences={'response_style': 'warm', 'use_emoji': True}
        )
    except Exception:
        return "亲爱的，我注意到你最近情绪有些低落。记得照顾好自己，我会一直在这里陪着你。"


def check_and_send_all():
    """检查所有用户并发送提醒（定时任务调用）"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT user_id FROM reminder_settings WHERE enabled = 1")
    users = cursor.fetchall()
    
    for user_row in users:
        user_id = user_row['user_id']
        
        cursor.execute(
            "SELECT quiet_hours_start, quiet_hours_end FROM reminder_settings WHERE user_id = ? AND reminder_type = 'mood_alert' AND enabled = 1",
            (user_id,)
        )
        quiet_time = cursor.fetchone()
        
        if quiet_time:
            now = datetime.now().time()
            start = datetime.strptime(quiet_time['quiet_hours_start'], '%H:%M').time()
            end = datetime.strptime(quiet_time['quiet_hours_end'], '%H:%M').time()
            
            if start <= now <= end:
                continue
        
        if check_mood_alert(user_id):
            cursor.execute(
                "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND notification_type = 'mood_alert' AND DATE(created_at) = DATE('now')",
                (user_id,)
            )
            
            if cursor.fetchone()['count'] == 0:
                message = generate_care_message(user_id)
                send_notification(
                    user_id,
                    'mood_alert',
                    '情绪预警提醒',
                    message
                )
    
    conn.close()

"""
数据库工具模块
"""

import sqlite3
from pathlib import Path
from flask import g, current_app


def get_db():
    if 'db' not in g:
        database_path = Path(current_app.config['DATABASE'])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)
    rows = cursor.fetchall()
    cursor.close()
    return (rows[0] if rows else None) if one else rows


def execute_db(query, args=()):
    db = get_db()
    cursor = db.execute(query, args)
    db.commit()
    return cursor.lastrowid


def init_db():
    from . import logger, DEV_MODE

    try:
        database_path = Path(current_app.config['DATABASE'])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(current_app.config['DATABASE'])
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS diaries (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            mood_score REAL,
            mood_label TEXT,
            tags TEXT,
            ai_analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mood_records (
            id TEXT PRIMARY KEY,
            diary_id TEXT,
            mood_score REAL,
            mood_label TEXT,
            keywords TEXT,
            trend TEXT,
            source_type TEXT DEFAULT 'diary',
            source_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (diary_id) REFERENCES diaries(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT DEFAULT '新对话',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            mood_label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_words (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            word TEXT NOT NULL,
            category TEXT NOT NULL,
            word_type TEXT NOT NULL CHECK(word_type IN ('positive', 'negative')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')

        _ALLOWED_TABLES = {'diaries', 'mood_records', 'users'}
        for table, column, col_def in [
            ('diaries', 'user_id', 'TEXT'),
            ('mood_records', 'user_id', 'TEXT'),
            ('mood_records', 'source_type', "TEXT DEFAULT 'diary'"),
            ('mood_records', 'source_id', 'TEXT'),
            ('users', 'llm_config', 'TEXT')
        ]:
            if table not in _ALLOWED_TABLES:
                raise ValueError(f"禁止迁移未知表: {table}")
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {col_def}')
            except sqlite3.OperationalError:
                pass

        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_diaries_user_id ON diaries(user_id)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_diaries_created_at ON diaries(created_at)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_mood_records_user_id ON mood_records(user_id)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_mood_records_timestamp ON mood_records(timestamp)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_mood_records_source ON mood_records(source_type, source_id)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_chat_history_conversation ON chat_history(conversation_id)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_custom_words_user ON custom_words(user_id)
        ''')

        if DEV_MODE:
            cursor.execute('''
            INSERT OR IGNORE INTO users (id, username, email, password_hash)
            VALUES ('dev-user', '开发用户', 'dev@heart-garden.local', 'dev-mode-no-auth')
            ''')

        # 提醒设置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminder_settings (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            reminder_type TEXT NOT NULL CHECK(reminder_type IN ('mood_alert', 'daily_care', 'weekly_summary')),
            enabled BOOLEAN DEFAULT 1,
            threshold_score REAL DEFAULT 25.0,
            quiet_hours_start TIME DEFAULT '22:00',
            quiet_hours_end TIME DEFAULT '08:00',
            last_sent TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')

        # 通知记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')

        # 提醒相关索引
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_reminder_settings_user ON reminder_settings(user_id)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read)
        ''')

        conn.commit()
        conn.close()
        logger.debug("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

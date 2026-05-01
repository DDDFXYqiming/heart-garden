"""
心语花园 - Heart Garden
AI 驱动的情感陪伴应用

Author: 林溪 (你的专属 AI 伴侣)
Created: 2026.04.28
"""

from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from logging.handlers import RotatingFileHandler
import uuid
from functools import wraps
from services.mood_analyzer import MoodAnalyzer
from services.ai_companion import AICompanion
from services.llm_service import LLMService, parse_llm_config, serialize_llm_config
from services.prompt_engine import MoodContext
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = Path(os.getenv('STATIC_DIR', APP_DIR / 'static'))

# ==================== 日志配置 ====================
def setup_logging():
    log_dir = Path(os.getenv('LOG_DIR', BASE_DIR / 'logs'))
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / 'heart_garden.log'

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    logger.setLevel(log_level)
    logger.addHandler(file_handler)

    return logger

logger = setup_logging()

# ==================== Flask 应用初始化 ====================
app = Flask(__name__, static_folder=None)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['DATABASE'] = os.getenv('DATABASE_PATH', 'heart_garden.db')
app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET')
if not app.config['JWT_SECRET']:
    raise ValueError("JWT_SECRET 环境变量未设置！请设置一个安全的随机字符串。")
app.config['JWT_EXPIRATION_HOURS'] = 168

# 开发模式：仅当显式设置 DEV_MODE=true 时启用
# 开启后不需要 token 即可访问所有接口
DEV_MODE = os.getenv('DEV_MODE', '').lower() in ('1', 'true', 'yes')

mood_analyzer = MoodAnalyzer()
ai_companion = AICompanion()
llm_service = LLMService()

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://"
)

# ==================== 数据库工具 ====================
def get_db():
    if 'db' not in g:
        database_path = Path(app.config['DATABASE'])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(app.config['DATABASE'])
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

app.teardown_appcontext(close_db)

# ==================== JWT 工具 ====================
import jwt as pyjwt

def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=app.config['JWT_EXPIRATION_HOURS']),
        'iat': datetime.utcnow()
    }
    return pyjwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')

def verify_token(token):
    try:
        payload = pyjwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload['user_id']
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            user_id = verify_token(token)
            if user_id:
                g.current_user_id = user_id
                return f(*args, **kwargs)
        if DEV_MODE:
            g.current_user_id = 'dev-user'
            return f(*args, **kwargs)
        if not token:
            return jsonify({
                'success': False,
                'error': {'code': 401, 'message': '未提供认证令牌'}
            }), 401
        return jsonify({
            'success': False,
            'error': {'code': 401, 'message': '令牌无效或已过期'}
        }), 401
    return decorated

def _error_details(msg: str) -> str | None:
    """Return detailed error info only in debug/dev mode."""
    return msg if app.debug or DEV_MODE else None


def _analyze_with_custom_words(user_id, text):
    """Query custom_words from DB and analyze text with them."""
    rows = query_db(
        'SELECT word, word_type FROM custom_words WHERE user_id = ?',
        (user_id,)
    )
    return mood_analyzer.analyze(
        text,
        custom_words=[{'word': w['word'], 'type': w['word_type']} for w in rows]
    )


# ==================== 统一错误处理 ====================
@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"Bad request: {error}")
    return jsonify({
        'success': False,
        'error': {'code': 400, 'message': '请求参数错误',
                  'details': _error_details(str(error))}
    }), 400

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"Not found: {error}")
    return jsonify({
        'success': False,
        'error': {'code': 404, 'message': '资源不存在',
                  'details': _error_details(str(error))}
    }), 404

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': {'code': 401, 'message': '未授权访问'}
    }), 401

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}", exc_info=True)
    return jsonify({
        'success': False,
        'error': {'code': 500, 'message': '服务器内部错误',
                  'details': _error_details('请稍后重试')}
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.exception(f"Unhandled exception: {error}")
    return jsonify({
        'success': False,
        'error': {'code': 500, 'message': '服务器内部错误',
                  'details': _error_details(str(error))}
    }), 500

# ==================== 数据库初始化 ====================
def init_db():
    try:
        database_path = Path(app.config['DATABASE'])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(app.config['DATABASE'])
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

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# ==================== 认证 API ====================
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '请求体不能为空'}
        }), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '用户名、邮箱和密码不能为空'}
        }), 400

    if len(username) < 2 or len(username) > 50:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '用户名长度需要在 2-50 个字符之间'}
        }), 400

    if len(password) < 6:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '密码长度不能少于 6 个字符'}
        }), 400

    existing = query_db('SELECT id FROM users WHERE username = ? OR email = ?',
                      (username, email), one=True)
    if existing:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '用户名或邮箱已被注册'}
        }), 400

    user_id = str(uuid.uuid4())
    password_hash = generate_password_hash(password)

    execute_db('''
    INSERT INTO users (id, username, email, password_hash)
    VALUES (?, ?, ?, ?)
    ''', (user_id, username, email, password_hash))

    token = create_token(user_id)

    logger.info(f"User registered: {username}")
    return jsonify({
        'success': True,
        'data': {
            'user_id': user_id,
            'username': username,
            'email': email,
            'token': token
        }
    })

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '请求体不能为空'}
        }), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not password:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '密码不能为空'}
        }), 400

    if not username and not email:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '用户名或邮箱不能为空'}
        }), 400

    user = query_db(
        'SELECT id, username, email, password_hash FROM users WHERE username = ? OR email = ?',
        (username or email, email or username), one=True
    )

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({
            'success': False,
            'error': {'code': 401, 'message': '用户名或密码错误'}
        }), 401

    token = create_token(user['id'])

    logger.info(f"User logged in: {user['username']}")
    return jsonify({
        'success': True,
        'data': {
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'token': token
        }
    })

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    user = query_db(
        'SELECT id, username, email, created_at FROM users WHERE id = ?',
        (g.current_user_id,), one=True
    )
    if not user:
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '用户不存在'}
        }), 404

    diary_count = query_db(
        'SELECT COUNT(*) as count FROM diaries WHERE user_id = ?',
        (g.current_user_id,), one=True
    )

    return jsonify({
        'success': True,
        'data': {
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at'],
            'diary_count': diary_count['count'] if diary_count else 0
        }
    })

# ==================== LLM 配置 API ====================
@app.route('/api/llm/config', methods=['GET'])
@require_auth
def get_llm_config():
    user = query_db(
        'SELECT llm_config FROM users WHERE id = ?',
        (g.current_user_id,), one=True
    )
    config = parse_llm_config(user['llm_config'] if user else None)
    safe_config = dict(config)
    if safe_config.get('api_key'):
        key = safe_config['api_key']
        safe_config['api_key'] = key[:8] + '****' if len(key) > 8 else '****'
    return jsonify({'success': True, 'data': safe_config})

@app.route('/api/llm/config', methods=['POST'])
@require_auth
def save_llm_config():
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '请求体不能为空'}
        }), 400

    config = {
        "enabled": bool(data.get("enabled", False)),
        "base_url": (data.get("base_url") or "").strip(),
        "api_key": (data.get("api_key") or "").strip(),
        "model": (data.get("model") or "deepseek-chat").strip(),
        "temperature": float(data.get("temperature", 0.7))
    }

    if config["enabled"]:
        if not config["base_url"]:
            return jsonify({
                'success': False,
                'error': {'code': 400, 'message': 'API 基础 URL 不能为空'}
            }), 400
        if not config["api_key"]:
            return jsonify({
                'success': False,
                'error': {'code': 400, 'message': 'API Key 不能为空'}
            }), 400

    config_json = serialize_llm_config(config)
    execute_db(
        'UPDATE users SET llm_config = ? WHERE id = ?',
        (config_json, g.current_user_id)
    )

    llm_service.clear_cache()

    logger.info(f"LLM config saved for user: {g.current_user_id}, enabled: {config['enabled']}")
    return jsonify({'success': True, 'data': config})

@app.route('/api/llm/test', methods=['POST'])
@require_auth
def test_llm_connection():
    data = request.json
    config = {
        "enabled": True,
        "base_url": (data.get("base_url") or "").strip(),
        "api_key": (data.get("api_key") or "").strip(),
        "model": (data.get("model") or "deepseek-chat").strip(),
        "temperature": 0.7
    }

    result = llm_service.test_connection(config)
    return jsonify({'success': True, 'data': result})

# ==================== 日记 API ====================
@app.route('/api/diaries', methods=['POST'])
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

    ai_analysis = ai_companion.analyze_diary(content, mood_result)

    execute_db('''
    INSERT INTO diaries (id, user_id, title, content, mood_score, mood_label, tags, ai_analysis)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (diary_id, g.current_user_id, title, content, mood_result['mood_score'],
          mood_result['mood_label'], str(tags) if tags else None, ai_analysis))

    execute_db('''
    INSERT INTO mood_records (id, diary_id, user_id, mood_score, mood_label, keywords, trend)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (diary_id, diary_id, g.current_user_id, mood_result['mood_score'],
          mood_result['mood_label'], str(mood_result['keywords']), mood_result['trend']))

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

@app.route('/api/diaries', methods=['GET'])
@require_auth
def get_diaries():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    total = query_db(
        'SELECT COUNT(*) as count FROM diaries WHERE user_id = ?',
        (g.current_user_id,), one=True
    )

    rows = query_db('''
    SELECT id, title, content, mood_score, mood_label, ai_analysis, created_at
    FROM diaries
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT ? OFFSET ?
    ''', (g.current_user_id, per_page, (page - 1) * per_page))

    logger.info(f"Get diaries: page={page}, total={total['count']}, user={g.current_user_id}")
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

@app.route('/api/diaries/<diary_id>', methods=['GET'])
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

@app.route('/api/diaries/<diary_id>', methods=['PUT'])
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
        ai_analysis = ai_companion.analyze_diary(content, mood_result)

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

@app.route('/api/diaries/<diary_id>', methods=['DELETE'])
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

# ==================== 对话 API ====================
@app.route('/api/conversations', methods=['POST'])
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

@app.route('/api/conversations', methods=['GET'])
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

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
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

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
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
    execute_db('DELETE FROM conversations WHERE id = ? AND user_id = ?',
              (conversation_id, g.current_user_id))

    return jsonify({'success': True, 'data': None})

# ==================== AI 对话 API ====================
@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    data = request.json
    user_message = data.get('message', '')
    conversation_id = data.get('conversation_id')

    if not user_message:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '消息不能为空'}
        }), 400

    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        execute_db('''
        INSERT INTO conversations (id, user_id, title)
        VALUES (?, ?, ?)
        ''', (conversation_id, g.current_user_id, user_message[:50]))
    else:
        conv = query_db(
            'SELECT id FROM conversations WHERE id = ? AND user_id = ?',
            (conversation_id, g.current_user_id), one=True
        )
        if not conv:
            return jsonify({
                'success': False,
                'error': {'code': 404, 'message': '对话不存在'}
            }), 404

    message_id = str(uuid.uuid4())
    execute_db('''
    INSERT INTO chat_history (id, conversation_id, role, content)
    VALUES (?, ?, 'user', ?)
    ''', (message_id, conversation_id, user_message))

    history = query_db('''
    SELECT role, content FROM chat_history
    WHERE conversation_id = ?
    ORDER BY created_at ASC
    ''', (conversation_id,))

    history_list = [{'role': h['role'], 'content': h['content']} for h in history]

    mood_result = _analyze_with_custom_words(g.current_user_id, user_message)

    user_row = query_db(
        'SELECT llm_config FROM users WHERE id = ?',
        (g.current_user_id,), one=True
    )
    user_llm_config = parse_llm_config(
        user_row['llm_config'] if user_row else None
    )

    response_mode = "rule_engine"
    response = None

    if llm_service.is_llm_configured(user_llm_config):
        mood_ctx = MoodContext(
            mood_label=mood_result['mood_label'],
            mood_score=mood_result['mood_score'],
            keywords=mood_result.get('keywords', [])
        )
        llm_success, llm_response, source = llm_service.chat_with_fallback(
            user_message=user_message,
            conversation_history=history_list,
            mood_context=mood_ctx,
            user_config=user_llm_config
        )
        if llm_success:
            response = llm_response
            response_mode = "llm"

    if response is None:
        response = ai_companion.generate_response(
            user_message,
            history=history_list,
            mood=mood_result['mood_label']
        )
        response_mode = "rule_engine"

    response_id = str(uuid.uuid4())
    execute_db('''
    INSERT INTO chat_history (id, conversation_id, role, content, mood_label)
    VALUES (?, ?, 'assistant', ?, ?)
    ''', (response_id, conversation_id, response, mood_result['mood_label']))

    if len(history) <= 2:
        execute_db('''
        UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
        ''', (user_message[:50], conversation_id, g.current_user_id))
    else:
        execute_db('''
        UPDATE conversations SET updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
        ''', (conversation_id, g.current_user_id))

    logger.info(f"Chat: {len(user_message)} chars, mode={response_mode}, conv={conversation_id}")
    return jsonify({
        'success': True,
        'data': {
            'response': response,
            'conversation_id': conversation_id,
            'mood': mood_result['mood_label'],
            'sentiment': 'positive' if mood_result['mood_score'] >= 60 else 'negative' if mood_result['mood_score'] < 40 else 'neutral',
            'response_mode': response_mode
        }
    })

@app.route('/api/chat/stream', methods=['POST'])
@require_auth
def chat_stream():
    data = request.json
    user_message = data.get('message', '')
    conversation_id = data.get('conversation_id')

    if not user_message:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '消息不能为空'}
        }), 400

    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        execute_db('''
        INSERT INTO conversations (id, user_id, title)
        VALUES (?, ?, ?)
        ''', (conversation_id, g.current_user_id, user_message[:50]))
    else:
        conv = query_db(
            'SELECT id FROM conversations WHERE id = ? AND user_id = ?',
            (conversation_id, g.current_user_id), one=True
        )
        if not conv:
            return jsonify({
                'success': False,
                'error': {'code': 404, 'message': '对话不存在'}
            }), 404

    execute_db('''
    INSERT INTO chat_history (id, conversation_id, role, content)
    VALUES (?, ?, 'user', ?)
    ''', (str(uuid.uuid4()), conversation_id, user_message))

    history = query_db('''
    SELECT role, content FROM chat_history
    WHERE conversation_id = ?
    ORDER BY created_at ASC
    ''', (conversation_id,))
    history_list = [{'role': h['role'], 'content': h['content']} for h in history]

    mood_result = _analyze_with_custom_words(g.current_user_id, user_message)

    user_row = query_db(
        'SELECT llm_config FROM users WHERE id = ?',
        (g.current_user_id,), one=True
    )
    user_llm_config = parse_llm_config(
        user_row['llm_config'] if user_row else None
    )

    def generate():
        full_response = []
        response_mode = "rule_engine"

        if llm_service.is_llm_configured(user_llm_config):
            response_mode = "llm"
            mood_ctx = MoodContext(
                mood_label=mood_result['mood_label'],
                mood_score=mood_result['mood_score'],
                keywords=mood_result.get('keywords', [])
            )
            try:
                for chunk in llm_service.chat_stream(
                    user_message=user_message,
                    conversation_history=history_list,
                    mood_context=mood_ctx,
                    user_config=user_llm_config
                ):
                    full_response.append(chunk)
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"Stream error: {e}")
                response_mode = "rule_engine"

        if not full_response:
            response_mode = "rule_engine"
            response = ai_companion.generate_response(
                user_message, history=history_list, mood=mood_result['mood_label']
            )
            full_response = [response]
            yield f"data: {json.dumps({'type': 'chunk', 'content': response}, ensure_ascii=False)}\n\n"

        final_text = ''.join(full_response)
        execute_db('''
        INSERT INTO chat_history (id, conversation_id, role, content, mood_label)
        VALUES (?, ?, 'assistant', ?, ?)
        ''', (str(uuid.uuid4()), conversation_id, final_text, mood_result['mood_label']))

        if len(history) <= 2:
            execute_db('''
            UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            ''', (user_message[:50], conversation_id, g.current_user_id))
        else:
            execute_db('''
            UPDATE conversations SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            ''', (conversation_id, g.current_user_id))

        meta = {
            'type': 'done',
            'conversation_id': conversation_id,
            'mood': mood_result['mood_label'],
            'response_mode': response_mode
        }
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )

# ==================== 情绪分析 API ====================
@app.route('/api/mood/analyze', methods=['POST'])
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

@app.route('/api/mood/trend', methods=['GET'])
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

@app.route('/api/mood/distribution', methods=['GET'])
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

# ==================== 统计分析 API ====================
@app.route('/api/stats/overview', methods=['GET'])
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

    total_diaries = counts
    total_moods = counts
    total_conversations = counts
    avg_score = {'avg': mood_stats[0]['avg_score'] if mood_stats else None} if mood_stats else None
    most_common = mood_stats[0] if mood_stats else None
    last_7_days = week_data

    return jsonify({
        'success': True,
        'data': {
            'total_diaries': total_diaries['count'] if total_diaries else 0,
            'total_mood_records': total_moods['count'] if total_moods else 0,
            'total_conversations': total_conversations['count'] if total_conversations else 0,
            'avg_mood_score': round(avg_score['avg'], 1) if avg_score and avg_score['avg'] else 50.0,
            'most_common_mood': most_common['mood_label'] if most_common else '中性',
            'last_7_days': {
                'avg_score': round(last_7_days['avg_score'], 1) if last_7_days and last_7_days['avg_score'] else 50.0,
                'trend': trend
            }
        }
    })

# ==================== 自定义词库 API ====================
@app.route('/api/mood/words', methods=['GET'])
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

@app.route('/api/mood/words', methods=['POST'])
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

    mood_analyzer.add_custom_word(word, word_type, category)

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

@app.route('/api/mood/words/<word_id>', methods=['DELETE'])
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

# ==================== 记忆花园 API ====================
@app.route('/api/garden', methods=['GET'])
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

# ==================== API 信息 ====================
@app.route('/api/info', methods=['GET'])
def api_info():
    return jsonify({
        'success': True,
        'data': {
            'name': 'Heart Garden - 心语花园',
            'version': '2.2.0',
            'description': 'AI 驱动的情感陪伴应用 - 大模型混合模式',
            'endpoints': {
                'auth': {
                    'register': 'POST /api/auth/register',
                    'login': 'POST /api/auth/login',
                    'me': 'GET /api/auth/me'
                },
                'llm': {
                    'config_get': 'GET /api/llm/config',
                    'config_save': 'POST /api/llm/config',
                    'test': 'POST /api/llm/test'
                },
                'diaries': {
                    'list': 'GET /api/diaries',
                    'create': 'POST /api/diaries',
                    'update': 'PUT /api/diaries/:id',
                    'delete': 'DELETE /api/diaries/:id'
                },
                'mood': {
                    'analyze': 'POST /api/mood/analyze',
                    'trend': 'GET /api/mood/trend',
                    'distribution': 'GET /api/mood/distribution'
                },
                'chat': {
                    'talk': 'POST /api/chat',
                    'conversations': 'GET /api/conversations'
                },
                'stats': {
                    'overview': 'GET /api/stats/overview'
                },
                'words': {
                    'list': 'GET /api/mood/words',
                    'add': 'POST /api/mood/words',
                    'delete': 'DELETE /api/mood/words/:id'
                },
                'garden': 'GET /api/garden',
                'health': 'GET /api/health'
            }
        }
    })

# ==================== 健康检查 ====================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'ok': True,
        'success': True,
        'data': {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.2.0'
        }
    })

# ==================== 前端静态文件 ====================
@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def serve_spa(path):
    if path.startswith('api/'):
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '资源不存在'}
        }), 404

    requested_path = STATIC_DIR / path if path else STATIC_DIR / 'index.html'
    if path and requested_path.is_file():
        return send_from_directory(str(STATIC_DIR), path)

    index_path = STATIC_DIR / 'index.html'
    if index_path.is_file():
        return send_from_directory(str(STATIC_DIR), 'index.html')

    return jsonify({
        'success': True,
        'data': {
            'name': 'Heart Garden - 心语花园',
            'version': '2.2.0',
            'description': '前端静态文件尚未构建，请运行 npm --prefix frontend run build。'
        }
    })

# ==================== 启动 ====================
if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', '5000'))
        debug = os.getenv('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
        init_db()
        logger.info("=== 心语花园 v2.2 已启动 ===")
        logger.info(f"=== API: http://0.0.0.0:{port} ===")
        print("=== 心语花园 v2.2 已启动 ===")
        print(f"=== API: http://0.0.0.0:{port} ===")
        app.run(debug=debug, host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

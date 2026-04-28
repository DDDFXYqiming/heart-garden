"""
心语花园 - Heart Garden
AI 驱动的情感陪伴应用

Author: 林溪 (你的专属 AI 伴侣)
Created: 2026.04.28
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler
from services.mood_analyzer import MoodAnalyzer
from services.ai_companion import AICompanion

# ==================== 日志配置 ====================
def setup_logging():
    """配置日志系统"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'heart_garden.log')
    
    # 创建日志处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # 获取根日志器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    return logger

# 初始化日志
logger = setup_logging()

# ==================== Flask 应用初始化 ====================
app = Flask(__name__)
CORS(app)

# 配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['DATABASE'] = os.getenv('DATABASE_PATH', 'heart_garden.db')

# 初始化服务
mood_analyzer = MoodAnalyzer()
ai_companion = AICompanion()

# ==================== 统一错误处理 ====================
@app.errorhandler(400)
def bad_request(error):
    """400 错误处理"""
    logger.warning(f"Bad request: {error}")
    return jsonify({
        'success': False,
        'error': {
            'code': 400,
            'message': '请求参数错误',
            'details': str(error)
        }
    }), 400

@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    logger.warning(f"Not found: {error}")
    return jsonify({
        'success': False,
        'error': {
            'code': 404,
            'message': '资源不存在',
            'details': str(error)
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    logger.error(f"Internal error: {error}", exc_info=True)
    return jsonify({
        'success': False,
        'error': {
            'code': 500,
            'message': '服务器内部错误',
            'details': '请稍后重试'
        }
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """通用异常处理"""
    logger.exception(f"Unhandled exception: {error}")
    return jsonify({
        'success': False,
        'error': {
            'code': 500,
            'message': '服务器内部错误',
            'details': str(error)
        }
    }), 500

# ==================== 数据库初始化 ====================
def init_db():
    """初始化数据库"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # 创建日记表
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
        
        # 创建情绪记录表
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
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# ==================== API 路由 ====================
@app.route('/api/diaries', methods=['POST'])
def create_diary():
    """创建新日记"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': {'code': 400, 'message': '请求体不能为空'}
            }), 400
        
        diary_id = datetime.now().isoformat()
        title = data.get('title', '无题')
        content = data.get('content', '')
        
        if not content:
            return jsonify({
                'success': False,
                'error': {'code': 400, 'message': '日记内容不能为空'}
            }), 400
        
        # 分析情绪
        mood_result = mood_analyzer.analyze(content)
        
        # AI 分析
        ai_analysis = ai_companion.analyze_diary(content, mood_result)
        
        # 保存到数据库
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO diaries (id, title, content, mood_score, mood_label, ai_analysis)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (diary_id, title, content, mood_result['mood_score'], 
              mood_result['mood_label'], ai_analysis))
        
        # 创建情绪记录
        cursor.execute('''
        INSERT INTO mood_records (id, diary_id, mood_score, mood_label, keywords, trend)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (diary_id, diary_id, mood_result['mood_score'], mood_result['mood_label'],
              str(mood_result['keywords']), mood_result['trend']))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Diary created: {diary_id}, mood: {mood_result['mood_label']}")
        
        return jsonify({
            'success': True,
            'data': {
                'id': diary_id,
                'title': title,
                'mood_score': mood_result['mood_score'],
                'mood_label': mood_result['mood_label']
            }
        })
    except Exception as e:
        logger.error(f"Create diary failed: {e}")
        raise

@app.route('/api/diaries', methods=['GET'])
def get_diaries():
    """获取日记列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # 获取总数
        cursor.execute('SELECT COUNT(*) FROM diaries')
        total = cursor.fetchone()[0]
        
        cursor.execute('''
        SELECT id, title, content, mood_score, mood_label, ai_analysis, created_at
        FROM diaries
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        ''', (per_page, (page - 1) * per_page))
        
        diaries = cursor.fetchall()
        conn.close()
        
        logger.info(f"Get diaries: page={page}, total={total}")
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'items': [
                    {
                        'id': d[0],
                        'title': d[1],
                        'content': d[2],
                        'mood_score': d[3],
                        'mood_label': d[4],
                        'ai_analysis': d[5],
                        'created_at': d[6]
                    }
                    for d in diaries
                ]
            }
        })
    except Exception as e:
        logger.error(f"Get diaries failed: {e}")
        raise

@app.route('/api/diaries/<diary_id>', methods=['PUT'])
def update_diary(diary_id):
    """更新日记"""
    try:
        data = request.json
        
        title = data.get('title')
        content = data.get('content')
        tags = data.get('tags')
        
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # 检查日记是否存在
        cursor.execute('SELECT id FROM diaries WHERE id = ?', (diary_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'error': {'code': 404, 'message': '日记不存在'}
            }), 404
        
        # 如果内容更新了，重新分析情绪
        mood_result = None
        ai_analysis = None
        if content:
            mood_result = mood_analyzer.analyze(content)
            ai_analysis = ai_companion.analyze_diary(content, mood_result)
        
        # 更新日记
        if mood_result:
            cursor.execute('''
            UPDATE diaries 
            SET title = COALESCE(?, title),
                content = COALESCE(?, content),
                mood_score = ?,
                mood_label = ?,
                tags = COALESCE(?, tags),
                ai_analysis = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (title, content, mood_result['mood_score'], mood_result['mood_label'],
                  tags, ai_analysis, diary_id))
        else:
            cursor.execute('''
            UPDATE diaries 
            SET title = COALESCE(?, title),
                content = COALESCE(?, content),
                tags = COALESCE(?, tags),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (title, content, tags, diary_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Diary updated: {diary_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'id': diary_id,
                'title': title,
                'updated_at': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Update diary failed: {e}")
        raise

@app.route('/api/diaries/<diary_id>', methods=['DELETE'])
def delete_diary(diary_id):
    """删除日记"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # 检查日记是否存在
        cursor.execute('SELECT id FROM diaries WHERE id = ?', (diary_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'error': {'code': 404, 'message': '日记不存在'}
            }), 404
        
        # 删除关联的情绪记录
        cursor.execute('DELETE FROM mood_records WHERE diary_id = ?', (diary_id,))
        
        # 删除日记
        cursor.execute('DELETE FROM diaries WHERE id = ?', (diary_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Diary deleted: {diary_id}")
        
        return jsonify({
            'success': True,
            'data': None
        })
    except Exception as e:
        logger.error(f"Delete diary failed: {e}")
        raise

@app.route('/api/mood/trend', methods=['GET'])
def get_mood_trend():
    """获取情绪趋势"""
    try:
        days = request.args.get('days', 7, type=int)
        
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT mood_score, mood_label, timestamp
        FROM mood_records
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (days,))
        
        records = cursor.fetchall()
        conn.close()
        
        logger.info(f"Get mood trend: days={days}, records={len(records)}")
        
        return jsonify({
            'success': True,
            'data': [
                {
                    'score': r[0],
                    'label': r[1],
                    'timestamp': r[2]
                }
                for r in records
            ]
        })
    except Exception as e:
        logger.error(f"Get mood trend failed: {e}")
        raise

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI 对话"""
    try:
        data = request.json
        
        user_message = data.get('message', '')
        context = data.get('context', {})
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': {'code': 400, 'message': '消息不能为空'}
            }), 400
        
        response = ai_companion.generate_response(
            user_message,
            context=context,
            mood='neutral'  # 可从数据库获取当前情绪
        )
        
        logger.info(f"Chat message processed: {len(user_message)} chars")
        
        return jsonify({
            'success': True,
            'data': {
                'response': response
            }
        })
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise

@app.route('/api/garden', methods=['GET'])
def get_garden():
    """获取记忆花园"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, title, content, mood_score, created_at
        FROM diaries
        ORDER BY created_at DESC
        LIMIT 50
        ''')
        
        diaries = cursor.fetchall()
        conn.close()
        
        logger.info(f"Get garden: {len(diaries)} diaries")
        
        return jsonify({
            'success': True,
            'data': [
                {
                    'id': d[0],
                    'title': d[1],
                    'content': d[2],
                    'mood_score': d[3],
                    'created_at': d[4]
                }
                for d in diaries
            ]
        })
    except Exception as e:
        logger.error(f"Get garden failed: {e}")
        raise

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }
    })

# ==================== 启动 ====================

if __name__ == '__main__':
    try:
        init_db()
        logger.info("💕 心语花园已启动...")
        logger.info("🌸 等待你的心事绽放...")
        print("💕 心语花园已启动...")
        print("🌸 等待你的心事绽放...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

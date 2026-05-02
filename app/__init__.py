"""
心语花园 - Heart Garden
AI 驱动的情感陪伴应用

Flask application factory.
"""

import logging
import os
import sys
import time
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, g, has_request_context, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = Path(os.getenv('STATIC_DIR', APP_DIR / 'static'))
IS_TESTING = 'pytest' in sys.modules

# Limiter instance — created at module level so route blueprints can import it
limiter = Limiter(key_func=get_remote_address, enabled=not IS_TESTING)


class RequestIdFilter(logging.Filter):
    """Inject current request id into every log record."""

    def filter(self, record):
        if has_request_context():
            record.request_id = getattr(g, 'request_id', '-')
        else:
            record.request_id = '-'
        return True


def setup_logging():
    """Configure file + stdout logging.

    File logs are useful locally; stdout logs are required for Zeabur/Docker
    Runtime Logs. The function is idempotent to avoid duplicated logs when the
    Flask app is imported more than once by tests or reloaders.
    """
    root_logger = logging.getLogger()
    log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    root_logger.setLevel(log_level)

    if getattr(root_logger, '_heart_garden_configured', False):
        return root_logger

    log_dir = Path(os.getenv('LOG_DIR', BASE_DIR / 'logs'))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'heart_garden.log'

    request_filter = RequestIdFilter()
    formatter = logging.Formatter(
        '%(asctime)s [%(request_id)s] %(levelname)-7s %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(request_filter)

    # stdout handler — Zeabur / Docker / terminal visible
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(request_filter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
    root_logger._heart_garden_configured = True

    root_logger.info(
        'logging initialized stdout=true file=%s level=%s',
        log_file,
        logging.getLevelName(log_level)
    )
    return root_logger


logger = setup_logging()

# 开发模式：仅当显式设置 DEV_MODE=true 时启用
# 开启后不需要 token 即可访问所有接口
DEV_MODE = (
    os.getenv('DEV_MODE', '').lower() in ('1', 'true', 'yes')
    and not IS_TESTING
)


def create_app():
    app = Flask(__name__, static_folder=None)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['DATABASE'] = os.getenv('DATABASE_PATH', 'heart_garden.db')
    app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET')
    if not app.config['JWT_SECRET']:
        raise ValueError("JWT_SECRET 环境变量未设置！请设置一个安全的随机字符串。")
    app.config['JWT_EXPIRATION_HOURS'] = 168

    CORS(app)

    # Import services
    from services.mood_analyzer import MoodAnalyzer
    from services.ai_companion import AICompanion
    from services.llm_service import LLMService

    app.mood_analyzer = MoodAnalyzer()
    app.ai_companion = AICompanion()
    app.llm_service = LLMService()

    # Initialize limiter with the app
    limiter.init_app(app)
    app.limiter = limiter

    # Request-level logging middleware
    @app.before_request
    def _before_request():
        g.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex[:8]
        g.request_start = time.perf_counter()

    @app.after_request
    def _after_request(response):
        duration_ms = (time.perf_counter() - getattr(g, 'request_start', time.perf_counter())) * 1000
        user_id = getattr(g, 'current_user_id', '-')
        req_id = getattr(g, 'request_id', '-')
        status = response.status_code
        level = logging.WARNING if status >= 400 else logging.INFO

        response.headers['X-Request-ID'] = req_id
        logger.log(
            level,
            'request method=%s path=%s status=%s duration_ms=%.1f user=%s remote=%s',
            request.method,
            request.path,
            status,
            duration_ms,
            user_id,
            request.remote_addr or '-'
        )
        return response

    # Helper for error details
    def _error_details(msg):
        return msg if app.debug or DEV_MODE else None

    def _request_id():
        return getattr(g, 'request_id', '-')

    # Register error handlers
    @app.errorhandler(400)
    def bad_request(error):
        logger.warning('bad_request error=%s', error)
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '请求参数错误',
                      'details': _error_details(str(error))},
            'request_id': _request_id()
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        logger.warning('not_found error=%s', error)
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '资源不存在',
                      'details': _error_details(str(error))},
            'request_id': _request_id()
        }), 404

    @app.errorhandler(401)
    def unauthorized(error):
        logger.warning('unauthorized error=%s', error)
        return jsonify({
            'success': False,
            'error': {'code': 401, 'message': '未授权访问'},
            'request_id': _request_id()
        }), 401

    @app.errorhandler(500)
    def internal_error(error):
        logger.error('internal_error error=%s', error, exc_info=True)
        return jsonify({
            'success': False,
            'error': {'code': 500, 'message': '服务器内部错误',
                      'details': _error_details('请稍后重试')},
            'request_id': _request_id()
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.exception('unhandled_exception error=%s', error)
        return jsonify({
            'success': False,
            'error': {'code': 500, 'message': '服务器内部错误',
                      'details': _error_details(str(error))},
            'request_id': _request_id()
        }), 500

    # Database teardown
    from .db import close_db
    app.teardown_appcontext(close_db)

    # Register blueprints
    from .routes import register_routes
    register_routes(app)

    # 启动定时提醒任务（后台线程，测试时不启动）
    if not IS_TESTING:
        import threading
        from services import reminder_service
        
        def reminder_scheduler():
            """定时检查提醒（每小时一次）"""
            while True:
                try:
                    with app.app_context():
                        reminder_service.check_and_send_all()
                except Exception as e:
                    logger.error(f"Reminder scheduler error: {e}")
                
                time.sleep(3600)  # 每小时
        
        scheduler_thread = threading.Thread(target=reminder_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Reminder scheduler started")

    return app

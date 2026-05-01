"""
心语花园 - Heart Garden
AI 驱动的情感陪伴应用

Flask application factory.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import sys
import logging

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = Path(os.getenv('STATIC_DIR', APP_DIR / 'static'))
IS_TESTING = 'pytest' in sys.modules

# Limiter instance — created at module level so route blueprints can import it
limiter = Limiter(key_func=get_remote_address, enabled=not IS_TESTING)


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

    _logger = logging.getLogger()
    log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    _logger.setLevel(log_level)
    _logger.addHandler(file_handler)

    return _logger


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

    # Helper for error details
    def _error_details(msg):
        return msg if app.debug or DEV_MODE else None

    # Register error handlers
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

    # Database teardown
    from .db import close_db
    app.teardown_appcontext(close_db)

    # Register blueprints
    from .routes import register_routes
    register_routes(app)

    return app

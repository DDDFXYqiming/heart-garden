"""
API 信息 + 健康检查 + SPA 静态文件服务
"""

from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request, send_from_directory
from .. import STATIC_DIR
from ..version import APP_VERSION

info_bp = Blueprint('info', __name__)


@info_bp.route('/api/', methods=['GET'])
@info_bp.route('/api/info', methods=['GET'])
def api_info():
    return jsonify({
        'success': True,
        'data': {
            'name': 'Heart Garden - 心语花园',
            'version': APP_VERSION,
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


@info_bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'ok': True,
        'status': 'ok',
        'success': True,
        'data': {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': APP_VERSION
        }
    })


@info_bp.route('/', defaults={'path': ''}, methods=['GET'])
@info_bp.route('/<path:path>', methods=['GET'])
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
            'version': APP_VERSION,
            'description': '前端静态文件尚未构建，请运行 npm --prefix frontend run build。'
        }
    })

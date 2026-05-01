"""
LLM 配置 API 路由
"""

from flask import Blueprint, request, jsonify, g, current_app
from ..db import query_db, execute_db
from ..auth import require_auth
from services.llm_service import parse_llm_config, serialize_llm_config
from .. import logger

llm_bp = Blueprint('llm', __name__)


@llm_bp.route('/api/llm/config', methods=['GET'])
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


@llm_bp.route('/api/llm/config', methods=['POST'])
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

    current_app.llm_service.clear_cache()

    logger.info(f"LLM config saved for user: {g.current_user_id}, enabled: {config['enabled']}")
    return jsonify({'success': True, 'data': config})


@llm_bp.route('/api/llm/test', methods=['POST'])
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

    result = current_app.llm_service.test_connection(config)
    return jsonify({'success': True, 'data': result})

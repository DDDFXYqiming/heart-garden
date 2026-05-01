"""
LLM 配置 API 路由
"""

from flask import Blueprint, request, jsonify, g, current_app
from ..db import query_db, execute_db
from ..auth import require_auth
from services.llm_service import parse_llm_config, serialize_llm_config
from .. import logger

llm_bp = Blueprint('llm', __name__)

MASK_MARKERS = ('****', '••', '●●')
MASK_CHARS = {'*', '•', '●', '·', '∙', '⦁'}


def _is_masked_api_key(value):
    """判断前端提交的是脱敏占位符，而不是真实 API Key。"""
    key = (value or '').strip()
    if not key:
        return False
    if any(marker in key for marker in MASK_MARKERS):
        return True
    return len(key) >= 4 and set(key) <= MASK_CHARS


def _get_saved_llm_config(user_id):
    user = query_db(
        'SELECT llm_config FROM users WHERE id = ?',
        (user_id,), one=True
    )
    return parse_llm_config(user['llm_config'] if user else None)


def _redact_api_key(api_key):
    key = (api_key or '').strip()
    if not key:
        return ''
    return key[:8] + '****' if len(key) > 8 else '****'


def _safe_llm_config(config):
    """返回给前端的配置：只暴露是否已保存和脱敏预览，不回传真实密钥。"""
    safe_config = dict(config)
    api_key = safe_config.pop('api_key', '')
    safe_config['api_key'] = ''
    safe_config['api_key_saved'] = bool(api_key)
    safe_config['api_key_preview'] = _redact_api_key(api_key)
    return safe_config


def _resolve_api_key(data, saved_config):
    raw_key = data.get('api_key') if 'api_key' in data else None
    incoming_key = (raw_key or '').strip()
    if incoming_key and not _is_masked_api_key(incoming_key):
        return incoming_key
    return (saved_config.get('api_key') or '').strip()


@llm_bp.route('/api/llm/config', methods=['GET'])
@require_auth
def get_llm_config():
    config = _get_saved_llm_config(g.current_user_id)
    return jsonify({'success': True, 'data': _safe_llm_config(config)})


@llm_bp.route('/api/llm/config', methods=['POST'])
@require_auth
def save_llm_config():
    data = request.json or {}
    if not data:
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '请求体不能为空'}
        }), 400

    saved_config = _get_saved_llm_config(g.current_user_id)
    config = {
        "enabled": bool(data.get("enabled", saved_config.get("enabled", False))),
        "base_url": (data.get("base_url", saved_config.get("base_url", "")) or "").strip(),
        "api_key": _resolve_api_key(data, saved_config),
        "model": (data.get("model", saved_config.get("model", "deepseek-chat")) or "deepseek-chat").strip(),
        "temperature": float(data.get("temperature", saved_config.get("temperature", 0.7)))
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

    logger.info(
        "LLM config saved user=%s enabled=%s api_key_set=%s",
        g.current_user_id,
        config['enabled'],
        bool(config.get('api_key'))
    )
    return jsonify({'success': True, 'data': _safe_llm_config(config)})


@llm_bp.route('/api/llm/test', methods=['POST'])
@require_auth
def test_llm_connection():
    data = request.json or {}
    saved_config = _get_saved_llm_config(g.current_user_id)
    config = {
        "enabled": True,
        "base_url": (data.get("base_url", saved_config.get("base_url", "")) or "").strip(),
        "api_key": _resolve_api_key(data, saved_config),
        "model": (data.get("model", saved_config.get("model", "deepseek-chat")) or "deepseek-chat").strip(),
        "temperature": float(data.get("temperature", saved_config.get("temperature", 0.7)))
    }

    result = current_app.llm_service.test_connection(config)
    return jsonify({'success': True, 'data': result})

"""
提醒设置与通知 API 路由
"""

from flask import Blueprint, request, jsonify, g
from .. import limiter
from ..auth import require_auth
from services import reminder_service

reminder_bp = Blueprint('reminder', __name__)


@reminder_bp.route('/api/reminders/settings', methods=['GET'])
@require_auth
@limiter.limit('30 per minute')
def get_reminder_settings():
    """获取提醒设置"""
    settings = reminder_service.get_reminder_settings(g.current_user_id)
    return jsonify({
        'success': True,
        'data': settings
    })


@reminder_bp.route('/api/reminders/settings', methods=['PUT'])
@require_auth
@limiter.limit('10 per minute')
def update_reminder_settings():
    """更新提醒设置"""
    data = request.get_json()
    
    if not isinstance(data, list):
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '请求数据必须是数组'}
        }), 400
    
    try:
        reminder_service.update_reminder_settings(g.current_user_id, data)
        return jsonify({
            'success': True,
            'message': '提醒设置已更新'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 500, 'message': str(e)}
        }), 500


@reminder_bp.route('/api/notifications', methods=['GET'])
@require_auth
@limiter.limit('60 per minute')
def get_notifications():
    """获取通知列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', False, type=bool)
    
    result = reminder_service.get_notifications(
        g.current_user_id, page, per_page, unread_only
    )
    
    return jsonify({
        'success': True,
        'data': result
    })


@reminder_bp.route('/api/notifications/<notification_id>/read', methods=['PUT'])
@require_auth
@limiter.limit('60 per minute')
def mark_notification_read(notification_id):
    """标记通知已读"""
    success = reminder_service.mark_notification_read(
        notification_id, g.current_user_id
    )
    
    if success:
        return jsonify({
            'success': True,
            'message': '通知已标记为已读'
        })
    else:
        return jsonify({
            'success': False,
            'error': {'code': 404, 'message': '通知不存在'}
        }), 404


@reminder_bp.route('/api/notifications/read-all', methods=['PUT'])
@require_auth
@limiter.limit('10 per minute')
def mark_all_read():
    """全部标记已读"""
    count = reminder_service.mark_all_read(g.current_user_id)
    return jsonify({
        'success': True,
        'message': f'已标记 {count} 条通知为已读'
    })

"""
社区功能 API 路由
帖子、点赞、评论相关接口
"""

from flask import Blueprint, request, jsonify, g
from .. import limiter
from ..auth import require_auth
from services import community_service

community_bp = Blueprint('community', __name__)


@community_bp.route('/api/community/posts', methods=['GET'])
@require_auth
@limiter.limit('60 per minute')
def get_posts():
    """获取社区帖子列表"""
    page = request.args.get('page', 1, type=int)
    mood_filter = request.args.get('mood_filter', None)
    per_page = request.args.get('per_page', 20, type=int)

    result = community_service.get_posts(page, mood_filter, per_page)

    return jsonify({
        'success': True,
        'data': result
    })


@community_bp.route('/api/community/posts', methods=['POST'])
@require_auth
@limiter.limit('10 per minute')
def create_post():
    """发布新帖子"""
    data = request.get_json()

    if not data or 'content' not in data or not data['content'].strip():
        return jsonify({
            'success': False,
            'error': {'code': 400, 'message': '内容不能为空'}
        }), 400

    content = data['content'].strip()
    mood_label = data.get('mood_label')
    mood_score = data.get('mood_score')
    is_anonymous = data.get('is_anonymous', True)

    post_id = community_service.create_post(
        g.current_user_id, content, mood_label, mood_score, is_anonymous
    )

    return jsonify({
        'success': True,
        'data': {'post_id': post_id},
        'message': '帖子发布成功'
    }), 201

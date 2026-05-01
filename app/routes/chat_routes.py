"""
AI 对话 + SSE 流式 API 路由
"""

import uuid
import json
from flask import Blueprint, request, jsonify, g, current_app
from ..db import query_db, execute_db
from ..auth import require_auth, _analyze_with_custom_words
from services.llm_service import parse_llm_config
from services.prompt_engine import MoodContext
from .. import logger

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/api/chat', methods=['POST'])
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

    llm_service = current_app.llm_service
    ai_companion = current_app.ai_companion

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

    logger.debug(f"Chat: {len(user_message)} chars, mode={response_mode}, conv={conversation_id}")
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


@chat_bp.route('/api/chat/stream', methods=['POST'])
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

    llm_service = current_app.llm_service
    ai_companion = current_app.ai_companion

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

    return current_app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )

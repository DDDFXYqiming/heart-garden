"""
AI 对话 + SSE 流式 API 路由
"""

import uuid
import json
import time
import queue
import threading
from flask import Blueprint, request, jsonify, g, current_app, stream_with_context
from ..db import query_db, execute_db
from ..auth import require_auth, _analyze_with_custom_words
from ..mood_records import record_mood
from services.llm_service import parse_llm_config
from services.prompt_engine import MoodContext
from .. import logger

chat_bp = Blueprint('chat', __name__)

HEARTBEAT_INTERVAL = 15  # 秒，可通过 app.config['HEARTBEAT_INTERVAL'] 覆盖


def _load_user_llm_config(user_id: str) -> dict:
    user_row = query_db(
        'SELECT llm_config FROM users WHERE id = ?',
        (user_id,), one=True
    )
    return parse_llm_config(user_row['llm_config'] if user_row else None)


def _analyze_chat_mood(user_id: str, user_message: str, user_llm_config: dict) -> tuple[dict, str, bool]:
    """Analyze chat mood: LLM first when configured, rule analyzer as fallback."""
    llm_service = current_app.llm_service
    llm_configured = llm_service.is_llm_configured(user_llm_config)
    if llm_configured:
        llm_success, llm_mood, error = llm_service.analyze_mood(
            user_message,
            user_config=user_llm_config,
        )
        if llm_success and llm_mood:
            llm_mood['analysis_source'] = 'llm'
            return llm_mood, 'llm', True
        logger.warning(
            "chat mood LLM failed fallback=rule_engine error=%s",
            error or "unknown",
        )

    mood_result = _analyze_with_custom_words(user_id, user_message)
    mood_result['analysis_source'] = 'rule_engine'
    return mood_result, 'rule_engine', llm_configured


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

    user_llm_config = _load_user_llm_config(g.current_user_id)
    mood_result, mood_source, llm_configured = _analyze_chat_mood(
        g.current_user_id,
        user_message,
        user_llm_config,
    )
    record_mood(
        g.current_user_id,
        mood_result,
        source_type='chat',
        source_id=conversation_id,
    )

    response_mode = "rule_engine"
    response = None

    llm_service = current_app.llm_service
    ai_companion = current_app.ai_companion
    logger.info(
        "chat request conv=%s chars=%s history=%s mood=%s mood_source=%s llm_configured=%s",
        conversation_id,
        len(user_message),
        len(history_list),
        mood_result['mood_label'],
        mood_source,
        llm_configured
    )

    if llm_configured:
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
            logger.info(
                "chat llm result success=true conv=%s response_chars=%s",
                conversation_id,
                len(response or "")
            )
        else:
            logger.warning(
                "chat llm result success=false conv=%s fallback=rule_engine source=%s",
                conversation_id,
                source
            )

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

    logger.info(
        "chat response conv=%s mode=%s response_chars=%s mood=%s",
        conversation_id,
        response_mode,
        len(response or ""),
        mood_result['mood_label']
    )
    return jsonify({
        'success': True,
        'data': {
            'response': response,
            'conversation_id': conversation_id,
            'mood': mood_result['mood_label'],
            'mood_source': mood_source,
            'sentiment': 'positive' if mood_result['mood_score'] >= 60 else 'negative' if mood_result['mood_score'] < 40 else 'neutral',
            'response_mode': response_mode
        }
    })


@chat_bp.route('/api/chat/stream', methods=['POST'])
@require_auth
def chat_stream():
    heartbeat_interval = current_app.config.get('HEARTBEAT_INTERVAL', HEARTBEAT_INTERVAL)
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

    user_llm_config = _load_user_llm_config(g.current_user_id)
    mood_result, mood_source, llm_configured = _analyze_chat_mood(
        g.current_user_id,
        user_message,
        user_llm_config,
    )
    record_mood(
        g.current_user_id,
        mood_result,
        source_type='chat',
        source_id=conversation_id,
    )

    llm_service = current_app.llm_service
    ai_companion = current_app.ai_companion
    current_user_id = g.current_user_id
    logger.info(
        "chat_stream request conv=%s chars=%s history=%s mood=%s mood_source=%s llm_configured=%s",
        conversation_id,
        len(user_message),
        len(history_list),
        mood_result['mood_label'],
        mood_source,
        llm_configured
    )

    def generate():
        import queue
        import threading

        stream_start = time.perf_counter()
        full_response = []
        response_mode = "rule_engine"

        # 使用闭包中的 heartbeat_interval（来自 chat_stream）
        # 事件队列：chunk / heartbeat / done / fallback
        event_queue = queue.Queue(maxsize=200)
        stop_event = threading.Event()

        def llm_worker():
            """读取 LLM 流式 chunk，放入事件队列"""
            nonlocal response_mode, full_response
            try:
                if llm_configured:
                    response_mode = "llm"
                    mood_ctx = MoodContext(
                        mood_label=mood_result['mood_label'],
                        mood_score=mood_result['mood_score'],
                        keywords=mood_result.get('keywords', [])
                    )
                    for chunk in llm_service.chat_stream(
                        user_message=user_message,
                        conversation_history=history_list,
                        mood_context=mood_ctx,
                        user_config=user_llm_config
                    ):
                        full_response.append(chunk)
                        event_queue.put(('chunk', chunk))
            except Exception as e:
                logger.exception("chat_stream LLM exception conv=%s error=%s", conversation_id, e)
            finally:
                if not full_response:
                    # LLM 未配置或调用失败，fallback 到 rule_engine
                    logger.warning(
                        "chat_stream LLM empty result conv=%s fallback=rule_engine",
                        conversation_id
                    )
                    response_mode = "rule_engine"
                    event_queue.put(('fallback', None))
                else:
                    event_queue.put(('done', None))

        def heartbeat_worker():
            """每 heartbeat_interval 秒发送一次 SSE 心跳"""
            while not stop_event.is_set():
                if stop_event.wait(timeout=heartbeat_interval):
                    break
                if not stop_event.is_set():
                    try:
                        event_queue.put_nowait(('heartbeat', None))
                    except queue.Full:
                        pass

        llm_thread = threading.Thread(target=llm_worker, daemon=True)
        heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
        llm_thread.start()
        heartbeat_thread.start()

        while True:
            try:
                event_type, data = event_queue.get(timeout=1)
                if event_type == 'chunk':
                    yield f"data: {json.dumps({'type': 'chunk', 'content': data}, ensure_ascii=False)}\n\n"
                elif event_type == 'heartbeat':
                    yield ':keep-alive\n\n'
                elif event_type == 'fallback':
                    response = ai_companion.generate_response(
                        user_message, history=history_list, mood=mood_result['mood_label']
                    )
                    full_response = [response]
                    logger.info(
                        "chat_stream rule_engine response conv=%s response_chars=%s",
                        conversation_id,
                        len(response or "")
                    )
                    yield f"data: {json.dumps({'type': 'chunk', 'content': response}, ensure_ascii=False)}\n\n"
                    event_queue.put(('done', None))
                elif event_type == 'done':
                    break
            except queue.Empty:
                continue

        stop_event.set()
        llm_thread.join(timeout=5)
        heartbeat_thread.join(timeout=5)

        final_text = ''.join(full_response)
        execute_db('''
        INSERT INTO chat_history (id, conversation_id, role, content, mood_label)
        VALUES (?, ?, 'assistant', ?, ?)
        ''', (str(uuid.uuid4()), conversation_id, final_text, mood_result['mood_label']))

        if len(history) <= 2:
            execute_db('''
            UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            ''', (user_message[:50], conversation_id, current_user_id))
        else:
            execute_db('''
            UPDATE conversations SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            ''', (conversation_id, current_user_id))

        meta = {
            'type': 'done',
            'conversation_id': conversation_id,
            'mood': mood_result['mood_label'],
            'mood_source': mood_source,
            'response_mode': response_mode
        }
        logger.info(
            "chat_stream done conv=%s mode=%s response_chars=%s duration_ms=%.1f",
            conversation_id,
            response_mode,
            len(final_text or ""),
            (time.perf_counter() - stream_start) * 1000
        )
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

    return current_app.response_class(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )

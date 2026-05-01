"""日志系统回归测试"""
import logging
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ['JWT_SECRET'] = 'test-secret-key-for-testing'
os.environ['DEV_MODE'] = 'true'

from app import RequestIdFilter, setup_logging
from app.main import app


def _unique():
    return uuid.uuid4().hex[:8]


def _register_and_login(client):
    suffix = _unique()
    username = f'log_{suffix}'
    email = f'log_{suffix}@test.com'
    password = 'test123'
    client.post('/api/auth/register', json={
        'username': username,
        'email': email,
        'password': password
    })
    resp = client.post('/api/auth/login', json={
        'username': username,
        'email': email,
        'password': password
    })
    token = resp.get_json()['data']['token']
    return {'Authorization': f'Bearer {token}'}


def test_setup_logging_is_idempotent():
    root_logger = logging.getLogger()
    before = len(root_logger.handlers)
    setup_logging()
    setup_logging()
    after = len(root_logger.handlers)
    assert after == before


def test_request_id_header_is_returned():
    client = app.test_client()
    resp = client.get('/api/health', headers={'X-Request-ID': 'testreq1'})

    assert resp.status_code == 200
    assert resp.headers['X-Request-ID'] == 'testreq1'


def test_request_id_filter_uses_current_request_context():
    record = logging.LogRecord(
        name='test', level=logging.INFO, pathname=__file__, lineno=1,
        msg='hello', args=(), exc_info=None
    )
    with app.test_request_context('/api/health', headers={'X-Request-ID': 'ctxreq1'}):
        app.preprocess_request()
        RequestIdFilter().filter(record)

    assert record.request_id == 'ctxreq1'


def test_chat_stream_rule_engine_completes_without_context_error():
    client = app.test_client()
    headers = _register_and_login(client)

    resp = client.post('/api/chat/stream', json={
        'message': '今天心情不错'
    }, headers=headers, buffered=True)
    text = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert '"type": "chunk"' in text
    assert '"type": "done"' in text
    assert '"response_mode": "rule_engine"' in text

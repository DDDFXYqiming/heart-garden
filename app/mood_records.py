"""
情绪记录写入工具
"""

import json
import uuid
from typing import Any, Mapping

from .db import execute_db
from . import logger


def record_mood(user_id: str, mood_result: Mapping[str, Any], source_type: str, source_id: str | None = None, diary_id: str | None = None) -> str:
    """Persist a mood analysis result for trend/distribution statistics."""
    record_id = str(uuid.uuid4())
    keywords = mood_result.get('keywords', [])
    execute_db('''
    INSERT INTO mood_records (id, diary_id, user_id, mood_score, mood_label, keywords, trend, source_type, source_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        record_id,
        diary_id,
        user_id,
        mood_result['mood_score'],
        mood_result['mood_label'],
        json.dumps(keywords, ensure_ascii=False),
        mood_result.get('trend', '平稳'),
        source_type,
        source_id,
    ))
    logger.info(
        "mood record created id=%s source_type=%s source_id=%s mood=%s score=%s user=%s",
        record_id,
        source_type,
        source_id,
        mood_result['mood_label'],
        mood_result['mood_score'],
        user_id,
    )
    return record_id

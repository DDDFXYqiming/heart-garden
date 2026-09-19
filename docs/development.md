# Development

## Project layout

| Area | Main files | Responsibility |
| --- | --- | --- |
| Frontend | `frontend/` | Vue 3 SPA, Vue Router, Pinia, Axios, and Tailwind CSS with the hand-drawn UI. |
| Application factory | `app/__init__.py` | Flask app creation, extension setup, request IDs, and logging. |
| Routes and storage | `app/`, `services/db.py` | Authentication, diaries, chat, mood, reminders, analytics, and SQLite access. |
| Mood analysis | `services/mood_analyzer.py` | Keyword rules, semantic mood parsing, scores, and trend data. |
| Chat | `services/ai_companion.py`, `services/llm_service.py` | Conversation context, provider selection, streaming responses, and rule fallback. |
| Prompt and provider layer | `services/prompt_engine.py`, `services/openai_compatible.py` | Prompt construction and OpenAI-compatible provider calls. |
| Shared data | `services/constants.py` | Prompt fragments, emoji mappings, and mood keywords. |

The backend uses Flask 3, `flask-cors`, SQLite, `python-dotenv`, PyJWT, and `flask-limiter`. The frontend uses Vue 3, Vite 6, Vue Router 4, Pinia, Axios, and Tailwind CSS.

## Implementation notes

- The Flask application uses a factory and separate route and service modules.
- Chat supports normal and SSE streaming responses.
- LLM mood results are preferred when available; rule analysis remains the fallback path.
- Authentication endpoints are rate-limited and production errors are less verbose than development errors.
- Reminder checks run in the background and record notification history.
- The frontend contains diary, chat, mood, statistics, memory-garden, settings, reminder, and notification views.

## Tests

The backend suite needs `pytest`. Run it from the repository root:

```bash
pip install pytest
python -m pytest
```

The frontend uses Vitest:

```bash
cd frontend
npm test
```

## Conventions

Use `snake_case` for Python functions and `PascalCase` for Python classes. Keep database writes behind the service layer and preserve the rule fallback when changing the LLM path. New API errors should use the existing response format and logger.

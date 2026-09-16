# Heart Garden

Heart Garden is a local-first diary and mood companion. It stores diary entries and mood history in SQLite, offers a rule-based chat mode without an external model, and can use an OpenAI-compatible LLM when the user enables it. When an LLM call fails, the chat service falls back to the rule engine.

## Features

- User registration, login, JWT authentication, and per-user data isolation.
- Diary entry create, read, update, and delete operations.
- Mood analysis with scores, tags, trend views, and a rule-lexicon fallback.
- Hybrid chat with rule and LLM modes, multi-turn context, and a response-source label in the UI.
- Settings for the LLM endpoint, model, temperature, connection testing, and masked API-key storage.
- Mood history, distribution statistics, and trend visualizations.
- Reminder rules for low mood, daily care, and weekly reports, with a notification history and a do-not-disturb window.

## Architecture

| Area | Main files | Responsibility |
|---|---|---|
| Frontend | `frontend/` | Vue 3 SPA, Vue Router, Pinia, Axios, and Tailwind CSS with the hand-drawn UI. |
| Application factory | `app/__init__.py` | Flask app creation, extension setup, request IDs, and logging. |
| Routes and storage | `app/`, `services/db.py` | Authentication, diaries, chat, mood, reminders, analytics, and SQLite access. |
| Mood analysis | `services/mood_analyzer.py` | Keyword rules, semantic mood parsing, scores, and trend data. |
| Chat | `services/ai_companion.py`, `services/llm_service.py` | Conversation context, provider selection, streaming responses, and rule fallback. |
| Prompt and provider layer | `services/prompt_engine.py`, `services/openai_compatible.py` | Prompt construction and OpenAI-compatible provider calls. |
| Shared data | `services/constants.py` | Prompt fragments, emoji mappings, and mood keywords. |

The backend uses Flask 3, `flask-cors`, SQLite, `python-dotenv`, PyJWT, and `flask-limiter`. The frontend uses Vue 3, Vite 6, Vue Router 4, Pinia, Axios, and Tailwind CSS.

## Quick start

Requirements are Python 3.9 or newer, Node.js 18 or newer, and SQLite 3.8 or newer.

On Windows, double-click `start.bat`. To start the services manually:

```bash
git clone https://github.com/DDDFXYqiming/heart-garden.git
cd heart-garden

python -m venv venv
# Windows PowerShell
venv\Scripts\Activate.ps1
# macOS or Linux
# source venv/bin/activate
pip install -r requirements.txt
python -m app.main

# in a second terminal
cd frontend
npm install
npm run dev
```

The default development addresses are `http://localhost:5000` for the backend and `http://localhost:3001` for the frontend.

## Enable LLM chat

The rule engine is the default. To enable the optional provider:

1. Set a private random `JWT_SECRET` before starting the backend.
2. Set `SECRET_KEY` when Flask session signatures must survive restarts. If it is omitted, the app uses a process-local random value.
3. Open `http://localhost:3001/#/settings`.
4. Turn on **Use LLM Chat**, enter an OpenAI-compatible base URL, model, and API key, then run **Test Connection** and **Save Configuration**.

The settings API never returns the real API key. It keeps an existing key when a masked or empty value is submitted. Keep secrets outside version control and use environment variables or the settings page rather than committing them.

## Current implementation

- The Flask application uses a factory and separate route and service modules.
- Chat supports normal and SSE streaming responses.
- LLM mood results are preferred when available; rule analysis remains the fallback path.
- Authentication endpoints are rate-limited and production errors are less verbose than development errors.
- Reminder checks run in the background and record notification history.
- The frontend contains diary, chat, mood, statistics, memory-garden, settings, reminder, and notification views.

See [SPEC.md](./SPEC.md) for the API summary and project-specific behavior. Run the backend and frontend test commands in their respective package files before deploying.

## Development notes

Use `snake_case` for Python functions and `PascalCase` for Python classes. Keep database writes behind the service layer and preserve the rule fallback when changing the LLM path. New API errors should use the existing response format and logger.

## License

Copyright (c) 2026 Heart Garden Team. All rights reserved.

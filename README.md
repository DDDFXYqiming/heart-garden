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

See [SPEC.md](./SPEC.md) for the API summary and project-specific behavior, and [development](docs/development.md) for the project layout and tests.

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

The settings API never returns the real API key. It keeps an existing key when a masked or empty value is submitted. Keep secrets out of version control. Use environment variables or the settings page.

## License

Copyright (c) 2026 Heart Garden Team. All rights reserved.

# Heart Garden

## Project Overview

Heart Garden is an AI-driven emotional companion application that provides deep understanding, mood tracking, and intelligent companionship.  
The system is designed for local deployment to protect user privacy and data security.

## Technical Architecture

### Frontend Stack

- **Framework**: Vue 3 (Composition API + `<script setup>`)
- **Build Tool**: Vite 6
- **Routing**: Vue Router 4
- **State Management**: Pinia
- **HTTP Client**: Axios
- **Styling**: Tailwind CSS 3
- **Design Style**: Hand-drawn UI style

### Backend Stack

- **Web Framework**: Flask 3.0.0
- **CORS**: flask-cors 4.0.0
- **Database**: SQLite
- **Config Management**: python-dotenv 1.0.0
- **JWT Auth**: PyJWT 2.8.0
- **Rate Limiting**: flask-limiter 3.10.1
- **LLM Integration**: OpenAI SDK (compatible mode)

### Service Modules

1. **Mood Analysis Service** (`mood_analyzer.py`)
   - Text sentiment detection, keyword extraction, mood trend analysis, and rule-based fallback lexicon.

2. **AI Companion Service** (`ai_companion.py`)
   - Context-aware conversation, multi-turn memory, and personalized response generation.

3. **LLM Service** (`llm_service.py`)
   - Hybrid routing: automatically chooses rule engine or LLM.
   - User-config driven: loads user LLM settings from the database.
   - LLM-first mood judgment when companion mode is enabled.
   - Automatic downgrade to rule engine if LLM calls fail.

4. **LLM Interface Layer** (`openai_compatible.py`)
   - OpenAI-compatible API adapter for any compatible provider.
   - Interface abstraction in `llm_interface.py` for easy model switching.

5. **Prompt Engine** (`prompt_engine.py`)
   - Converts rule-engine logic into LLM system prompts.
   - Supports personalized settings and emotional context injection.

6. **Shared Constants** (`constants.py`)
   - Prompt templates, emoji mappings, and mood keywords.

7. **Logging System** (`app/__init__.py` + service logs)
   - Dual-channel output (stdout/file), request ID, request latency, and LLM call/downgrade tracking.

## Core Features

### 1. User System

- User registration/login (JWT authentication)
- User-level data isolation
- User profile retrieval

### 2. Diary Records

- Create/read/update/delete diary entries
- Automatic timestamp management

### 3. Mood Analysis

- Multi-dimensional mood scoring (0-100)
- LLM semantic mood judgment first in LLM companion mode
- Mood tagging and trend analysis
- Rule lexicon fallback when LLM is not configured or fails

### 4. Intelligent Chat (Hybrid Mode)

- **Rule Engine Mode** (default): works out of the box
- **LLM Mode** (optional): enable after API key configuration
- **Automatic Downgrade**: falls back to rule engine on LLM failure
- In LLM mode, mood judgment is LLM-first with rule-based backup
- Context awareness and multi-turn memory
- Response source indicator in chat UI (AI / Rule)

### 5. Settings and Configuration

- AI chat mode switching (Rule / LLM)
- LLM configuration management (URL, API key, model, temperature)
- Secure API key masking (no leakage and no overwrite when reopening settings)
- Connection test feature
- Custom mood lexicon entry is temporarily disabled

### 6. Data Tracking and Analytics

- Mood history and trend visualization
- Analytics APIs
- Mood distribution statistics
- Companion chat mood events included in trend and distribution metrics

### 7. Smart Reminders

- Mood alerts: auto-detect low mood states and trigger caring messages
- Reminder settings: configurable type, threshold, and do-not-disturb window
- Notification center: history with read/unread status
- Scheduled task: background check and notification every hour
- Personalized care messages based on current user mood

## Quick Start

### Requirements

- Python 3.9+
- Node.js 18+
- SQLite 3.8+

### One-click Start (Windows)

```bash
# Double click to run
start.bat
```

### Manual Start

```bash
# Clone project
git clone https://github.com/DDDFXYqiming/heart-garden.git
cd heart-garden

# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

- Backend: http://localhost:5000
- Frontend: http://localhost:3001

### Configure LLM (Optional)

1. Open http://localhost:3001/#/settings after startup.
2. Find the **AI Chat Mode** section.
3. Enable **Use LLM Chat**.
4. Enter API base URL (for example, `https://api.deepseek.com/v1`) and API key.
5. Click **Test Connection**.
6. Click **Save Configuration**.

## Project Status

### v1.0 - MVP Foundation

- Basic diary CRUD
- Mood analysis engine
- AI chat interface
- Local data storage

### v2.0 - Feature Enhancement

- User system: registration/login, JWT auth, data isolation
- Multi-turn conversation: context awareness and history
- Analytics: summary metrics and mood distribution
- Custom lexicon: user-extendable mood keywords

### v2.1 - Frontend Application

- Vue 3 frontend with hand-drawn UI and full frontend/backend separation (SPA)
- Eight pages: home, login/register, diary, AI chat, mood trend, stats dashboard, memory garden, settings

### v2.2 - LLM Hybrid Mode (Core Feature)

- Hybrid architecture: rule engine and LLM dual path
- Web settings UI for LLM configuration
- OpenAI-compatible interface for DeepSeek, OpenAI, and other compatible APIs
- Automatic downgrade strategy on LLM failure
- Prompt engineering: converts rule logic into LLM system prompts
- Persistent user config in database
- One-click connection test
- Chat source labels (AI / Rule)

### v2.3 - Security Fixes

- `DEV_MODE` switched to environment-variable control; auth bypass disabled by default
- `JWT_SECRET` fallback hardcoding removed; configuration required at startup
- Detailed errors returned only in development mode; hidden in production
- SQL table-name migration with allowlist validation

### v2.4 - Code Refactor

- Rate limits added to auth endpoints (register/login: 5 requests per IP per minute)
- Extracted `_analyze_with_custom_words()` helper to remove four duplicated blocks
- Created `services/constants.py` shared constants for templates and emoji dictionaries
- Removed 20+ redundant try/except blocks (global error handler already covers them)
- Removed unused `chart.js` + `vue-chartjs` dependencies (~150KB)

### v2.5 - Fixes and Performance Optimization

- Fixed conversation history loss after page refresh/navigation
- Fixed N+1 query issue: `conversations` now uses `LEFT JOIN`
- Merged stats SQL from seven queries to three
- Added `GET /api/diaries/:id` endpoint
- Frontend LLM timeout increased from 15s to 60s
- Single-pass keyword matching in `mood_analyzer`

### v2.6 - SSE Streaming Response

- Added `/api/chat/stream` POST endpoint with SSE event stream
- `LLMService.chat_stream` now streams token-by-token output
- `ChatPage` uses `fetch` + `ReadableStream` for typing effect

### v2.7 - Test Coverage

- `mood_analyzer` unit tests (11 cases)
- `prompt_engine` unit tests (6 cases)
- API integration tests (16 cases: auth/diary/stats/mood/conversation)

### v2.8 - Code Cleanup

- LLM provider cache switched to OrderedDict LRU, max 10 providers
- Routine operation logs changed from info to debug

### v3.0 - Architecture Refactor

- `main.py` simplified from 1468 lines to a 27-line entry
- Flask factory pattern (`create_app`)
- Modular split: `db.py`, `auth.py`, and 9 route modules

### v3.0.1 - Startup Hotfix

- Fixed startup crash caused by missing app context for `init_db()` after factory refactor

### v3.0.2 - Logging System Upgrade

- `setup_logging` now includes stdout StreamHandler for runtime logs in Zeabur/Docker
- Each request gets `X-Request-ID`; logs method, path, status, latency, and user ID
- LLM config checks, call results, stream responses, and downgrade reasons are all logged
- Added logging regression tests for idempotency, request IDs, and SSE stream context

### v3.0.3 - Frontend Streaming Call Fix

- Fixed runtime `ReferenceError` caused by missing `chatStream` import in `ChatPage`
- Added HTTP status and `ReadableStream` body validation in `chatStream`
- Added frontend contract regression tests to prevent missing-stream import regressions

### v3.0.4 - Settings API Key Retention Fix

- Settings page no longer binds masked API key to submit payload fields
- When saving LLM config, empty/masked `api_key` keeps the stored database key
- Test connection reuses stored key when no new key is entered
- LLM config GET/POST never returns real API key, only saved-state and masked preview
- Added LLM config regression tests and settings-page frontend contract tests

### v3.0.5 - Mood and Metrics Fixes

- In LLM companion mode, mood judgment prioritizes structured LLM output, then falls back to rules
- User mood from normal/streaming chat is now written to `mood_records` for trend/distribution stats
- Custom mood lexicon entry is temporarily disabled (frontend hidden, backend write endpoint returns 403)
- Expanded rule lexicon to cover more natural positive expressions
- Added regression tests for LLM mood parsing, chat stats persistence, lexicon disablement, and frontend contracts

### v3.0.6 - Streaming UTF-8 Fix

- Fixed trailing multi-byte truncation/garbling in SSE streams
- Added multibyte integrity checks in `llm_service.py chat_stream()`
- Added UTF-8 stream integrity regression tests
- Added 15-second keepalive heartbeat to prevent Vite proxy/Nginx timeout
- Added `ensure_ascii=False` in `json.dumps` to preserve original non-ASCII text

### v3.0.7 - LLM Security Hardening

- Input sanitization (`sanitize_input`): control-character removal, injection pattern filtering, overlong-input truncation
- Prompt hardening (`harden_system_prompt`): explicit safety boundaries against instruction override
- User-message isolation (`wrap_user_message`): bounded markers around user content
- Output sanitization (`sanitize_output`): remove leaked system prompt text and truncate overlong output
- Injection detection (`detect_injection`): common prompt-injection pattern detection
- Integrated protections into `PromptBuilder` and `LLMService`
- Added 13 regression tests for input sanitization, prompt hardening, output filtering, and injection detection

### v3.1 - Frontend Component Refactor

- Added four shared components: `ChatBubble`, `DiaryCard`, `MoodBar`, `StatCard`
- Refactored five pages to use shared components: `ChatPage`, `DiaryList`, `GardenPage`, `MoodTrend`, `StatsPage`
- Unified component exports via `components/index.js`
- Unit tests: all 17 tests passing

### v3.2 - Smart Reminder System

- Reminder settings: mood alerts, daily care reminders, weekly report reminders (enable/disable, thresholds, do-not-disturb)
- Notification center: reminder history, read/unread management, one-click mark-all-read
- Mood alert trigger: average of latest 3 mood records < 40
- Scheduled checks: background task runs hourly
- Frontend pages: reminder settings and notification center

## API

See the API summary section in [SPEC.md](./SPEC.md).

## Development Guidelines

### Code Style

- Follow PEP 8
- Use `snake_case` for function names
- Use `PascalCase` for class names

### Error Handling

- Unified API response format
- Exception capture with logging
- User-friendly error messages

## License

Copyright (c) 2026 Heart Garden Team. All rights reserved.

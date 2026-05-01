# Zeabur Deployment Report

## Summary
- Deployment method used: Prepared for Zeabur CLI via Dockerfile; remote deploy not run because no safe `ZEABUR_TOKEN` is available in this shell.
- Project: Not selected yet.
- Service: One Docker-backed Flask service serving the Vue static build.
- Region/server: Zeabur Free Plan target only; no paid server purchase.
- Public URL: Not generated yet.
- Health endpoint: `/api/health`
- Persistence: Temporary SQLite/log paths only for free demo deployment.
- Volume: None. Do not mount `/data` for this free demo plan.
- Domain: Use generated `*.zeabur.app` only.

## Local Changes
- Files changed: `app/main.py`, `Dockerfile`, `.dockerignore`, `.env.example`, `ZEABUR_DEPLOYMENT_REPORT.md`.
- Why changed: Read Zeabur `PORT`, serve the Vue SPA from Flask, keep SQLite/logs in temporary paths for the free demo, avoid shipping local secrets/data in Docker context, and document the deployment constraints.
- Existing unrelated working-tree changes are preserved: `start.bat`, `frontend/src/api/index.js`, `frontend/src/views/ChatPage.vue`, `services/llm_service.py`.

## Environment Variables Required
- `JWT_SECRET`: Required, set in Zeabur service variables with a strong random value.
- `SECRET_KEY`: Required, set in Zeabur service variables with a strong random value.
- `ENV=production`
- `DATABASE_PATH=/tmp/heart-garden/heart_garden.db`
- `LOG_DIR=/tmp/heart-garden/logs`
- `PORT`: Injected by Zeabur; do not hardcode.
- Optional app-specific variables: `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, or per-user LLM settings stored through the app UI.

## Validation
- Local Python compile: Passed with `python -m compileall -q app services`.
- Local frontend build: Passed with `npm --prefix frontend run build`.
- Local test suite: Passed with `python -m pytest` against a clean temporary SQLite database.
- Local health check: Passed using `PORT=18080`, temporary SQLite/log paths, and `STATIC_DIR=frontend/dist`.
- Local app check: `/` returned HTTP 200; `/api/` returned API info; register and diary creation succeeded.
- Docker build: Not run locally because Docker CLI is not installed or not in PATH.
- Zeabur build: Not run; blocked pending a newly generated, non-exposed token in `ZEABUR_TOKEN`.
- Runtime logs: Local runtime started with debug off and no startup exception.
- Public URL check: Pending Zeabur deploy.

## Cost Notes
- Plan: Zeabur Free Plan only.
- Server: Do not purchase a server.
- Volume/storage: None for this free demo; data may be lost after restart/redeploy/sleep.
- Domain: Generated `*.zeabur.app` only; no custom domain.
- AI/API usage: Zeabur AI Hub is not used. External model API costs depend on keys configured by users in the app.

## Remaining Manual Steps
- Revoke the Zeabur API key that was pasted in chat, then generate a new key.
- Set the new key only in the local shell as `ZEABUR_TOKEN`; do not write it to `.env` or tracked files.
- Run `npx zeabur@latest auth login --token $env:ZEABUR_TOKEN`.
- Run `npx zeabur@latest deploy` from the repository root.
- In Zeabur, set `JWT_SECRET` and `SECRET_KEY` service variables without printing them.
- Stop if Zeabur asks to subscribe, buy a server, mount a Volume, or bind a custom domain.
- After deploy, generate a `*.zeabur.app` domain and verify `/api/health`.

FROM node:22-slim AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=production \
    PORT=8080 \
    DATABASE_PATH=/tmp/heart-garden/heart_garden.db \
    LOG_DIR=/tmp/heart-garden/logs

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY services ./services
COPY --from=frontend-builder /build/frontend/dist ./app/static

RUN mkdir -p /tmp/heart-garden/logs

EXPOSE 8080

CMD ["python", "-m", "app.main"]

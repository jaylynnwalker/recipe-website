# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts ./
COPY src ./src
RUN npm run build

FROM nginx:1.27-alpine AS frontend
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/dist /usr/share/nginx/html
EXPOSE 8080

FROM python:3.12-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app
WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --create-home app
COPY backend/requirements.txt ./backend/requirements.txt
RUN python -m pip install --upgrade pip && python -m pip install -r backend/requirements.txt
COPY backend ./backend
COPY deploy/backend-entrypoint.sh ./deploy/backend-entrypoint.sh
RUN mkdir -p /data /media && chown -R app:app /app /data /media
USER app
EXPOSE 8000
ENTRYPOINT ["sh", "/app/deploy/backend-entrypoint.sh"]

#!/bin/sh
set -eu

python -m alembic -c backend/alembic.ini upgrade head
python -m backend.app.bootstrap
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'

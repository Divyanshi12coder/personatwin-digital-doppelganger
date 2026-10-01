#!/bin/sh
# Apply database migrations, then start the API.
set -e
echo "Running database migrations..."
alembic upgrade head
echo "Starting PersonaTwin API on port ${PORT:-8000}"
# Only trust X-Forwarded-For from these proxy addresses (real client IPs for rate limiting).
# Set FORWARDED_ALLOW_IPS="*" only when the API is reachable exclusively through your proxy.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}"

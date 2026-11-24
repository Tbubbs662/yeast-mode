#!/bin/bash
# Retake the README screenshots.
#
# Needs the dev app running (docker compose up -d). Seeds the `demo` account
# with sample data, then screenshots it with Playwright in a throwaway
# container, so nothing is installed on the host.
#
#   DEMO_PASSWORD=... docs/screenshots/take.sh
#
# Without DEMO_PASSWORD a random one is generated and printed.
set -euo pipefail
cd "$(dirname "$0")/../.."

PLAYWRIGHT_VERSION=1.65.2
DEMO_PASSWORD="${DEMO_PASSWORD:-$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')}"

echo "Seeding the demo account..."
docker compose exec -T -e DEMO_PASSWORD="$DEMO_PASSWORD" web python manage.py shell < docs/screenshots/seed_demo.py

echo "Taking screenshots..."
docker run --rm --network host \
    -e DEMO_PASSWORD="$DEMO_PASSWORD" \
    -e DEBIAN_FRONTEND=noninteractive \
    -e PIP_ROOT_USER_ACTION=ignore \
    -e PIP_DISABLE_PIP_VERSION_CHECK=1 \
    -v "$PWD/docs/screenshots:/work" \
    python:3.12-slim sh -c "
        apt-get update -qq >/dev/null && apt-get install -y -qq libatomic1 >/dev/null
        pip install -q playwright==$PLAYWRIGHT_VERSION >/dev/null
        playwright install --with-deps chromium >/dev/null
        python /work/take_screenshots.py
        chown $(id -u):$(id -g) /work/*.png
    "

echo "Done. Log in as demo / $DEMO_PASSWORD to look around."

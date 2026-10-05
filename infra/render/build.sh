#!/usr/bin/env bash
set -euo pipefail

export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/opt/render/project/src/.playwright-browsers}"

pip install -r requirements.txt
python -m playwright install chromium
python manage.py collectstatic --noinput

#!/bin/sh
set -e
echo '=== RAILWAY START SCRIPT ==='
echo "Date: $(date -u)"
echo 'Launching Python...'
exec python -u /app/bot.py

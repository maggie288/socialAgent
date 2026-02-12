#!/bin/sh
# Railway 等平台会注入 PORT，在此读取避免 CMD 中 $PORT 字面量
port="${PORT:-5000}"
exec gunicorn --bind "0.0.0.0:${port}" --workers 2 --threads 2 --access-logfile - --error-logfile - app:app

#!/bin/sh
# Railway 等平台会注入 PORT，用 sh 执行以正确展开变量
PORT=${PORT:-5000}
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 app:app

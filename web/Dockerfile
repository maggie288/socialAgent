# 生产镜像：Web 投喂入口（多语言）
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

ENV PORT=5000 FLASK_ENV=production
# 用脚本读取 PORT，避免 CMD 中 $PORT 在容器内未展开
CMD ["sh", "run.sh"]

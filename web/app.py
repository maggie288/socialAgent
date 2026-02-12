"""
Web 投喂入口：将主理人消息（文字/图片）转发到 OpenClaw。
支持多语言（i18n），配置通过环境变量。生产环境请用 Gunicorn 运行。
"""
import os
import json
import logging
from pathlib import Path
from flask import Flask, request, jsonify, render_template
import requests
from dotenv import load_dotenv

# 优先当前目录，再尝试项目根目录 .env
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

_is_production = os.environ.get("FLASK_ENV") == "production"
if _is_production:
    app.config["DEBUG"] = False
    logging.basicConfig(level=logging.INFO)
else:
    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "0") == "1"

logger = logging.getLogger(__name__)

_openclaw_url = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789").rstrip("/")
# OpenClaw 使用 OpenAI 兼容接口，路径为 /v1/chat/completions（非 /api/chat）
OPENCLAW_CHAT = _openclaw_url if "/v1/chat/completions" in _openclaw_url else f"{_openclaw_url}/v1/chat/completions"
OPENCLAW_TOKEN = os.environ.get("OPENCLAW_TOKEN", "")

TRANSLATIONS_DIR = Path(__file__).resolve().parent / "translations"
SUPPORTED_LANGS = ("zh", "en", "ja", "es", "fr")
DEFAULT_LANG = "zh"


def _load_translations(lang):
    path = TRANSLATIONS_DIR / f"{lang}.json"
    if not path.exists():
        path = TRANSLATIONS_DIR / "zh.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_locale():
    """优先 query ?lang=，其次 Accept-Language，默认 zh"""
    lang = request.args.get("lang", "").strip() or request.form.get("lang", "").strip()
    if lang and lang.split("-")[0] in [c for c in SUPPORTED_LANGS]:
        return lang.split("-")[0]
    al = request.headers.get("Accept-Language", "")
    for part in al.split(","):
        part = part.split(";")[0].strip().split("-")[0].lower()
        if part in SUPPORTED_LANGS:
            return part
    return DEFAULT_LANG


@app.route("/")
def index():
    """渲染投喂页面，支持 ?lang= 与 Accept-Language"""
    lang = get_locale()
    i18n = _load_translations(lang)
    return render_template("chat.html", lang=lang, i18n=i18n, supported_langs=SUPPORTED_LANGS)


@app.route("/api/i18n/<lang>")
def i18n(lang):
    """返回指定语言的翻译 JSON，供前端切换语言"""
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    return jsonify(_load_translations(lang))


@app.route("/api/chat", methods=["POST"])
def chat():
    """接收前端消息，转发给 OpenClaw；请求体可带 lang，使分身用该语言回复"""
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "message is required"}), 400

    lang = (data.get("lang") or get_locale() or DEFAULT_LANG).split("-")[0]
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG

    # 语言提示：让 OpenClaw 用用户语言回复（若 API 支持 system/context）
    lang_hint = _lang_reply_hint(lang)
    messages = [{"role": "user", "content": user_message}]
    if lang_hint:
        messages = [{"role": "system", "content": lang_hint}, *messages]

    headers = {
        "Authorization": f"Bearer {OPENCLAW_TOKEN}",
        "Content-Type": "application/json",
        "x-openclaw-agent-id": "main",
    }
    # OpenAI 兼容格式：model 必填，OpenClaw 用 openclaw 或 openclaw:main
    payload = {"model": "openclaw", "messages": messages, "stream": False}

    try:
        resp = requests.post(OPENCLAW_CHAT, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        # 兼容 OpenAI 返回：choices[0].message.content
        return jsonify(data)
    except requests.RequestException as e:
        logger.warning("chat upstream error: %s", e)
        return jsonify({"error": str(e)}), 500


def _lang_reply_hint(lang):
    hints = {
        "zh": "Reply in Simplified Chinese (中文).",
        "en": "Reply in English.",
        "ja": "Reply in Japanese (日本語).",
        "es": "Reply in Spanish (Español).",
        "fr": "Reply in French (Français).",
    }
    return hints.get(lang, "")


@app.route("/api/upload", methods=["POST"])
def upload():
    """接收图片/文件，转发给 OpenClaw（多模态投喂）。
    具体 multipart 格式需与 OpenClaw 文档对齐，此处为占位实现。
    """
    file = request.files.get("file") or request.files.get("image")
    if not file:
        return jsonify({"error": "file or image required"}), 400

    lang = (request.form.get("lang") or get_locale() or DEFAULT_LANG).split("-")[0]
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    lang_hint = _lang_reply_hint(lang)
    messages = [
        {"role": "user", "content": f"[User uploaded an image: {file.filename}]"}
    ]
    if lang_hint:
        messages = [{"role": "system", "content": lang_hint}, *messages]

    try:
        file.read()  # consume for now
        headers = {
            "Authorization": f"Bearer {OPENCLAW_TOKEN}",
            "Content-Type": "application/json",
            "x-openclaw-agent-id": "main",
        }
        payload = {"model": "openclaw", "messages": messages, "stream": False}
        resp = requests.post(OPENCLAW_CHAT, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as e:
        logger.warning("upload upstream error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.after_request
def add_security_headers(response):
    if _is_production:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    return response


@app.route("/health")
def health():
    """健康检查，供负载均衡/容器编排使用"""
    return jsonify({"status": "ok", "service": "foodie-twin-web"})


@app.route("/ready")
def ready():
    """就绪检查：OpenClaw 可达性可选，此处仅返回 200"""
    return "", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = app.config.get("DEBUG", False)
    app.run(host="0.0.0.0", port=port, debug=debug)

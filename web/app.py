"""
Web 投喂入口：将主理人消息（文字/图片）转发到 OpenClaw。
支持注册/登录，会话鉴权，以及 Feed / 分享上传页面拆分。
"""
import os
import json
import logging
from datetime import datetime
from functools import wraps
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# 优先当前目录，再尝试项目根目录 .env
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

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
DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_FILE = DATA_DIR / "users.json"
SHARES_FILE = DATA_DIR / "shares.json"
UPLOAD_DIR = Path(__file__).resolve().parent / "static" / "uploads"
SUPPORTED_LANGS = ("zh", "en", "ja", "es", "fr")
DEFAULT_LANG = "zh"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_RECOMMENDATIONS = [
    {
        "title": "今日轻盈沙拉碗",
        "desc": "牛油果 + 鹰嘴豆 + 烤南瓜，适合午餐补能量。",
        "tag": "低负担",
    },
    {
        "title": "一锅番茄海鲜炖饭",
        "desc": "30 分钟完成，海鲜鲜味和番茄酸甜很平衡。",
        "tag": "快手",
    },
    {
        "title": "豆乳抹茶布丁",
        "desc": "少糖甜品，口感细腻，适合晚餐后小确幸。",
        "tag": "甜品",
    },
]


def _load_json(path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_users():
    users = _load_json(USERS_FILE, [])
    return {u.get("username", ""): u for u in users if u.get("username")}


def _save_users(users_map):
    _save_json(USERS_FILE, list(users_map.values()))


def _load_shares():
    shares = _load_json(SHARES_FILE, [])
    if not isinstance(shares, list):
        return []
    return shares


def _save_shares(shares):
    _save_json(SHARES_FILE, shares)


def _current_user():
    return session.get("username")


def _is_api_request():
    return request.path.startswith("/api/")


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if _current_user():
            return view_func(*args, **kwargs)
        if _is_api_request():
            return jsonify({"error": "login required"}), 401
        return redirect(url_for("login", next=request.path))

    return wrapped


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
    if _current_user():
        return redirect(url_for("feed"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if _current_user():
        return redirect(url_for("feed"))

    error = ""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not username or not password:
            error = "用户名和密码不能为空。"
        elif len(username) < 3:
            error = "用户名至少 3 个字符。"
        elif len(password) < 6:
            error = "密码至少 6 位。"
        elif password != confirm_password:
            error = "两次输入密码不一致。"
        else:
            users_map = _load_users()
            if username in users_map:
                error = "该用户名已存在。"
            else:
                users_map[username] = {
                    "username": username,
                    "password_hash": generate_password_hash(password),
                    "created_at": datetime.utcnow().isoformat(),
                }
                _save_users(users_map)
                session["username"] = username
                return redirect(url_for("feed"))

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if _current_user():
        return redirect(url_for("feed"))

    error = ""
    next_url = request.args.get("next") or url_for("feed")
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        users_map = _load_users()
        user = users_map.get(username)

        if not user or not check_password_hash(user.get("password_hash", ""), password):
            error = "用户名或密码错误。"
        else:
            session["username"] = username
            if next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("feed"))

    return render_template("login.html", error=error, next_url=next_url)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/feed")
@login_required
def feed():
    shares = _load_shares()
    return render_template(
        "feed.html",
        username=_current_user(),
        recommendations=DEFAULT_RECOMMENDATIONS,
        shares=list(reversed(shares)),
    )


@app.route("/share")
@login_required
def share_page():
    return render_template("share.html", username=_current_user())


@app.route("/api/i18n/<lang>")
def i18n(lang):
    """返回指定语言的翻译 JSON，供前端切换语言"""
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    return jsonify(_load_translations(lang))


@app.route("/api/chat", methods=["POST"])
@login_required
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
@login_required
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


@app.route("/api/feed")
@login_required
def feed_api():
    shares = list(reversed(_load_shares()))
    return jsonify({"recommendations": DEFAULT_RECOMMENDATIONS, "shares": shares})


@app.route("/api/share", methods=["POST"])
@login_required
def share():
    text = (request.form.get("text") or "").strip()
    file = request.files.get("image")
    if not text and not file:
        return jsonify({"error": "text or image required"}), 400

    image_url = ""
    if file and file.filename:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = secure_filename(file.filename)
        saved_name = f"{timestamp}_{_current_user()}_{filename}"
        destination = UPLOAD_DIR / saved_name
        file.save(destination)
        image_url = f"/static/uploads/{saved_name}"

    shares = _load_shares()
    share_item = {
        "username": _current_user(),
        "text": text,
        "image_url": image_url,
        "created_at": datetime.utcnow().isoformat(),
    }
    shares.append(share_item)
    shares = shares[-200:]
    _save_shares(shares)
    return jsonify({"ok": True, "share": share_item})


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

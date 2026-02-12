# 生产环境部署方案

本文档说明如何将 **Web 投喂入口**（多语言版）部署到生产环境。OpenClaw 需单独部署，此处仅部署 Web 转发层。

---

## 一、生产环境要求

| 项目 | 说明 |
|------|------|
| 运行方式 | 使用 **Gunicorn**，不要用 `flask run` |
| 环境变量 | `FLASK_ENV=production`；`OPENCLAW_URL`、`OPENCLAW_TOKEN` 必填 |
| 健康检查 | `GET /health` 返回 `{"status":"ok"}`；`GET /ready` 返回 200 |
| 日志 | 标准输出，由宿主机或编排系统收集 |

---

## 二、环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `OPENCLAW_URL` | 是 | OpenClaw 实例地址，如 `http://your-openclaw-host:18789` |
| `OPENCLAW_TOKEN` | 是 | OpenClaw API Token |
| `PORT` | 否 | 监听端口，默认 5000 |
| `FLASK_ENV` | 生产建议 | 设为 `production` 关闭 debug、启用安全头 |
| `FLASK_DEBUG` | 否 | 仅开发时设为 `1` |

---

## 三、部署方式

### 方式 A：Docker（推荐）

适用：本机、自有服务器、云主机。

```bash
# 在项目根目录
cp .env.example .env
# 编辑 .env，填写 OPENCLAW_URL、OPENCLAW_TOKEN

docker compose up -d
# 访问 http://localhost:5000（或 .env 中 PORT）
```

- 镜像构建：`docker compose build`
- 查看日志：`docker compose logs -f web`
- 若 OpenClaw 与 Web 同机：可把 `OPENCLAW_URL` 设为 `http://host.docker.internal:18789`（Mac/Windows）；Linux 可用 `http://<宿主机内网IP>:18789` 或同一 compose 内服务名。

### 方式 B：宿主机直接跑 Gunicorn

适用：VPS、云主机，无 Docker。

```bash
cd web
pip install -r requirements.txt
export FLASK_ENV=production
export OPENCLAW_URL="http://你的OpenClaw地址:18789"
export OPENCLAW_TOKEN="你的Token"
export PORT=5000

gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 --access-logfile - --error-logfile - app:app
```

或使用 systemd（`/etc/systemd/system/foodie-twin-web.service`）：

```ini
[Unit]
Description=Foodie Twin Web
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/socialAgent/web
Environment=FLASK_ENV=production
EnvironmentFile=/path/to/socialAgent/.env
ExecStart=/path/to/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 方式 C：反向代理（Nginx / Caddy）

在 Gunicorn 前加一层反向代理，做 HTTPS、域名、限流等。

**Nginx 示例**（HTTPS 需自行配置证书）：

```nginx
upstream foodie_twin_web {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    location / {
        proxy_pass http://foodie_twin_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /health {
        proxy_pass http://foodie_twin_web;
    }
}
```

**Caddy 示例**（自动 HTTPS）：

```
your-domain.com {
    reverse_proxy localhost:5000
}
```

### 方式 D：PaaS（Railway / Render / Fly.io）

- **Railway**：连接 GitHub 仓库，根目录设为 `web` 或使用 Dockerfile；在 Variables 中配置 `OPENCLAW_URL`、`OPENCLAW_TOKEN`、`FLASK_ENV=production`；Start Command 留空则用 Dockerfile 的 CMD，否则填 `gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app`（注意 PaaS 通常通过 `PORT` 注入端口）。
- **Render**：同上，Build Command 可选 `pip install -r requirements.txt`，Start Command 用 Gunicorn 并绑定 `$PORT`。
- **Fly.io**：`fly launch` 在 `web` 目录或项目根（Dockerfile 指向 web）；`fly secrets set OPENCLAW_URL=... OPENCLAW_TOKEN=...`；应用监听 `0.0.0.0:8080` 时在 `fly.toml` 中配置 `internal_port = 8080`。

PaaS 部署时注意：OpenClaw 需对公网可访问，或通过内网/隧道打通；`OPENCLAW_URL` 填公网或 PaaS 可访问的地址。

---

## 四、健康检查与就绪

- **存活**：`GET /health` → 200，body `{"status":"ok","service":"foodie-twin-web"}`。
- **就绪**：`GET /ready` → 200，无 body。

负载均衡或 Kubernetes 可配置：

- HTTP 存活探针：`/health`
- 就绪探针：`/ready`

---

## 五、安全检查清单

- [ ] 生产环境未设置 `FLASK_DEBUG=1`
- [ ] `FLASK_ENV=production` 已设置
- [ ] `OPENCLAW_TOKEN` 仅通过环境变量或密钥管理注入，未写进代码或仓库
- [ ] 对外提供 HTTPS（通过 Nginx/Caddy 或 PaaS）
- [ ] 如需限制来源，在反向代理层做 IP/地域或认证

---

## 六、故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 502 Bad Gateway | Gunicorn 未启动或崩溃 | 查看应用日志；确认 PORT 与反向代理一致 |
| 发消息无回复 | OpenClaw 不可达或 Token 错误 | 检查 `OPENCLAW_URL`、`OPENCLAW_TOKEN`；从部署环境 curl OpenClaw 健康接口 |
| 多语言不生效 | 前端未带 `lang` 或后端未收到 | 确认请求体含 `lang`；确认 `/api/i18n/<lang>` 可访问 |

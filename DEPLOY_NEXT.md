# 阿里云已配置好 — 继续部署所需信息与下一步

你已有一台阿里云 OpenClaw，接下来需要**两条信息**用于后续部署，然后按顺序做 **Moltbook 认领** 和 **Web 公网部署**。

---

## 一、需要你准备/确认的信息

| 信息 | 说明 | 哪里用 |
|------|------|--------|
| **OPENCLAW_URL** | OpenClaw 访问地址，形如 `http://你的公网IP:18789`（不要漏端口、不要用 https 除非你已配证书） | 本地 .env、Railway/Render 环境变量 |
| **OPENCLAW_TOKEN** | 在 OpenClaw Web 控制台「获取 Token」或 SSH 里查到的访问 Token | 同上 |
| **Twitter/X 账号** | 能登录、能发推即可，无需把账号密码给任何人 | 仅用于在 Moltbook 打开认领链接、发一条验证推文 |
| **Railway 或 Render 账号**（二选一） | 用于把 Web 投喂入口部署到公网 | 部署 Web 时登录并连接本仓库 |

**请把 OPENCLAW_URL 和 OPENCLAW_TOKEN 填到项目根目录的 `.env` 里**（不要提交到 Git，不要发到聊天里），格式如下：

```bash
# 项目根目录 .env
OPENCLAW_URL=http://你的公网IP:18789
OPENCLAW_TOKEN=你从OpenClaw获取的Token
FLASK_ENV=production
```

填好后可先本地验证（见下文），再部署到公网。

---

## 二、下一步操作顺序

### 1. 本地先验证（可选但推荐）

在项目根目录执行：

```bash
# 确保 .env 已填 OPENCLAW_URL 和 OPENCLAW_TOKEN
docker compose up -d
# 浏览器打开 http://localhost:5000，发一条消息，能收到分身回复即说明打通
```

或不用 Docker，直接跑 Web：

```bash
cd web
pip install -r requirements.txt
# 会读取根目录 .env
python app.py
# 浏览器打开 http://localhost:5001（或 5000），测试对话
```

若本地能正常对话，说明 OpenClaw 与 Web 已打通，可以继续部署到公网。

---

### 2. 在 Moltbook 上注册并认领分身（必须在 OpenClaw 自己的 Web 控制台里做）

**不要在我们的投喂页面里发这句指令**，否则会报 405 或无法执行「Read https://moltbook.com/skill.md」。必须到 OpenClaw 原生界面里操作。

- 打开 OpenClaw **Web 控制台**：`http://你的公网IP:端口`（例如 `http://47.85.44.90:19448`），用 Token 登录。
- 在对话里**先安装本仓库的美食品味主理人技能**（二选一）：
  - **方式 A**：把本仓库里的 `skills/foodie_taste_curator_full.skill.md` 内容复制到一条消息里，对 Agent 说：「请安装下面这份 Skill」并粘贴全文；  
  - **方式 B**：若 OpenClaw 能访问你本机或 GitHub 原始文件地址，可说：「Read [该文件的 URL] and install this skill.」
- 安装完成后，对 Agent 说（把 `你的英文名` 换成你想要的用户名）：

  ```text
  Read https://moltbook.com/skill.md and follow the instructions to join Moltbook. Username: 你的英文名_eats
  ```

- Agent 会回复一个 **认领链接**（如 `https://moltbook.com/claim/xxx`）。
- 用**你的 Twitter/X 账号**在浏览器打开该链接，按页面提示**发一条推文**完成验证。
- 认领成功后，分身即在 Moltbook 上线，会按 Skill 自动发帖、评论。

**若在投喂页面发消息出现 405 Method Not Allowed**：本仓库的 Web 已改为调用 OpenClaw 的 `POST /v1/chat/completions` 接口。若仍 405，需在 OpenClaw 服务器上开启该接口（部分版本默认关闭），在配置中设置 `gateway.http.endpoints.chatCompletions.enabled: true`，或查阅阿里云/OpenClaw 文档确认 Chat Completions 已启用。

---

### 3. 把 Web 投喂入口部署到公网

**不一定要部署到阿里云**。二选一即可：

- **选项 A**：部署到 **Railway / Render**（推荐，连 GitHub 即可，免管服务器），见下文。
- **选项 B**：部署到 **阿里云**（和 OpenClaw 同云，可用同一台或再买一台轻量/ECS），见 [DEPLOY.md](./DEPLOY.md) 或下文「部署到阿里云」小节。

这样任何人通过一个链接（https 或 http）就能和你的分身聊天。

**Railway：**

1. 打开 [railway.app](https://railway.app/)，用 GitHub 登录，New Project → Deploy from GitHub repo，选本仓库。
2. 在项目设置里把 **Root Directory** 设为 `web`（若没有此选项，则构建时在 `web` 下执行命令）。
3. 在 Variables 里添加：
   - `OPENCLAW_URL` = 你的 OpenClaw 地址（如 `http://你的公网IP:18789`）
   - `OPENCLAW_TOKEN` = 你的 Token
   - `FLASK_ENV` = `production`
4. Railway 会自动用 `web/Procfile` 或检测 Python 并启动；若需指定启动命令，填：  
   `gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 app:app`
5. 部署完成后会生成一个 **https 链接**，即你的公网投喂入口。

**Render：**

1. 打开 [render.com](https://render.com/)，用 GitHub 登录，New → Web Service，选本仓库。
2. 设置：**Root Directory** 填 `web`，Build Command：`pip install -r requirements.txt`，Start Command：`gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 2 app:app`。
3. 在 Environment 里添加 `OPENCLAW_URL`、`OPENCLAW_TOKEN`、`FLASK_ENV=production`。
4. 部署完成后用给出的 **https 链接** 访问。

**注意**：Railway/Render 所在机房要能访问你的阿里云公网 IP:18789。若 OpenClaw 仅允许特定 IP 访问，需在阿里云安全组里放行 Railway/Render 的出口 IP，或暂时对 `0.0.0.0/0` 开放 18789（仅测试时建议，长期建议收紧）。

---

## 三、小结：你现在要做的

1. **把 OPENCLAW_URL、OPENCLAW_TOKEN 填到项目根目录 `.env`**（不提交、不发给别人）。
2. **（推荐）本地跑一遍** `docker compose up -d` 或 `cd web && python app.py`，浏览器里发消息验证能收到回复。
3. **Moltbook 认领**：在 OpenClaw Web 里安装美食品味主理人 Skill，执行加入 Moltbook 的指令，用 Twitter/X 打开认领链接并发推验证。
4. **公网 Web**：用 Railway 或 Render 部署本仓库的 `web`，环境变量填同样的 `OPENCLAW_URL`、`OPENCLAW_TOKEN`、`FLASK_ENV=production`，拿到 https 链接即可分享给任何人使用。

若某一步报错，把**报错信息或界面截图**（注意打码 Token）发出来，我可以按步骤帮你排查。

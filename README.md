# Social Agent · 美食品味主理人

基于 [skills.md](./skills.md) 与 [solution.md](./solution.md) 方案：在 Moltbook 上用 OpenClaw Agent 作为「美食品味主理人」数字分身，支持丝滑投喂（外卖截图、定位打卡、菜品拍照）与自建 Web 投喂入口。**Web 投喂入口支持多语言（中/英/日/西/法），方便全球用户分享。**

## 项目结构

```
socialAgent/
├── skills.md                    # Cursor 开发技能说明（优先阅读）
├── solution.md                  # 方案讨论全文
├── skills/
│   └── foodie_taste_curator_full.skill.md   # OpenClaw 完整技能（给 Agent 安装）
├── memory/                     # 部署时映射到 ~/.openclaw/memory/
│   ├── .gitkeep
│   └── taste_profile.md.example # 品味档案示例
├── web/                        # 自建 Web 投喂入口（可选，多语言）
│   ├── app.py
│   ├── requirements.txt
│   ├── translations/           # zh, en, ja, es, fr
│   └── templates/
│       └── chat.html
├── .env.example
└── README.md
```

## 快速开始

### 1. 安装美食品味主理人技能（OpenClaw 环境）

在已部署的 OpenClaw 中，让 Agent 加载技能：

```
Read /path/to/skills/foodie_taste_curator_full.skill.md and install this skill.
```

然后按技能内「第十章」对主理人发送激活指令（外卖截图、定位打卡、菜品拍照）。

### 2. 运行 Web 投喂入口（可选）

```bash
cd web
cp ../.env.example ../.env
# 编辑 .env，填写 OPENCLAW_URL 和 OPENCLAW_TOKEN
pip install -r requirements.txt
python app.py
```

浏览器打开 `http://localhost:5000`（或 `?lang=en` 等切换语言），即可用聊天页面向分身发文字/图片。右上角可切换语言（中文 / English / 日本語 / Español / Français），分身会按所选语言回复。

### 3. 品味档案

- 开发/占位：使用项目内 `memory/`，可复制 `memory/taste_profile.md.example` 为 `memory/taste_profile.md` 编辑。
- 生产：部署时将 `memory/` 映射到 `~/.openclaw/memory/`，Token 与 state 文件勿提交仓库。

## 开发约定

- 开发与迭代以 [skills.md](./skills.md) 为准：目标产物、路径、发帖模板、丝滑投喂协议、安全与合规。
- 修改 Skill 时保持 YAML front matter 与「配置与常量」一致；限流与路径集中维护。
- Web 入口的 Token 与服务器地址仅通过环境变量或 `.env` 配置，不写死在代码中。

## 生产部署

- **不懂部署、从本机代码到公网**：直接看 **[本地代码如何部署](docs/本地代码如何部署.md)**，用最简单的话说明「要部署什么、准备什么、Railway 或阿里云两种方式一步步怎么做」。
- 使用 **Gunicorn** 运行，勿用 Flask 开发服务器。环境变量见 `.env.example`，生产务必设置 `FLASK_ENV=production`。
- **要让分身在互联网真实运行（Moltbook + 公网投喂）**：先看 **[MOLTBOOK_DEPLOY.md](./MOLTBOOK_DEPLOY.md)**，其中列出需要提前注册的账号及完整部署顺序。
- 仅部署 Web 层：见 **[DEPLOY.md](./DEPLOY.md)**（Docker / Gunicorn / Nginx / Railway / Render / Fly.io）。

## 参考

- Moltbook 注册：Agent 读 `https://moltbook.com/skill.md` 并按说明注册，主理人用 X(Twitter) 认领。
- 投喂入口首选：飞书（或企业微信/钉钉/Telegram）；本仓库 Web 为自建可选方案，可分享链接到微信/飞书使用。

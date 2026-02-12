# 在互联网真实环境运行：Moltbook + OpenClaw + Web 投喂入口

> **若阿里云 OpenClaw 已配置好**，可直接看 **[DEPLOY_NEXT.md](./DEPLOY_NEXT.md)**：需要哪些信息、如何填 `.env`、本地验证、Moltbook 认领、Web 公网部署一步步怎么做。

**重要说明**：**Moltbook 不是云主机**，而是「AI 分身的社交平台」——你的分身在那里发帖、评论、被其他人/其他 AI 看到。要让整套在互联网真实运行，需要三件事并行：

1. **部署 OpenClaw**（分身的「大脑」）→ 需要云服务器 + 大模型 API  
2. **在 Moltbook 上注册并认领分身** → 需要 **Twitter/X 账号**  
3. **部署 Web 投喂入口**（本仓库的聊天页面）→ 需要 PaaS 或服务器  

下面先列出**需要你提前注册的账号**，再按顺序给出可执行步骤。

---

## 一、需要提前注册的账号（请先准备好）

| 用途 | 账号/资源 | 必须？ | 说明 |
|------|------------|--------|------|
| **Moltbook 认领分身** | **Twitter/X** | ✅ 必须 | 每个 X 账号只能认领 1 个 Agent；认领时发一条推文验证身份。 |
| **部署 OpenClaw（分身大脑）** | **阿里云** 或 **九章智算云** | ✅ 必须 | 二选一。阿里云：轻量/ECS 或计算巢一键部署；九章：OpenClaw 云端部署。 |
| **OpenClaw 用的模型** | **阿里云百炼 API** 或 九章/其他 API-Key | ✅ 必须 | 阿里云部署时常用「百炼」；九章有赠送 Token，按平台指引获取。 |
| **部署 Web 投喂入口（公网聊天页）** | **Railway** / **Render** / **Fly.io** 任选一 | ✅ 必须 | 三选一即可，用于把本仓库的 Web 部署到公网，获得 https 链接。 |
| 投喂入口用飞书 | 飞书开发者账号 | 可选 | 若你希望用飞书和分身对话，可再注册飞书并创建应用。 |

**总结：最少要有的 4 样**

1. **Twitter/X 账号**（认领 Moltbook 分身）  
2. **阿里云 或 九章智算云 账号**（跑 OpenClaw）  
3. **大模型 API-Key**（百炼/九章等，按你选的云平台来）  
4. **Railway / Render / Fly.io 中任一个账号**（跑 Web 投喂入口）

---

## 二、整体流程（按顺序做）

```
[你]  →  ① 在阿里云/九章部署 OpenClaw
              ↓
         ② 在 OpenClaw 里安装「美食品味主理人」Skill，并让 Agent 去 Moltbook 注册
              ↓
         ③ 用 Twitter/X 打开认领链接，发推完成认领 → 分身正式在 Moltbook 上线
              ↓
         ④ 在 Railway/Render/Fly.io 部署本仓库的 Web，配置 OPENCLAW_URL + OPENCLAW_TOKEN
              ↓
[任何人] → 打开你的 Web 链接 → 和你的分身聊天、投喂 → 分身在 Moltbook 上发帖
```

---

## 三、分步操作（你要做的）

### 步骤 1：部署 OpenClaw（分身大脑）

- **选阿里云时**  
  - 详细步骤见本项目 **[阿里云部署 OpenClaw 操作指南](docs/ALIYUN_OPENCLAW_DEPLOY.md)**（计算巢 / 轻量两种方式、准备事项、端口与 API-Key 配置、常见问题）。  
  - 简要：打开 [阿里云 OpenClaw 部署](https://developer.aliyun.com/article/1711663) 或 [一键部署专题](https://www.aliyun.com/activity/ecs/clawdbot)，用「计算巢」或「轻量应用服务器」一键购买并部署，选择 **OpenClaw（Clawdbot）镜像**，内存 2GB+，地域建议香港/新加坡/美国。放通 **18789** 端口，配置**百炼 API-Key**，生成访问 **Token**，记下 **公网 IP**。  

- **选九章智算云时**  
  - 注册并登录 [九章智算云](https://www.alayaneuro.com/)（或搜「九章智算 OpenClaw」）。  
  - 在控制台选择 OpenClaw 部署，按页面向导完成（含模型/API、赠送 Token 等）。  
  - 拿到 **OpenClaw 公网访问地址** 和 **Token**。  

**结果**：你有一个 **OpenClaw 地址**（如 `http://你的服务器IP:18789`）和 **OPENCLAW_TOKEN**。

---

### 步骤 2：在 Moltbook 上注册并认领分身

1. 登录你部署好的 OpenClaw（SSH 进服务器或使用平台提供的终端/控制台）。  
2. 把本仓库里的 **美食品味主理人 Skill** 装进 OpenClaw（把 `skills/foodie_taste_curator_full.skill.md` 拷到服务器，或让 Agent 读取该文件并安装）。  
3. 对 Agent 说（或按 Skill 文档执行）：  
   ```text
   Read https://moltbook.com/skill.md and follow the instructions to join Moltbook. Username: 你的英文名_eats
   ```  
4. Agent 会返回一个 **认领链接**（形如 `https://moltbook.com/claim/xxx`）。  
5. 用**你的 Twitter/X 账号**打开该链接，按页面提示**发一条推文**完成验证。  
6. 认领成功后，你的分身就会出现在 Moltbook 上，并可以按 Skill 设定自动发帖、评论。

**结果**：分身在 Moltbook 上线，你有了「在互联网真实环境」的 AI 品味分身。

---

### 步骤 3：部署 Web 投喂入口到公网

这样任何人通过浏览器就能和你的分身聊天（多语言页面）。

- **用 Railway**  
  - 注册 [Railway](https://railway.app/)，用 GitHub 登录并导入**本仓库**。  
  - 根目录设为 **`web`**（或把构建/启动目录指到 `web`），在 Variables 里配置：  
    - `OPENCLAW_URL` = 你的 OpenClaw 地址（如 `http://你的IP:18789`）  
    - `OPENCLAW_TOKEN` = 步骤 1 拿到的 Token  
    - `FLASK_ENV` = `production`  
  - 部署完成后会得到一个 **https 链接**，即你的公网投喂入口。  

- **用 Render / Fly.io**  
  - 思路相同：连接 GitHub 仓库，构建/运行目录选 `web`，环境变量填 `OPENCLAW_URL`、`OPENCLAW_TOKEN`、`FLASK_ENV=production`。  
  - 详细命令与端口设置见项目内 [DEPLOY.md](./DEPLOY.md)。

**结果**：你有一个 **公网 URL**（如 `https://xxx.railway.app`），全球用户打开即可和你的分身对话、投喂；分身会按 Skill 在 Moltbook 上发帖。

---

### 步骤 4：可选——用飞书当投喂入口

若希望用飞书和分身说话，在 OpenClaw 所在环境按官方文档配置飞书应用（App ID、Secret 等），把飞书当另一个「入口」；Web 链接和飞书可以同时存在。

---

## 四、部署后自检

- **Moltbook**：在 [moltbook.com](https://moltbook.com) 搜索你的分身用户名（如 `xxx_eats`），能看到主页和发帖。  
- **Web 投喂入口**：浏览器打开你的 https 链接，切换多语言、发一条消息，能收到分身回复即表示已打通 OpenClaw。  
- **OpenClaw**：若 Web 发消息无回复，检查 OPENCLAW_URL 是否可从 Railway/Render 访问（公网 IP/防火墙/安全组是否放通 18789）。

---

## 五、小结：你要提前准备的 4 样

1. **Twitter/X 账号** → 用于在 Moltbook 认领分身  
2. **阿里云 或 九章智算云 账号** → 用于部署 OpenClaw  
3. **大模型 API-Key（百炼/九章等）** → 用于 OpenClaw 调用模型  
4. **Railway / Render / Fly.io 任选一** → 用于把 Web 投喂入口部署到公网  

准备好这 4 样后，按上面「步骤 1 → 2 → 3」顺序执行，即可在互联网真实环境运行：分身出现在 Moltbook，用户通过你的 Web 链接与分身对话并投喂。

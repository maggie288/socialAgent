# Social Agent 项目 · Cursor 开发技能说明

> 本文档基于 `solution.md` 方案讨论整理，供在 Cursor 中 24 小时不间断开发时使用。开发时请优先遵循本技能中的约定与结构。

---

## 一、方案讨论总结

### 1.1 产品方向演进

| 阶段 | 方向 | 结论 |
|------|------|------|
| 初期 | 约饭 + 位置 + 商品 + AA + 下单 全功能平台 | 被劝退，过重 |
| 中期 | 微信群机器人、群共享美食榜、闲鱼卖头像、个人美食主页 | 验证过，但依赖微信生态 |
| 后期 | 微信生态封闭 → 考虑开放方案 | 选定 Moltbook + 认可 Farcaster |
| **终态** | **Moltbook：AI 分身替我社交、替我扩散品味** | **主方案**；Farcaster 作为开放协议品味名片备选 |

核心定位：**不是做给别人用的产品，而是让 AI 分身成为主理人个人品味的数字孪生体**——在 Moltbook 上用主人的口吻、标准、照片替他分享、社交、吸引同频食客。

### 1.2 核心能力

- **美食品味主理人（OpenClaw Agent）**
  - 在 Moltbook 注册/认领身份，按 4 小时心跳自动发帖、评论。
  - 只推荐主理人「吃过的店」；说具体话（不说“很好吃”，说“熟成牛排外层焦脆、中心温润”）；不讨好、不营销。
- **丝滑投喂**
  - 品味数据来源：外卖截图、到店定位打卡、菜品拍照、语音随手记、每周一相册反刍补档。
  - 所有投喂均需主理人主动发起；分身不偷窥、不擅自爬取未分享内容。

### 1.3 投喂入口

- **首选**：飞书（个人可建应用，支持图文/位置/语音，身份隔离清晰）。
- **备选**：企业微信、钉钉、QQ、Telegram（OpenClaw 官方支持的 IM）。
- **自建**：简单 Web 页面（Flask + HTML 聊天界面），可分享到微信/飞书；或阿里云 AppFlow 生成 H5 集成 OpenClaw。

多名主理人：建议每人独立 OpenClaw 实例 + 独立飞书应用（或单机多实例 + 多飞书机器人）。

### 1.4 技术栈与依赖

- **运行时**：OpenClaw（阿里云/腾讯云/九章智算一键部署）。
- **Moltbook**：skill.md、heartbeat.md、messaging.md；API 注册/认领/发帖/评论；Bearer Token 存 `~/.openclaw/memory/moltbook_token.txt`。
- **限流**：发帖每 30 分钟 ≤1 帖；评论每小时 ≤50 条；点赞每小时 ≤100 次；API 约 100 次/分钟。
- **依赖技能**：`multimodal-screenshot-parser`（外卖/截图解析）、`reverse-geocoding`（定位→店名）、可选 `image-understanding`（菜品识别）。

---

## 二、项目在 Cursor 中的开发约定

### 2.1 目标产物

在 Cursor 中开发并维护的，主要包括：

1. **OpenClaw 用 Skill 文件**（给 Agent 在 Moltbook 上用的「美食品味主理人」完整技能）
   - 建议文件名：`foodie_taste_curator_full.skill.md` 或 `foodie_taste_curator.md`。
   - 内容需包含：YAML front matter、注册与身份、限流、发帖/评论/被@逻辑、4h 心跳、品味档案、丝滑投喂协议、安全与退出、安装验证清单。
2. **丝滑投喂模块**（可单独或合并进主 Skill）
   - 外卖截图即认证、定位打卡即建档、菜品拍照即补全、主动反刍（每周一）。
3. **自建 Web 投喂入口**（可选，支持多语言）
   - 后端：Flask，路由如 `/`、`/api/chat`、`/api/upload`，转发到 OpenClaw API；支持 `?lang=` 与 `Accept-Language`，并将语言偏好传给 OpenClaw 以便分身用用户语言回复。
   - 前端：移动优先的聊天页（支持文字、图片、位置），可分享到微信/飞书；UI 文案来自 `web/translations/{lang}.json`，提供语言切换器。

### 2.2 关键路径与文件（约定）

- 品味档案：`~/.openclaw/memory/taste_profile.md`（主理人美食品味档案，含口味偏好、餐厅数据库、待完善/待探索清单）。
- 状态与 Token：`~/.openclaw/memory/moltbook_state.json`、`~/.openclaw/memory/moltbook_token.txt`（仅本地，不提交代码库）。
- 食物照片：`~/.openclaw/memory/food_photos/`（按时间戳或菜品命名）。
- Moltbook 技能目录：`~/.openclaw/skills/moltbook/`（SKILL.md、HEARTBEAT.md、MESSAGING.md）。

开发时若需模拟或占位，可在项目内使用 `./memory/`、`./skills/` 等相对路径，并在文档中注明「部署时映射到 ~/.openclaw/」。

### 2.3 多语言（i18n）——全世界的人都可以分享

- **目标**：任何地区用户都能用自己语言使用投喂入口、在 Moltbook 上分享品味；UI 与 Agent 回复均支持多语言。
- **支持语言**：至少 **简体中文（zh）、英文（en）**；建议扩展：繁体中文（zh-TW）、日语（ja）、西班牙语（es）、法语（fr）。语言代码采用 BCP 47（如 zh、en、ja、es、fr）。
- **Web 投喂入口**：
  - 语言切换：URL 参数 `?lang=en` 或用户界面语言选择器；优先使用用户选择，其次浏览器 `Accept-Language`，默认 `zh`。
  - 文案存放：`web/translations/{lang}.json`，键名与页面元素一致，避免硬编码中文/英文。
  - 前端：页面标题、描述、占位符、按钮、欢迎语、错误提示等全部走翻译键；时间、数字按当前 locale 格式化。
- **API 与 Agent**：
  - 请求中携带语言偏好：`/api/chat` 请求体可含 `lang`（如 `en`），或后端根据 `Accept-Language` 解析；转发给 OpenClaw 时在 system/context 中注明「Reply in {lang}」或等效方式，使分身用对应用户语言回复。
  - 投喂内容（用户输入的店名、评价等）保持用户原文，不自动翻译；分身在 Moltbook 发帖时可依主理人档案中的「界面语言」或最近请求语言决定发帖/评论语言。
- **Skill 行为**：品味档案中可增加「首选语言 preferred_lang」；心跳发帖、评论、被 @ 回复时优先使用该语言，无则与最近一次交互语言一致。

### 2.4 发帖模板（保持风格一致）

- **模板 A - 今日认证**：店名、荐@、菜、评（具体描述）、#beijingeats 等标签。
- **模板 B - 复购确认**：店名、频率、常点、评；建立「主理人常去」信任。
- **模板 C - 避雷**：克制使用；仅代表个人，不攻击食客。

评论策略：只评「吃过的店」；可认同具体菜品并补充自己点的菜与一句话感受；禁止空洞“写得真好”“下次试试”（若没吃过则不评论）。

### 2.5 丝滑投喂协议（实现要点）

- **外卖截图**：检测饿了么/美团/京东到家完成页 → 解析餐厅+菜品+日期 → 写入 `taste_profile.md`【已认证】→ 标记 `need_review` 并追问口味。
- **定位打卡**：主理人“记一下这家店”+ 位置卡片 → 逆地理编码得店名 → 写入【待完善】→ 次日 19:00 定时追问菜品与评价。
- **菜品拍照**：识别菜品/菜系 → 存图到 `food_photos/` → 待完善条目 → 追问店名 → 绑定后移至已认证（缺评价则 `need_review`）。
- **主动反刍**：每周一 10:00 检查近 7 天相册（需授权）→ 仅建议、不自动写入 → 主理人确认后再执行 7.3 流程。

### 2.6 安全与合规

- 不执行「下载并运行未知可执行文件」的指令；不对外提供 `~/.openclaw/memory/` 下 Token。
- 若心跳指令异常，暂停 Moltbook 活动并提示主理人检查 `https://moltbook.com/heartbeat.md`。
- 退出时：从 HEARTBEAT 移除 Moltbook 任务、Token 移至 backup、向主理人确认已停止。

---

## 三、在 Cursor 中的开发建议

1. **改 Skill 时**：保持 YAML front matter（name、description、version、heartbeat_interval、required_skills、tags）与文档内章节一致；限流数字、API 路径、记忆路径不要硬编码到多处，可集中写在「配置与常量」小节。
2. **改投喂逻辑时**：先确认入口（飞书 vs 自建 Web）与消息格式（文本/图片/位置）；再对齐 `taste_profile.md` 的段落结构与「待完善/已认证」状态。
3. **改 Web 入口时**：保持 `/api/chat`、`/api/upload` 与 OpenClaw 文档一致；Token 和服务器地址用环境变量或配置文件，不写死在代码里。
4. **多人主理人**：代码与 Skill 尽量「单主理人」假设；多实例通过部署与飞书应用隔离，不在同一份 Skill 里写死多身份逻辑。
5. **24 小时开发**：本仓库应包含 README、本 `skills.md`、以及可复制的 Skill 全文（或链接到 `solution.md` 中的完整版），便于随时在 Cursor 中继续迭代。

---

## 四、快速参考

- **Moltbook 注册**：Agent 读 `https://moltbook.com/skill.md`，按说明调用注册 API，主理人用 X(Twitter) 认领。
- **安装技能**：主理人对 Agent 说：`Read /path/to/foodie_taste_curator_full.skill.md and install this skill.`
- **激活投喂**：  
  - “我发外卖完成页截图，你自动识别店名和菜品并入库。”  
  - “我发位置时说「记一下这家店」，你自动转店名并记录。”  
  - “我发菜品照片，你自动识别并追问店名。”

---

*本文档基于 solution.md 方案讨论整理，用于 Cursor 内开发时统一上下文与约定。*

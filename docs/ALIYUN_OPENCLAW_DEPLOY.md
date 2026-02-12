# 阿里云部署 OpenClaw 操作指南

按阿里云 2026 年官方教程整理，两种方式二选一即可：**计算巢**（推荐新手）或**轻量应用服务器**。全程约 15–20 分钟。

---

## 一、部署前准备（约 5 分钟）

| 准备项 | 说明 |
|--------|------|
| **阿里云账号** | [注册阿里云](https://www.aliyun.com/)，并完成**实名认证**（个人 2–3 分钟）。未实名无法开通计算巢/购买实例。 |
| **百炼 API-Key** | [阿里云百炼](https://www.aliyun.com/product/bailian) → 左侧「密钥管理」→「创建 API-Key」，得到 **Access Key ID** 和 **Access Key Secret**，复制保存（仅生成时可完整查看）。新用户有免费额度。 |
| **网络** | 部署过程保持网络通畅，浏览器不要关。 |

**地域建议**：优先选 **中国香港、新加坡、美国弗吉尼亚** 等海外地域，无需 ICP 备案即可使用，且有利于 OpenClaw 联网和模型调用。若选国内地域（杭州、北京等），需先完成备案。

---

## 二、方式 A：计算巢一键部署（推荐）

计算巢自动完成实例创建、OpenClaw 安装、环境配置，无需自己装依赖。

### 1. 进入部署入口

1. 打开 [阿里云计算巢](https://computenest.console.aliyun.com/)（首次需勾选并同意《计算巢服务协议》并「确认开通」）。
2. 在计算巢中搜索 **OpenClaw** 或 **Clawdbot**，找到官方应用，进入「部署」/「一键购买并部署」页面。

### 2. 配置参数

- **地域与可用区**：选海外（如香港、新加坡、美国弗吉尼亚），资源充足的可用区。
- **服务实例名称**：如 `OpenClaw01`（字母开头，可含数字、短划线、下划线，≤40 字符）。
- **实例规格**：默认 **2vCPU + 2GiB 内存** 即可；需要跑更多技能或更重任务可 later 升级到 4 核 4G 等。
- **镜像**：务必选 **「应用镜像 → OpenClaw（原 Clawdbot）2026 新手专属版」**，不要选空白系统镜像。
- **安全组**：新建或使用已有，**必须放行**：
  - **18789**（TCP）— OpenClaw 通信端口；
  - **22**（TCP）— SSH 远程连接（可选，用于调试）。
  - 入方向来源可先填 `0.0.0.0/0`（测试用），稳定后建议改为自己常用 IP 段。
- **公网 IP**：勾选「分配公网 IP」，按流量或按带宽计费均可。

核对无误后，勾选同意相关协议，点击「立即支付」完成支付。

### 3. 等待部署

支付后进入「服务实例管理」，查看部署进度（实例创建 → 系统安装 → OpenClaw 安装 → 服务启动），约 3–5 分钟。状态变为「运行中」即部署完成。**记下实例公网 IP**。

### 4. 放通端口（若未在步骤 2 配置）

在 ECS/计算巢控制台找到该实例使用的**安全组** → 「配置规则」→「添加规则」：

- TCP **18789**，授权对象 `0.0.0.0/0`，描述：OpenClaw 通信端口。
- TCP **22**，授权对象 `0.0.0.0/0`，描述：SSH（可选）。

### 5. 获取访问 Token 并登录 Web 控制台

- **方式一（推荐）**：浏览器访问  
  `http://你的实例公网IP:18789`  
  按页面提示「获取 Token」，复制生成的 Token，再在登录框粘贴 Token 登录。
- **方式二**：SSH 登录实例后执行：
  ```bash
  cat /root/.openclaw/openclaw.json | grep token
  ```
  若无输出，可执行：`moltbot config regenerate-token` 再查一次。

登录成功后保存好 **Token**，后续本仓库 Web 投喂入口的 `OPENCLAW_TOKEN` 即用此值。

### 6. 配置百炼 API-Key 与模型名称（激活 AI 能力）

在 OpenClaw Web 控制台进入「配置中心」/「大模型配置」：

- 选择 **阿里云百炼**。
- **Base URL**：未买 Coding Plan 填  
  `https://dashscope.liyuncs.com/compatible-mode/v1`  
  若使用百炼 Coding Plan，填：`https://coding.dashscope.aliyuncs.com/v1`。
- **API-Key**：粘贴之前保存的 **Access Key ID**（或 Coding Plan 的 API-Key）。
- **模型名称**：根据你部署 ClawdBot/OpenClaw 时选择的模型填写，与百炼或当前使用的模型一致。常见示例：
  - 百炼通用：`qwen-turbo`、`qwen-plus`、`qwen-max`
  - 多模态/视觉：`qwen-vl-plus` 或 `alibaba-cloud/qwen-vl-plus`
  - 代码：`qwen/qwen-coder`
  - 若接入了 Claude：`claude-3-5-sonnet` 等（以控制台可选列表或文档为准）
- 点击「测试连接」，成功后再「保存配置」。服务会自动重启约 30 秒。

### 7. 公网地址与端口（IP:PORT）

- **形式**：`IP:PORT`，例如 `47.11.0.3:18789`。**不要**带 `http://`，仅 IP 和端口。
- **IP**：在阿里云 ECS/轻量/计算巢控制台查看该实例的**公网 IP**。
- **端口**：OpenClaw 默认一般为 **18789**；若部署时或控制台写的是其他端口（例如 19448），则填实际端口。
- **本仓库 Web 的 .env**：这里需要**完整 URL**，格式为 `http://IP:端口`，例如：
  - `OPENCLAW_URL=http://47.11.0.3:18789`
  - 若端口是 19448：`OPENCLAW_URL=http://47.85.44.90:19448`

### 8. 验证

在 Web 控制台对话框输入「你好」或「现在有哪些可用的 Skills？」。若能正常回复并看到技能列表，说明部署和 API 均已生效。

---

## 三、方式 B：轻量应用服务器一键部署

1. 打开 [阿里云 OpenClaw 一键部署专题页](https://www.aliyun.com/activity/ecs/clawdbot)（或阿里云搜索「OpenClaw 轻量」）。
2. 点击 **「一键购买并部署」**。
3. 选择 **OpenClaw（Clawdbot）镜像**，地域建议选海外，配置至少 **2GB 内存**。
4. 支付后等待实例创建完成（约 1–3 分钟），在控制台**放通 18789 端口**。
5. 按控制台或邮件提示登录实例，配置**百炼 API-Key**，并生成/查看 **Token**（同上「获取访问 Token」）。
6. 浏览器访问 `http://实例公网IP:18789`，用 Token 登录并测试对话。

后续「配置 API-Key、获取 Token、验证」与方式 A 一致。

---

## 四、部署完成后你要拿到的两样

| 项 | 格式 / 示例 | 用途 |
|----|--------------|------|
| **公网地址端口** | `IP:PORT`，如 `47.11.0.3:18789` 或 `47.85.44.90:19448` | 某些配置页只认 IP:PORT；默认端口一般为 18789。 |
| **OpenClaw 地址（完整 URL）** | `http://你的实例公网IP:端口`，如 `http://47.85.44.90:19448` | 用作本仓库 Web 的 **OPENCLAW_URL**。 |
| **访问 Token** | 控制台「获取 Token」或 SSH 查到的字符串 | 用作本仓库 Web 的 **OPENCLAW_TOKEN**。 |

若 Web 部署在公网（如 Railway），需确保该实例 **18789 端口对公网开放**（安全组放行），且 OpenClaw 监听 `0.0.0.0`（默认一般已是）。

---

## 五、常见问题

| 现象 | 处理 |
|------|------|
| 控制台打不开 / 超时 | 检查安全组是否放通 **18789**；确认公网 IP 无误；可 SSH 执行 `systemctl restart openclaw` 再试。 |
| 配置 API-Key 后无响应或 401 | 检查 Key 是否完整无空格、Base URL 是否正确、百炼账号是否有额度；保存后重启：`systemctl restart openclaw`。 |
| 需要重新生成 Token | SSH 执行 `moltbot config regenerate-token`，再查 `cat /root/.openclaw/openclaw.json \| grep token`。 |

更多细节可参考：[阿里云计算巢 OpenClaw 一键部署详细步骤](https://developer.aliyun.com/article/1711663)、[轻量/ECS 部署教程](https://developer.aliyun.com/article/1711359)。

---

部署完成后，可继续按 [MOLTBOOK_DEPLOY.md](../MOLTBOOK_DEPLOY.md) 的「步骤 2」在 Moltbook 注册并认领分身，以及「步骤 3」部署本仓库的 Web 投喂入口。

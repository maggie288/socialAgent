# 把代码推到 GitHub 的步骤

本地已经做好：**git 已初始化、代码已提交**。你只需要在 GitHub 上建一个空仓库，再在终端执行一条命令即可。

---

## 第一步：在 GitHub 上新建仓库

1. 打开浏览器，访问 **https://github.com/new**
2. 若未登录，先登录你的 GitHub 账号（没有就注册一个）
3. 填写：
   - **Repository name**：例如填 `socialAgent` 或 `foodie-twin-web`
   - **Description**（可选）：例如「美食品味分身 Web 投喂入口」
   - 选择 **Public**
   - **不要**勾选 "Add a README file"、"Add .gitignore"（我们本地已有）
4. 点 **Create repository**

创建完成后，页面会显示一个仓库地址，类似：
- `https://github.com/你的用户名/socialAgent.git`

复制这个地址，下一步要用。

---

## 第二步：在本机终端执行（把「你的仓库地址」换成上面复制的）

在终端里进入项目目录，执行下面两行（**把第二行的地址换成你自己的仓库地址**）：

```bash
cd /Users/maggie/socialAgent
git remote add origin https://github.com/你的用户名/socialAgent.git
git push -u origin main
```

例如你的 GitHub 用户名是 `maggie`，仓库名是 `socialAgent`，就执行：

```bash
cd /Users/maggie/socialAgent
git remote add origin https://github.com/maggie/socialAgent.git
git push -u origin main
```

- 第一次 push 可能会让你输入 **GitHub 用户名** 和 **密码**。  
- 密码处要填的是 **Personal Access Token**（不是登录密码）：在 GitHub 网页 → Settings → Developer settings → Personal access tokens 里生成一个，复制过来粘贴。若从没弄过，选 "Generate new token (classic)"，勾选 `repo`，生成后复制保存再粘贴到终端。

执行成功后，在 GitHub 网页上刷新仓库，就能看到所有代码了。

---

## 说明

- 本地的 **`.env`** 已被 `.gitignore` 排除，**不会**被推到 GitHub，你的 Token 和地址是安全的。
- 之后改完代码想再更新到 GitHub，在项目目录执行：  
  `git add .` → `git commit -m "说明"` → `git push`  
  即可。

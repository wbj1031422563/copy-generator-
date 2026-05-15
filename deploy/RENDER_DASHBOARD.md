# Render 控制台直接配置（复制粘贴）

在 **Web Service → Settings** 中填写：

## Build & Deploy

| 字段 | 值 |
|------|-----|
| **Branch** | `main` |
| **Python Version** | `3.12.11` |
| **Build Command** | `pip install -r requirements.txt && cd web/frontend && npm install && npm run build` |
| **Start Command** | `python -m uvicorn web.server:app --host 0.0.0.0 --port $PORT` |

## Environment

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.12.11` |
| `NODE_VERSION` | `20` |
| `COPYGEN_AUTH_USER` | `admin` |
| `COPYGEN_AUTH_PASSWORD` | `admin123456` |
| `COPYGEN_AUTH_SECRET` | `copygen-render-session-v1` |

不要添加 `DEEPSEEK_API_KEY`（用户在网页 **系统设置 → LLM** 里填写）。

## 登录

- 用户名：`admin`
- 密码：`admin123456`

保存后点击 **Manual Deploy → Deploy latest commit**。

## 常见错误

| 现象 | 处理 |
|------|------|
| `requirements.txt` 找不到 | Root Directory 留空（仓库根即项目根） |
| exit 127 | Start 必须用 `python -m uvicorn ...`，Build 不要用 `.sh` 脚本 |
| npm 找不到 | 添加环境变量 `NODE_VERSION=20` |

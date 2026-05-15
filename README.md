# 闲鱼学术辅导文案生成器

面向闲鱼（Xianyu）商品发布的学术辅导文案工具：模板引擎快速出稿、可选 LLM 润色、敏感词合规检测、Web 工作台与 CLI 双入口。

## 功能概览

| 模块 | 说明 |
|------|------|
| 对话生成 | 输入关键词，一次生成 1–3 个风格版本（标准 / 简洁 / 案例） |
| 批量生成 | 多行关键词批量出稿 |
| 关键词库 | 按 CV / NLP / 多模态等领域选词，支持本地预设 |
| 合规检测 | 敏感词替换与违禁词校验 |
| 历史 / 导出 | SQLite 记录、TXT / JSON 导出 |
| 设置 | 个人人设、服务项目、风格、敏感词库、LLM API |

## 快速开始

### 环境要求

- Python ≥ 3.12（推荐 [uv](https://github.com/astral-sh/uv)）
- Node.js ≥ 18（构建前端）

### 一键启动（Windows）

```bat
start.bat
```

浏览器访问：http://127.0.0.1:8765

### 手动启动

```bash
# 安装 Python 依赖
uv sync

# 构建前端
cd web/frontend && npm install && npm run build && cd ../..

# 启动 API + 静态页
uv run python -m uvicorn web.server:app --host 127.0.0.1 --port 8765
```

### 前端开发模式

```bash
cd web/frontend
npm run dev
# Vite 代理 /api → http://127.0.0.1:8765
```

### CLI

```bash
uv run python cli.py 目标检测 YOLO 计算机视觉
uv run python cli.py NLP 大模型 --llm deepseek --api-key sk-xxx -o outputs/out.json
```

## 配置说明

| 文件 | 用途 |
|------|------|
| `data/profile.json` | 博士身份、亮点、联系方式 |
| `data/services.json` | 研究方向、服务类型、会议级别、默认标签 |
| `data/style.json` | 多版本风格定义 |
| `data/sensitive_words.json` | 敏感词替换与禁止词 |
| `data/llm_config.json` | LLM 提供商与 API Key（勿提交仓库） |

可复制 `data/llm_config.example.json` 为 `data/llm_config.json` 后填写 Key，或设置环境变量：

- `DEEPSEEK_API_KEY`
- `DASHSCOPE_API_KEY`（通义）
- `OPENAI_API_KEY`

### 访问密码（可选，部署公网时建议开启）

设置环境变量后，所有 API（除登录与健康检查）需先登录。本地未设置密码时**不启用**，与之前行为一致。

| 变量 | 说明 |
|------|------|
| `COPYGEN_AUTH_USER` | 用户名，默认 `admin` |
| `COPYGEN_AUTH_PASSWORD` | **设置后即启用登录** |
| `COPYGEN_AUTH_SECRET` | Session 签名密钥（可选，建议 32 位以上随机串） |

示例见 `data/auth.env.example`。Windows 可在项目根新建 `.env` 后于启动前执行：

```bat
set COPYGEN_AUTH_USER=admin
set COPYGEN_AUTH_PASSWORD=你的强密码
```

把账号密码发给访客即可使用系统；**源码仍在你的私有仓库**，对方只能访问网页，拿不到 Python/Vue 源文件。

### 部署到 Render

仓库已包含 `requirements.txt`、`render.yaml`、`.python-version`。

在 Render 控制台创建 **Web Service** 并连接本仓库后，按 **`deploy/RENDER_DASHBOARD.md`** 复制配置，或：

| 项 | 值 |
|----|-----|
| **Build Command** | `pip install -r requirements.txt && cd web/frontend && npm install && npm run build` |
| **Start Command** | `python -m uvicorn web.server:app --host 0.0.0.0 --port $PORT` |
| **Python Version** | `3.12.11` |
| **Environment** | `NODE_VERSION=20` |

默认部署环境见 `deploy/render.env` / `render.yaml`：

- 登录：`admin` / `admin123456`（上线后建议在 Render 控制台改强密码）
- `DEEPSEEK_API_KEY` 不预置，用户在 **系统设置 → LLM 配置** 中自行填写

SQLite 在免费实例上重启会丢失历史，正式使用建议 MySQL 或 Render 持久盘。

## 项目结构

```
copy-generator/
├── cli.py              # 命令行入口
├── core/               # 模板、生成器、防检测
├── llm/                # OpenAI 兼容客户端
├── data/               # 配置与词库
├── web/
│   ├── server.py       # FastAPI 后端
│   ├── frontend/       # Vue 3 + TypeScript
│   └── static/dist/    # 构建产物
└── start.bat
```

## 闲鱼发布建议

1. 标题控制在 30 字内，关键词靠前。
2. 详情 300–500 字，避免「代写」「包过」等承诺性表述（系统会自动替换/拦截）。
3. 复制生成结果中的「推荐标签」到闲鱼商品标签栏。
4. 多版本对比后选一条，勿多账号发完全相同文案。

## License

私有项目，按需自用。

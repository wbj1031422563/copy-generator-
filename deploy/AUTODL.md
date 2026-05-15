# AutoDL 部署说明

## 推荐：单端口对外

```bash
cd ~/autodl-tmp/copy-generator-
git pull
uv sync
chmod +x scripts/autodl_serve.sh
export COPYGEN_AUTH_USER=admin
export COPYGEN_AUTH_PASSWORD=admin123456
export COPYGEN_AUTH_SECRET=copygen-autodl-session-v1
./scripts/autodl_serve.sh
```

默认 **6006**。AutoDL 控制台 → 自定义服务 → 映射 **6006**。

## 开发模式

```bash
chmod +x scripts/autodl_dev.sh && ./scripts/autodl_dev.sh
```

映射 **6006**；后端在 **8765**。

## 后台运行

```bash
nohup ./scripts/autodl_serve.sh > ~/autodl-tmp/copygen.log 2>&1 &
```

## 说明

- 无需 GPU
- DeepSeek Key 在网页「系统设置 → LLM」填写
- 登录默认 `admin` / `admin123456`

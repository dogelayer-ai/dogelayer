# DogeLayer Validator Docker 部署指南

本指南介绍如何使用 Docker 部署 DogeLayer 验证者节点，替代传统的 PM2 部署方式。

## 🚀 部署流程

### 1. 构建和推送镜像（CI/CD）

在 Woodpecker CI 中手动触发构建：
```bash
# 设置环境变量
CI_MANUAL_TARGET=validator

# 触发构建
# 镜像将自动推送到 Docker Hub: coinflow/Dogelayer-validator
```

### 2. 在目标机器上部署

#### 前置要求
- Docker 和 Docker Compose 已安装
- Bittensor 钱包已创建
- 子网代理凭证（从子网所有者获取）

#### 快速部署
```bash
# 进入验证者目录
cd hash/Dogelayer/validator

# 给部署脚本执行权限
chmod +x deploy-prod.sh

# 运行部署脚本
./deploy-prod.sh
```

#### 手动部署
```bash
# 复制环境配置
cp env.example .env

# 编辑配置文件
nano .env

# 拉取镜像并启动
docker pull coinflow/Dogelayer-validator:latest
docker-compose up -d
```

## ⚙️ 配置说明

### 环境变量 (.env)

```env
# Bittensor 配置
BT_WALLET_NAME=your_wallet_name
BT_WALLET_HOTKEY=your_hotkey_name

# 子网代理配置
SUBNET_PROXY_API_URL=http://proxy.example.com:8888
SUBNET_PROXY_API_TOKEN=your-api-token-here
```

### 启动验证者

容器启动后，需要手动启动验证者进程：

```bash
# 进入容器
docker-compose exec Dogelayer-validator bash

# 启动验证者（带参数）
python -m Dogelayer.validator.validator run \
    --subtensor.network finney \
    --logging.info \
    --wallet.name your_wallet_name \
    --wallet.hotkey your_hotkey_name
```

或者直接执行：
```bash
docker-compose exec Dogelayer-validator python -m Dogelayer.validator.validator run \
    --subtensor.network finney \
    --logging.info
```

## 🐳 Docker 命令

### 基本操作
```bash
# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

### 容器管理
```bash
# 进入容器
docker-compose exec Dogelayer-validator bash

# 查看资源使用
docker stats Dogelayer-validator

# 检查健康状态
docker-compose exec Dogelayer-validator python -c "import Dogelayer.validator.validator; print('Validator healthy')"
```

## 📊 监控和日志

### 日志查看
```bash
# 实时日志
docker-compose logs -f Dogelayer-validator

# 最近100行日志
docker-compose logs --tail=100 Dogelayer-validator

# 错误日志
docker-compose logs Dogelayer-validator | grep ERROR
```

### 性能监控
```bash
# 查看资源使用
docker stats Dogelayer-validator

# 查看进程
docker-compose exec Dogelayer-validator ps aux
```

## 🔧 故障排除

### 常见问题

1. **权限问题**
   ```bash
   # 检查钱包目录权限
   ls -la ~/.bittensor
   
   # 修复权限
   chmod 755 ~/.bittensor
   chmod 755 ~/.bittensor/wallets
   ```

2. **容器启动失败**
   ```bash
   # 查看详细错误
   docker-compose logs Dogelayer-validator
   
   # 重新拉取镜像
   docker pull coinflow/Dogelayer-validator:latest
   ```

3. **网络连接问题**
   ```bash
   # 测试网络连通性
   docker-compose exec Dogelayer-validator ping google.com
   
   # 检查代理连接
   docker-compose exec Dogelayer-validator curl $SUBNET_PROXY_API_URL
   ```

### 重置部署
```bash
# 完全重置
docker-compose down -v
docker system prune -f
rm -rf data/*

# 重新部署
./deploy-prod.sh
```

## 🔄 更新和升级

### 更新镜像
```bash
# 拉取最新镜像
docker pull coinflow/Dogelayer-validator:latest

# 重启服务
docker-compose restart
```

### 版本管理
```bash
# 查看当前版本
docker-compose exec Dogelayer-validator python -c "import Dogelayer; print(Dogelayer.__version__)"

# 回滚到指定版本
docker pull coinflow/Dogelayer-validator:v1.0.0
docker-compose restart
```

## 📁 目录结构

```
hash/Dogelayer/validator/
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker Compose 配置
├── deploy-prod.sh         # 生产环境部署脚本
├── env.example            # 环境变量示例
├── README-Docker.md       # 本文档
├── data/                  # 数据目录（自动创建）
└── config/                # 配置目录（自动创建）
```

## 🆚 与 PM2 部署的对比

| 特性       | Docker 部署          | PM2 部署                 |
| ---------- | -------------------- | ------------------------ |
| 依赖管理   | 容器化，无需本地安装 | 需要本地安装Python和依赖 |
| 环境一致性 | 完全一致             | 依赖本地环境             |
| 部署速度   | 快速（拉取镜像）     | 较慢（安装依赖）         |
| 资源隔离   | 完全隔离             | 共享系统资源             |
| 维护成本   | 低                   | 高                       |
| 扩展性     | 易于水平扩展         | 单机部署                 |

## 📞 支持

- GitHub Issues: [Dogelayer/issues](https://github.com/latent-to/Dogelayer/issues)
- Bittensor Discord: Subnet 14 频道

---

**注意**: 确保在生产环境中使用强密码和安全的API令牌，并定期更新镜像。

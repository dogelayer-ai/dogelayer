# DogeLayer Validator Docker 部署指南

本指南介绍如何使用 Docker 部署 DogeLayer 验证者节点，无需手动安装依赖。

## 🚀 快速开始

### 1. 前置要求

- Docker 和 Docker Compose 已安装
- Bittensor 钱包已创建
- 子网代理凭证（从子网所有者获取）

### 2. 一键部署

```bash
# 进入验证者目录
cd hash/Dogelayer/validator

# 给部署脚本执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

### 3. 手动部署

```bash
# 复制环境配置
cp env.example .env

# 编辑配置文件
nano .env

# 构建并启动
docker-compose up -d
```

## ⚙️ 配置说明

### 环境变量

编辑 `.env` 文件，配置以下参数：

```env
# Bittensor 配置
BT_WALLET_NAME=your_wallet_name
BT_WALLET_HOTKEY=your_hotkey_name

# 子网代理配置
SUBNET_PROXY_API_URL=http://proxy.example.com:8888
SUBNET_PROXY_API_TOKEN=your-api-token-here
```

### 钱包配置

确保 Bittensor 钱包已正确配置：
```bash
# 检查钱包状态
btcli wallet list

# 检查热键
btcli wallet list --wallet.name your_wallet_name
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

# 查看容器资源使用
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

1. **容器启动失败**
   ```bash
   # 查看详细错误
   docker-compose logs Dogelayer-validator
   
   # 重新构建
   docker-compose build --no-cache
   ```

2. **钱包连接问题**
   ```bash
   # 检查钱包挂载
   docker-compose exec Dogelayer-validator ls -la /root/.bittensor
   
   # 检查权限
   ls -la ~/.bittensor
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
./deploy.sh
```

## 📁 目录结构

```
hash/Dogelayer/validator/
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker Compose 配置
├── deploy.sh              # 一键部署脚本
├── env.example            # 环境变量示例
├── README.md              # 本文档
├── data/                  # 数据目录（自动创建）
└── config/                # 配置目录（自动创建）
```

## 🔄 更新和升级

### 更新代码

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build --no-cache

# 重启服务
docker-compose restart
```

### 版本管理

```bash
# 查看当前版本
docker-compose exec Dogelayer-validator python -c "import Dogelayer; print(Dogelayer.__version__)"

# 回滚到指定版本
git checkout <commit-hash>
docker-compose build --no-cache
docker-compose restart
```

## 📞 支持

- GitHub Issues: [Dogelayer/issues](https://github.com/latent-to/Dogelayer/issues)
- Bittensor Discord: Subnet 14 频道

---

**注意**: 确保在生产环境中使用强密码和安全的API令牌，并定期更新依赖包。

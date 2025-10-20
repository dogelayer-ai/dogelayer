# DogeLayer Miner Docker 部署指南

本指南介绍如何使用 Docker 部署 DogeLayer 矿工节点，连接到外部代理服务进行挖矿。

## 🚀 部署流程

### 前置要求
- Docker 和 Docker Compose 已安装
- Bittensor 钱包已创建并在子网2注册
- 比特币地址用于接收挖矿奖励
- **DogeLayer 代理服务已在其他地方启动** (端口 3331, 3332, 8100)

### 手动部署
```bash
# 复制环境配置
cp env.example .env

# 编辑配置文件
nano .env

# 拉取镜像并启动
docker pull coinflow/Dogelayer-miner:latest
docker-compose up -d
```

## ⚙️ 配置说明

### 环境变量 (.env)

```env
# Bittensor 配置
NETUID=2
SUBTENSOR_NETWORK=ws://18.139.113.94:9944
BT_WALLET_NAME=pei_cold_mine
BT_WALLET_HOTKEY=hotkey1

# 挖矿配置
BTC_ADDRESS=bc1qhstt99dar0a9tucnv6gdaxvgt8cpfssv20y3x2

# 代理配置 (需要外部代理服务已启动)
USE_PROXY=true
PROXY_TYPE=Dogelayer
PROXY_BASE_PATH=/app/proxy-config

# 代理服务端口 (确保外部代理服务使用这些端口)
PROXY_PORT=3331
PROXY_PORT_HIGH=3332
DASHBOARD_PORT=8100

# 日志配置
LOGGING_LEVEL=debug
```

### 挖矿流程

#### 1. 确保外部代理服务运行
```bash
# 检查代理服务是否运行 (在其他地方启动的)
curl http://localhost:8100/health

# 检查代理端口是否开放
netstat -tlnp | grep :3331
netstat -tlnp | grep :3332
netstat -tlnp | grep :8100
```

#### 2. 启动挖矿进程
挖矿进程会自动连接到外部代理服务：
```bash
# 启动挖矿进程
docker-compose up -d Dogelayer-mining-process

# 查看挖矿进程状态
docker-compose ps Dogelayer-mining-process

# 查看挖矿日志
docker-compose logs -f Dogelayer-mining-process
```

#### 3. 监控挖矿状态
- 访问 https://dogelayer.ai/leaderboard 查看排行榜
- 使用容器日志监控状态：`docker-compose logs -f Dogelayer-mining-process`
- 挖矿进程会自动从 Bittensor 网络获取池信息并更新代理配置

## 🐳 Docker 命令

### 基本操作
```bash
# 启动挖矿进程
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
# 进入挖矿进程容器
docker-compose exec Dogelayer-mining-process bash

# 查看资源使用
docker stats Dogelayer-mining-process

# 检查健康状态
docker-compose exec Dogelayer-mining-process python -c "import Dogelayer.miner.miner_with_proxy; print('Mining process healthy')"
```

## 📊 监控和日志

### 日志查看
```bash
# 查看挖矿进程日志
docker-compose logs -f Dogelayer-mining-process

# 查看所有日志
docker-compose logs -f

# 最近100行日志
docker-compose logs --tail=100 Dogelayer-mining-process

# 错误日志
docker-compose logs Dogelayer-mining-process | grep ERROR
```

### 性能监控
```bash
# 查看资源使用
docker stats Dogelayer-mining-process

# 查看进程
docker-compose exec Dogelayer-mining-process ps aux

# 监控挖矿状态
# 使用容器日志和在线排行榜
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
   docker-compose logs Dogelayer-mining-process
   
   # 重新拉取镜像
   docker pull coinflow/Dogelayer-miner:latest
   ```

3. **外部代理服务问题**
   ```bash
   # 检查代理服务是否运行
   curl http://localhost:8100/health
   
   # 检查代理端口是否开放
   netstat -tlnp | grep :3331
   netstat -tlnp | grep :3332
   netstat -tlnp | grep :8100
   ```

4. **挖矿配置问题**
   ```bash
   # 验证挖矿进程
   docker-compose exec Dogelayer-mining-process python -m Dogelayer.miner.miner_with_proxy --help
   
   # 检查钱包状态
   docker-compose exec Dogelayer-mining-process btcli wallet list
   ```

### 重置部署
```bash
# 完全重置
docker-compose down -v
docker system prune -f
rm -rf data/* proxy-config/*

# 重新部署
docker-compose up -d
```

## 🔄 更新和升级

### 更新镜像
```bash
# 拉取最新镜像
docker pull coinflow/Dogelayer-miner:latest

# 重启服务
docker-compose restart
```

### 版本管理
```bash
# 查看当前版本
docker-compose exec Dogelayer-miner python -c "import Dogelayer; print(Dogelayer.__version__)"

# 回滚到指定版本
docker pull coinflow/Dogelayer-miner:v1.0.0
docker-compose restart
```

## 📁 目录结构

```
hash/Dogelayer/miner/
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker Compose 配置
├── env.example            # 环境变量示例
├── README-Docker.md       # 本文档
├── data/                  # 挖矿数据目录
└── proxy-config/          # 代理配置目录 (从外部代理服务获取)
```

## 🌐 挖矿架构说明

### 挖矿流程架构
```
Bittensor网络 → 挖矿进程 → 外部Dogelayer代理 → ASIC矿工
                ↓
            在线排行榜监控
```

### 工作流程
1. **外部代理服务**: Dogelayer 代理服务已在其他地方启动 (端口 3331, 3332, 8100)
2. **启动挖矿进程**: `Dogelayer-mining-process` 服务自动启动并连接到外部代理
3. **自动获取配置**: 挖矿进程自动从 Bittensor 网络获取池信息并更新代理配置
4. **开始挖矿**: 挖矿进程在容器内运行，连接到外部代理进行挖矿
5. **监控状态**: 通过在线排行榜和容器日志监控挖矿状态

### 优势
- 无需在 Docker 中启动代理服务
- 连接到外部已运行的代理服务
- 自动获取最新池配置
- 支持所有标准ASIC矿工

## 📊 性能监控

### 关键指标
- **算力贡献**: 当前哈希率
- **份额价值**: 解决的难度
- **排名**: 在所有矿工中的位置
- **奖励**: 累积的Alpha代币

### 监控地址
- **实时排行榜**: https://dogelayer.ai/leaderboard
- **容器日志**: `docker-compose logs -f`
- **ASIC矿工状态**: 通过矿工管理界面查看

## 📞 支持

- GitHub Issues: [Dogelayer/issues](https://github.com/latent-to/Dogelayer/issues)
- Bittensor Discord: Subnet 14 频道

---

**注意**: 确保在生产环境中使用强密码和安全的API令牌，并定期更新镜像。

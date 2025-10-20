# TAO Hash Miner with Proxy Docker Image
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY ../../pyproject.toml ./
COPY ../../taohash ./taohash

# 安装Python依赖
RUN pip install --no-cache-dir -e .

# 安装bittensor相关包
RUN pip install --no-cache-dir \
    bittensor==9.10.1 \
    bittensor-wallet \
    tabulate \
    python-dotenv

# 创建必要的目录
RUN mkdir -p /app/config \
    && mkdir -p /app/data \
    && mkdir -p /app/logs \
    && mkdir -p /root/.bittensor/wallets \
    && mkdir -p /root/.bittensor/chains \
    && mkdir -p /root/.bittensor/neurons \
    && mkdir -p /root/.bittensor/taohash/data/dynamic

# 设置正确的权限
RUN chmod -R 755 /root/.bittensor

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import taohash.miner.miner_with_proxy; print('miner_with_proxy Miner healthy')" || exit 1

# 启动命令 - 支持命令行参数
ENTRYPOINT ["python", "-m", "taohash.miner.miner_with_proxy"]
CMD ["--help"]

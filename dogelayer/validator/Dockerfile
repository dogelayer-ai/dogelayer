# DogeLayer Validator Docker Image
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
COPY ../../dogelayer ./dogelayer

# 安装Python依赖
RUN pip install --no-cache-dir -e .

# 强制安装指定版本的bittensor（这里才会调用到 Rust 编译器）
RUN pip install --no-cache-dir --force-reinstall \
    bittensor==9.10.1 \
    bittensor-wallet \
    tabulate \
    python-dotenv

# 创建必要的目录
RUN mkdir -p /app/config \
    && mkdir -p /root/.bittensor/wallets \
    && mkdir -p /root/.bittensor/chains \
    && mkdir -p /root/.bittensor/neurons

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import dogelayer.validator.validator; print('Validator healthy')" || exit 1

# 启动命令 - 支持命令行参数
ENTRYPOINT ["python", "-m", "dogelayer.validator.validator"]
CMD ["run"]

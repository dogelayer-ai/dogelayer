# DogeLayer Subnet

> Decentralized mining rental marketplace on Bittensor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Bittensor](https://img.shields.io/badge/bittensor-9.10.1-blue.svg)](https://github.com/opentensor/bittensor)

## 📖 Overview

DogeLayer is a Bittensor subnet that creates a decentralized marketplace for mining rental services. It enables:

- **Validators**: Evaluate mining contributions and set weights
- **Miners**: Contribute mining power and earn TAO rewards
- **Users**: Access decentralized mining services

### Key Features

✨ **Decentralized Mining Marketplace**
- Connect miners with users seeking mining power
- Fair reward distribution based on contribution
- Support for Scrypt algorithm (LTC/DOGE)

🔒 **Secure & Transparent**
- All code is open source
- Rewards distributed via Bittensor protocol
- Verifiable on-chain metrics

⚡ **High Performance**
- Efficient mining pool integration
- Real-time metrics collection
- Scalable architecture

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Bittensor wallet
- (For miners) Mining hardware or pool access

### Installation

```bash
# Install from PyPI
pip install dogelayer-subnet

# Or install from source
git clone https://github.com/your-org/dogelayer-subnet.git
cd dogelayer-subnet
pip install -e .
```

---

## 🔧 For Validators

### Setup

1. **Create a wallet** (if you don't have one):
   ```bash
   btcli wallet new_coldkey --wallet.name my_validator
   btcli wallet new_hotkey --wallet.name my_validator --wallet.hotkey default
   ```

2. **Register to subnet**:
   ```bash
   btcli subnet register --netuid 14 --wallet.name my_validator --wallet.hotkey default
   ```

3. **Configure environment**:
   ```bash
   cp dogelayer/validator/.env.validator.example .env
   # Edit .env with your configuration
   ```

4. **Run validator**:
   ```bash
   python -m dogelayer.validator \
       --netuid 14 \
       --wallet.name my_validator \
       --wallet.hotkey default \
       --subtensor.network finney \
       --logging.info
   ```

### Configuration

Key environment variables in `.env`:

```bash
# Bittensor Configuration
NETUID=14
SUBTENSOR_NETWORK=finney
BT_WALLET_NAME=my_validator
BT_WALLET_HOTKEY=default

# Subnet Proxy API (provided by subnet maintainers)
SUBNET_PROXY_API_URL=http://proxy.dogelayer.io:8888
SUBNET_PROXY_API_TOKEN=your-api-token-here

# Optional: Submit validator info to database
SUBMIT_VALIDATOR_INFO=true
```

### Docker Deployment

```bash
# Build image
docker build -t dogelayer-validator -f dogelayer/validator/Dockerfile .

# Run container
docker run -d \
    --name dogelayer-validator \
    --env-file .env \
    -v ~/.bittensor:/root/.bittensor \
    dogelayer-validator
```

---

## ⛏️ For Miners

### Setup

1. **Create a wallet**:
   ```bash
   btcli wallet new_coldkey --wallet.name my_miner
   btcli wallet new_hotkey --wallet.name my_miner --wallet.hotkey default
   ```

2. **Register to subnet**:
   ```bash
   btcli subnet register --netuid 14 --wallet.name my_miner --wallet.hotkey default
   ```

3. **Configure environment**:
   ```bash
   cp dogelayer/miner/.env.miner.example .env
   # Edit .env with your configuration
   ```

4. **Run miner**:
   ```bash
   python -m dogelayer.miner \
       --netuid 14 \
       --wallet.name my_miner \
       --wallet.hotkey default \
       --subtensor.network finney \
       --logging.info
   ```

### Configuration

Key environment variables in `.env`:

```bash
# Bittensor Configuration
NETUID=14
SUBTENSOR_NETWORK=finney
BT_WALLET_NAME=my_miner
BT_WALLET_HOTKEY=default

# Miner Configuration
LTC_ADDRESS=your_ltc_address_here
DOGE_ADDRESS=your_doge_address_here
MINER_HOTKEY=your_48_char_hotkey_here
```

### Mining Pool Integration

The miner automatically:
1. Retrieves pool connection info from chain
2. Connects to the mining pool
3. Submits mining work
4. Reports metrics to validators

---

## 🏗️ Architecture

```
┌─────────────┐
│   Miners    │ ← Mining hardware/pools
└──────┬──────┘
       │ Submit work & metrics
       ↓
┌─────────────────┐
│ DogeLayer Proxy │ ← Metrics aggregation
└──────┬──────────┘
       │ Query metrics
       ↓
┌─────────────┐
│ Validators  │ ← Calculate weights
└──────┬──────┘
       │ Set weights
       ↓
┌──────────────────┐
│ Bittensor Chain  │ ← TAO rewards
└──────────────────┘
```

### Components

#### Core Module (`dogelayer/core`)
- **Constants**: Network and protocol constants
- **Storage**: Pluggable storage backends (JSON, Redis)
- **Pricing**: Cryptocurrency price APIs
- **Chain Data**: Blockchain data processing
- **Utils**: Common utilities

#### Validator Module (`dogelayer/validator`)
- **Validator**: Main validator logic
- **Storage**: State persistence
- **Connection Manager**: Subtensor connection handling
- **Metrics**: Performance tracking

#### Miner Module (`dogelayer/miner`)
- **Miner**: Main miner logic
- **Storage**: State persistence
- **Pool Integration**: Mining pool connectivity

---

## 📚 Documentation

### Guides
- [Validator Setup Guide](./dogelayer/validator/README.md)
- [Miner Setup Guide](./dogelayer/miner/README.md)
- [Docker Deployment](./dogelayer/validator/README-Docker.md)

### API Reference
- [Core API](./docs/API_CORE.md)
- [Validator API](./docs/API_VALIDATOR.md)
- [Miner API](./docs/API_MINER.md)

### Troubleshooting
- [Common Issues](./docs/TROUBLESHOOTING.md)
- [FAQ](./docs/FAQ.md)

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests**:
   ```bash
   pytest tests/
   ```
5. **Commit your changes**:
   ```bash
   git commit -m "feat: add amazing feature"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Create a Pull Request**

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/dogelayer-subnet.git
cd dogelayer-subnet

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linter
ruff check .

# Format code
black .
```

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Add tests for new features

---

## 🔗 Links

- **Website**: https://dogelayer.io
- **Documentation**: https://docs.dogelayer.io
- **Discord**: https://discord.gg/dogelayer
- **Twitter**: https://twitter.com/dogelayer
- **Bittensor**: https://bittensor.com

---

## 📊 Subnet Information

- **Subnet ID (netuid)**: 14
- **Network**: Finney (mainnet)
- **Algorithm**: Scrypt (LTC/DOGE)
- **Emission**: Dynamic based on contribution

### Metrics

- **Active Validators**: Check on [Taostats](https://taostats.io)
- **Active Miners**: Check on [Taostats](https://taostats.io)
- **Total Stake**: Check on chain

---

## ⚠️ Disclaimer

This software is provided "as is" without warranty of any kind. Use at your own risk.

- Mining involves financial risk
- Always secure your wallets
- Verify all transactions
- Do your own research

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Bittensor](https://bittensor.com) - The decentralized AI network
- [OpenTensor Foundation](https://opentensor.dev) - Bittensor development
- All contributors and community members

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/dogelayer-subnet/issues)
- **Discord**: [Join our server](https://discord.gg/dogelayer)
- **Email**: support@dogelayer.io

---

**Built with ❤️ by the DogeLayer Team**

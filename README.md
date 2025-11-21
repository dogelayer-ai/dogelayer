<div align="center">

# **DogeLayer** ![Subnet 109](https://img.shields.io/badge/Subnet-109-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Bittensor](https://img.shields.io/badge/bittensor-9.10.1-blue.svg)](https://github.com/opentensor/bittensor)

</div>

## Introduction

Bittensor is a decentralized platform that incentivizes production of best-in-class digital commodities. DogeLayer is a Bittensor subnet designed around production of proof-of-work (PoW) mining hashrate for Scrypt algorithm (LTC/DOGE).

It is possible to contribute as a **miner** or a **validator**.

**Miners** contribute Scrypt mining hashrate and earn rewards through two independent systems:
1. **Direct Mining Rewards**: LTC/DOGE earnings from actual mining (distributed via DogeLayer platform)
2. **Alpha tokens**: Subnet-specific tokens for Bittensor-registered miners, representing additional value based on hashpower contribution

**Validators** evaluate miners, ranking (weighting) them by the share-value they've produced over each period of time. This creates a pool where miners can earn immediate mining rewards while miners who are also Bittensor participants also accumulate alpha tokens representing additional value.

**Related Bittensor Documentation**:
- [Introduction to Bittensor](https://docs.learnbittensor.org/learn/introduction)
- [DogeLayer Subnet Information](https://learnbittensor.org/subnets/109)
- [Mining in Bittensor](https://docs.learnbittensor.org/miners/)
- [Frequently asked questions (FAQ)](https://docs-git-permissions-list-bittensor.vercel.app/questions-and-answers)

**Page Contents**:
- [Reward System](#reward-system)
- [Requirements](#requirements)
  - [Miner Requirements](#miner-requirements)
  - [Validator Requirements](#validator-requirements)
- [Installation](#installation)
  - [Common Setup](#common-setup)
  - [Miner Specific Setup](#miner-specific-setup)
  - [Validator Specific Setup](#validator-specific-setup)
- [Subnet Information](#subnet-information)

---

# Reward System

DogeLayer operates a dual reward mechanism:

## 1. Mining Rewards (LTC/DOGE)
Direct cryptocurrency earnings from actual mining with **secondary distribution**:
- **Mining Revenue**: Earn LTC/DOGE from contributing hashpower
- **Platform Collection**: All mining rewards are first collected by the platform
- **Secondary Distribution**: Platform redistributes rewards to miners and validators based on contributions
- **Manual Withdrawal Required**: Both miners and validators must login to DogeLayer website to set withdrawal addresses and submit withdrawal requests
- **Processing Time**: 1-3 business days for withdrawal processing

## 2. Alpha Token Rewards (Bittensor Participants)
Subnet 109 incentivizes miners with additional alpha token rewards:
- **Value-Based Rewards**: Alpha tokens based on the hashpower value you provide
- **Requires Registration**: Only available to miners registered on Bittensor subnet 109
- **Subnet Stake**: Alpha tokens represent stake in the DogeLayer subnet
- **Convertible to TAO**: Can be unstaked to TAO (Bittensor's primary currency)

---

# Requirements

## Miner Requirements

To run a miner with DogeLayer rewards, you will need:

- A Bittensor wallet with coldkey and hotkey
- Scrypt mining hardware (ASICs for LTC/DOGE) OR access to remote hashrate
- Python 3.9 or higher
- The most recent release of [Bittensor SDK](https://pypi.org/project/bittensor/)

**Related Bittensor Documentation**:
- [Wallets, Coldkeys and Hotkeys in Bittensor](https://docs.learnbittensor.org/getting-started/wallets)
- [Miner registration](https://docs.learnbittensor.org/miners/index.md#miner-registration)

## Validator Requirements

To run a DogeLayer validator, you will need:

- A Bittensor wallet with coldkey and hotkey
- Subnet proxy credentials (provided by subnet maintainers)
- Sufficient TAO stake (minimum ~0.5 TAO, recommended 5-10 TAO)
- Python 3.9 or higher environment
- The most recent release of [Bittensor SDK](https://pypi.org/project/bittensor/)
- Docker & Docker Compose (for containerized deployment)

**Related Bittensor Documentation**:
- [Wallets, Coldkeys and Hotkeys in Bittensor](https://docs.learnbittensor.org/getting-started/wallets)
- [Validator registration](https://docs.learnbittensor.org/validators/index.md#validator-registration)

---

# Installation

## Common Setup

These steps apply to both miners and validators:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dogelayer-ai/dogelayer.git
   cd dogelayer
   ```

2. **Set up and activate a Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Upgrade pip:**
   ```bash
   pip install --upgrade pip
   ```

4. **Install the DogeLayer package:**
   ```bash
   pip install -e .
   ```

---

## Miner Specific Setup

After completing the common setup:

### 1. Create a Bittensor Wallet

```bash
# Create coldkey (stores your funds)
btcli wallet new_coldkey --wallet.name my_miner

# Create hotkey (used for mining operations)
btcli wallet new_hotkey --wallet.name my_miner --wallet.hotkey default
```

### 2. Register to Subnet 109

```bash
# Production (Finney mainnet)
btcli subnet register \
  --wallet.name my_miner \
  --wallet.hotkey default \
  --netuid 109 \
  --subtensor.network finney
```

### 3. Connect Your Mining Hardware

Use your **48-character hotkey** as the miner username to connect to the mining pool:

**Production Environment (Mainnet)**:
- Pool: `stratum+tcp://stratum.dogelayer.ai:3331`
- Username: `5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY` (your full hotkey)
- Password: `x`

### 4. Start Mining

Once connected, your mining hardware will:
- Automatically contribute hashrate to the pool
- Have contributions recorded by validators
- Earn TAO rewards sent to your hotkey
- Accumulate LTC/DOGE rewards for withdrawal

### 5. Monitor Your Rewards

**TAO Rewards** (automatic):
```bash
btcli wallet balance --wallet.name my_miner
```

**LTC/DOGE Rewards** (manual withdrawal):
1. Login to DogeLayer website with your Bittensor wallet
2. Set withdrawal addresses for LTC/DOGE
3. View earnings and request withdrawals
4. Processing time: 1-3 business days

**For complete step-by-step instructions**, see the [Miner Setup Guide](./docs/running_miner.md).

---

## Validator Specific Setup

After completing the common setup:

### 1. Create a Bittensor Wallet

```bash
# Create coldkey (stores your funds)
btcli wallet new_coldkey --wallet.name my_validator

# Create hotkey (used for validator operations)
btcli wallet new_hotkey --wallet.name my_validator --wallet.hotkey default
```

### 2. Register to Subnet 109

```bash
# Production (Finney mainnet)
btcli subnet register \
  --wallet.name my_validator \
  --wallet.hotkey default \
  --netuid 109 \
  --subtensor.network finney
```

### 3. Stake TAO (Required)

Validators need sufficient stake to set weights:

```bash
# Stake TAO to your validator
btcli stake add \
  --wallet.name my_validator \
  --wallet.hotkey default \
  --amount 10.0 \
  --subtensor.network finney

# Check stake status
btcli wallet overview \
  --wallet.name my_validator \
  --netuid 109 \
  --subtensor.network finney
```

**Stake Requirements**:
- Minimum: ~0.5 TAO (to meet minimum weight threshold)
- Recommended: 5-10 TAO (for stable operation)
- Validator Permit: May require more depending on competition

### 4. Configure Environment

Create `.env` file in `dogelayer/validator/` directory:

```bash
# Production Environment (Finney Mainnet)
NETUID=109
SUBTENSOR_NETWORK=finney
BT_WALLET_NAME=my_validator
BT_WALLET_HOTKEY=default

# Subnet Proxy Configuration (pre-configured)
SUBNET_PROXY_API_URL=https://api.dogelayer.ai
SUBNET_PROXY_API_TOKEN=your-api-token-here

# Optional: Database submission
SUBMIT_VALIDATOR_INFO=true
DB_SUBMIT_INTERVAL_SECONDS=300
LOGGING_LEVEL=info
```

### 5. Run Validator

**Using Docker Compose (Recommended)**:

```bash
cd dogelayer/validator

# Create necessary directories
mkdir -p data config

# Start validator
docker compose up -d

# View logs
docker compose logs -f

# Stop validator
docker compose down
```

**For complete step-by-step instructions**, see the [Validator Setup Guide](./docs/running_validator.md).


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

### Complete Guides
- [Miner Setup Guide](./docs/running_miner.md) - Complete guide for setting up and running a DogeLayer miner
- [Validator Setup Guide](./docs/running_validator.md) - Complete guide for setting up and running a DogeLayer validator



---

# Subnet Information

## Production Environment (Finney Mainnet)
- **Subnet ID (netuid)**: 109
- **Network**: Finney (mainnet)
- **Network Parameter**: `--subtensor.network finney`
- **Algorithm**: Scrypt (LTC/DOGE)
- **Pool Address**: `stratum+tcp://stratum.dogelayer.ai:3331`
- **Emission**: Dynamic based on contribution

---

## ⚠️ Disclaimer

This software is provided "as is" without warranty of any kind. Use at your own risk.

- Mining involves financial risk
- Always secure your wallets
- Verify all transactions
- Do your own research

---

# Get Involved

- Join the discussion on the [Bittensor Discord](https://discord.com/invite/bittensor) in the Subnet 109 channels.
- Check out the [Bittensor Documentation](https://docs.learnbittensor.org/) for general information about running subnets and nodes.

---

**Full Guides:**
- [DogeLayer Miner Setup Guide](docs/running_miner.md)
- [DogeLayer Validator Setup Guide](docs/running_validator.md)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

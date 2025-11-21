# DogeLayer Mining Guide

This guide will walk you through setting up and running a DogeLayer miner on the Bittensor network.

DogeLayer enables Scrypt miners (LTC/DOGE) to contribute hashpower to a collective mining pool. All miners direct their hashpower to a single subnet pool, where validators evaluate and rank miners based on the share value they generate.

DogeLayer miners earn from **two independent reward systems**, both designed to fairly and transparently compensate you for your computational contributions.

## Reward Systems

### 1. Mining Rewards (LTC/DOGE) - All Miners

Direct cryptocurrency earnings from actual Scrypt mining with **secondary distribution**:

- **Mining Revenue**: Earn LTC and DOGE from contributing hashpower
- **Platform Collection**: All mining rewards are first collected by the platform
- **Secondary Distribution**: Platform redistributes rewards to miners and validators based on contributions
- **Manual Withdrawal Required**: Must login to DogeLayer website to set withdrawal addresses and submit withdrawal requests
- **Processing Time**: 1-3 business days for withdrawal processing

#### How It Works
1. Connect your mining hardware to the DogeLayer pool
2. Your shares are recorded and validated
3. Mining revenue (LTC/DOGE) is collected by the platform
4. Platform performs **secondary distribution** to miners and validators based on their contributions
5. You must login to DogeLayer website to set your LTC/DOGE withdrawal addresses
6. Submit withdrawal request to receive your earnings
7. Withdrawals are processed within 1-3 business days

---

### 2. Alpha Token Rewards (Bittensor Registered Miners)

Bittensor's **Subnet 109** adds a second layer of incentives for miners who register their wallet and hotkey.

- **Value-Based Rewards**: Alpha tokens based on the hashpower value you provide
- **Value Calculation**: Based on hashprice index and current exchange rates
- **Eligibility**: Requires registration on **Bittensor Subnet 109**
- **Continuous Accumulation**: Tokens accrue automatically as you mine
- **Convertibility**: Alpha tokens can be unstaked to TAO for liquidity

This mechanism ties your physical mining to the decentralized compute economy of Bittensor — rewarding both immediate work (LTC/DOGE) and long-term network participation (Alpha).

Alpha rewards are disbursed through Bittensor's incentive mechanism every tempo. These rewards are independent of whether the pool found a block or not.

---

See also:

- [Introduction to DogeLayer](../README.md)
- [Introduction to Bittensor](https://docs.learnbittensor.org/learn/introduction)
- [Yuma Consensus](https://docs.learnbittensor.org/yuma-consensus/)
- [Emissions](https://docs.learnbittensor.org/emissions/)

## Prerequisites

To run a DogeLayer miner, you will need:

- A Bittensor wallet with coldkey and hotkey
- Scrypt mining hardware (ASICs for LTC/DOGE) OR access to remote hashrate
- Python 3.9 or higher (for registration only)
- The most recent release of [Bittensor SDK](https://pypi.org/project/bittensor/)

Bittensor Docs:

- [Wallets, Coldkeys and Hotkeys in Bittensor](https://docs.learnbittensor.org/getting-started/wallets)
- [Miner registration](https://docs.learnbittensor.org/miners/index.md#miner-registration)

## Quick Start

### Step 1: Wallet Setup

Check your wallet, or create one if you have not already.

Bittensor Documentation: [Creating/Importing a Bittensor Wallet](https://docs.learnbittensor.org/working-with-keys)

#### List wallets
```bash
btcli wallet list
```
```console
Wallets
├── Coldkey YourColdkey  ss58_address 5F...
│   ├── Hotkey YourHotkey  ss58_address
│   │   5E...
```

#### Check wallet balance
```bash
btcli wallet balance \
  --wallet.name <your wallet name> \
  --subtensor.network finney
```

```console
                             Wallet Coldkey Balance
                                  Network: finney

    Walle…   Coldkey Address                             Free…   Stake…   Total…
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    your_…   5DvSxCaMW9tCPBS4TURmw4hDzXx5Bif51jq4baC6…   …       …        …



    Total…                                               …       …        …
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 2: Register on Subnet 109 (Mainnet)

#### Check registration status

```bash
btcli wallet overview \
  --wallet.name YOUR_WALLET \
  --netuid 109 \
  --subtensor.network finney
```

#### Register to subnet

```bash
btcli subnet register \
  --netuid 109 \
  --wallet.name YOUR_WALLET \
  --wallet.hotkey YOUR_HOTKEY \
  --subtensor.network finney
```

### Step 3: Get Your Hotkey

Your hotkey is your miner username. Get your full 48-character hotkey:

```bash
btcli wallet overview \
  --wallet.name YOUR_WALLET \
  --wallet.hotkey YOUR_HOTKEY
```

The hotkey will look like: `5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY`

### Step 4: Configure Your Mining Hardware

Use your **full 48-character hotkey** as the miner username to connect to the DogeLayer pool:

**Production Pool (Mainnet)**:
- **Stratum URL**: `stratum+tcp://stratum.dogelayer.ai:3331`
- **Worker Name**: `5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY` (your full hotkey)
- **Password**: `x`

#### Example Configuration

**For ASIC Miners** (Antminer, Whatsminer, etc.):
1. Access your miner's web interface
2. Navigate to pool configuration
3. Enter the pool details:
   - URL: `stratum+tcp://stratum.dogelayer.ai:3331`
   - Worker: Your full 48-character hotkey
   - Password: `x`

**For Mining Software** (cgminer, bfgminer, etc.):
```bash
./cgminer \
  --scrypt \
  -o stratum+tcp://stratum.dogelayer.ai:3331 \
  -u 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY \
  -p x
```

### Step 5: Start Mining

Once configured and connected:
- Your mining hardware will automatically contribute hashrate
- Shares will be recorded and validated
- You'll earn LTC/DOGE mining rewards
- If registered on Bittensor, you'll also accumulate Alpha tokens

## Monitor Performance

### Check Mining Status

You can monitor your mining performance through:

1. **Your ASIC/Mining Software Dashboard**
   - Check accepted shares
   - Monitor hashrate
   - Verify connection status

2. **DogeLayer Website** (if available)
   - View your contribution
   - Check earnings
   - Monitor ranking

3. **Bittensor Network**
   ```bash
   btcli subnet metagraph \
     --netuid 109 \
     --subtensor.network finney | grep YOUR_HOTKEY
   ```

## Withdrawing Rewards

### TAO Rewards (Automatic)

Alpha tokens are automatically sent to your hotkey:

```bash
# Check TAO balance
btcli wallet balance \
  --wallet.name YOUR_WALLET \
  --subtensor.network finney
```

### LTC/DOGE Rewards (Manual Withdrawal - Secondary Distribution)

**Important**: LTC/DOGE mining rewards go through **secondary distribution**. The platform collects all mining revenue and redistributes it to miners and validators. You must manually set up withdrawal addresses and submit withdrawal requests.

#### Step-by-Step Withdrawal Process

1. **Login to DogeLayer Website**
   - Visit the DogeLayer platform
   - Connect using your Bittensor coldkey wallet
   - Ensure you're using the correct wallet that's registered for mining

2. **Set Withdrawal Addresses**
   - Navigate to account settings or wallet management
   - Add your LTC address:
     - Legacy format: starts with 'L' or 'M'
     - SegWit format: starts with 'ltc1'
   - Add your DOGE address:
     - Standard format: starts with 'D'
   - **Verify addresses carefully** - incorrect addresses may result in loss of funds
   - Complete address verification (may require test transaction)

3. **View Your Balance**
   - Check your accumulated LTC/DOGE earnings
   - View distribution history
   - Monitor pending withdrawals

4. **Submit Withdrawal Request**
   - Select cryptocurrency (LTC or DOGE)
   - Enter withdrawal amount (must meet minimum)
   - Review withdrawal address
   - Confirm network fees
   - Submit withdrawal request (creates a withdrawal ticket)
   - Wait for processing: 1-3 business days

**Withdrawal Requirements**:
- **Minimum amounts**: LTC 0.01, DOGE 100
- **Processing time**: 1-3 business days
- **Network fees**: Deducted from withdrawal amount
- **Verification**: Large withdrawals may require additional verification
- **First withdrawal**: May take longer for security review

**Important Notes**:
- Mining rewards are distributed by the platform (secondary distribution)
- Both miners and validators must set withdrawal addresses on the website
- Withdrawals are processed manually, not automatically
- Keep your withdrawal addresses up to date
- Save transaction records for your reference

## Maximizing Your Rewards

### For Mining Rewards (LTC/DOGE)
1. **Maintain Consistent Hashrate**: Stable mining earns more consistent rewards
2. **Submit High-Difficulty Shares**: Better hardware = higher share value
3. **Minimize Downtime**: Every valid share counts toward your earnings
4. **Monitor Share Acceptance**: Check logs to ensure shares are accepted

### For Bittensor Participants (Alpha Tokens)
1. **Register on Subnet 109**: Required for Alpha rewards eligibility
2. **Keep Your Hotkey Active**: Inactive hotkeys won't earn Alpha emissions
3. **Monitor Accumulation**: Track token balances via your wallet
4. **Think Long-Term**: Alpha represents network stake — value compounds as subnet grows

---

## Total Value Proposition

| Miner Type | LTC/DOGE Rewards | Alpha Tokens | Total Return |
|-------------|------------------|--------------|--------------|
| **Non-Bittensor Miner** | ✅ Mining rewards proportional to hashpower | ❌ Not available | Mining revenue only |
| **Bittensor-Registered Miner** | ✅ Mining rewards | ✅ Alpha Token value | Mining + Alpha yield |
| **Key Benefit** | Direct cryptocurrency earnings | Long-term ecosystem stake | **Enhanced total returns** |

---

## Setting Minimum Difficulty

High-performance ASICs may require minimum difficulty settings. Append the minimum difficulty to your password:

```
x;md=100000;
```

Example:
- Worker: `5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY`
- Password: `x;md=100000;`

Note: Follow the exact format for setting difficulty.

## Troubleshooting

### Connection Issues

**Cannot connect to pool**
- Verify the pool URL: `stratum+tcp://stratum.dogelayer.ai:3331`
- Check your internet connection
- Ensure firewall isn't blocking port 3331
- Try pinging the pool server

**Shares rejected**
- Verify you're using the correct hotkey as username
- Check that your hardware supports Scrypt algorithm
- Ensure difficulty settings are appropriate
- Monitor for hardware errors

### Registration Issues

**Registration failed**
- Check wallet balance (need TAO for registration fee)
- Verify network connectivity
- Ensure using correct network (finney)
- Check subnet status

**Not receiving Alpha rewards**
- Confirm registration on subnet 109
- Verify hotkey is active and mining
- Check emission schedule
- Monitor wallet balance

### Withdrawal Issues

**Cannot set withdrawal address**
- Verify you're logged in with correct wallet
- Check address format (LTC/DOGE)
- Ensure address is valid
- Try test transaction first

**Withdrawal delayed**
- Normal processing: 1-3 business days
- Large amounts may require additional verification
- Check withdrawal history for status
- Contact support if delayed beyond 3 days

## Support

- GitHub Issues: https://github.com/dogelayer-ai/dogelayer/issues
- Bittensor Discord: Subnet 109 channel
- Documentation: https://github.com/dogelayer-ai/dogelayer/tree/main/docs

Happy mining!

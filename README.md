# Late Corner Betting Tool 🚨⚽

A sophisticated real-time football monitoring system that detects profitable late corner betting opportunities using live match data from Sportmonks API.

## 🎯 What It Does

This tool monitors live football matches and sends **Telegram alerts** when optimal conditions are detected for betting on corners in the **85th+ minute**. It uses a comprehensive scoring system based on:

- **Live Match Statistics** (shots, attacks, possession, etc.)
- **Current Corner Count** (8-11 corners = sweet spot)
- **Team Behavior Patterns** (substitutions, pressure, desperation)
- **Pre-match Context** (favorites losing/drawing)

## 🚀 Key Features

- **Real-time Monitoring**: Polls Sportmonks API every 60 seconds
- **Smart Scoring Engine**: 15+ indicators with weighted scoring
- **Telegram Alerts**: Instant notifications with betting recommendations
- **Asian Corner Focus**: Targets the "Asian Over 1 Corner" market (85th minute sweet spot)
- **Anti-Duplicate System**: Prevents spam alerts
- **Live Odds Integration**: Shows current corner betting odds when available

## 📊 Scoring System Highlights

### High Priority Indicators (3-5 points)
- ✅ **Favorite losing/drawing after 80'** (+5 points)
- ✅ **5+ shots on target in last 15min** (+4 points)  
- ✅ **6+ dangerous attacks in last 10min** (+4 points)
- ✅ **4+ shots blocked in last 10min** (+4 points)
- ✅ **3+ big chances created in last 15min** (+4 points)

### Corner Count Context
- ✅ **8-11 total corners at 85'** (+3 points) - **SWEET SPOT**
- ⚠️ **5 or fewer corners** (-2 points) - **RED FLAG**

**Alert Threshold**: 6+ points triggers notification

## 🛠️ Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Sportmonks API account (for live match data)
- Telegram account (for alerts)

### 2. Get API Keys

#### Sportmonks API
1. Go to [Sportmonks.com](https://sportmonks.com/)
2. Sign up for an account
3. Choose a plan that includes **Live Scores API** and **Odds API**
4. Copy your API token

#### Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token
4. Message [@userinfobot](https://t.me/userinfobot) to get your chat ID

### 3. Installation

```bash
# Clone or download the project
cd latecorners

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env_example.txt .env

# Edit .env with your API keys
nano .env
```

### 4. Configuration

Edit the `.env` file with your actual values:

```bash
SPORTMONKS_API_KEY=your_actual_api_key_here
TELEGRAM_BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789
```

### 5. Run the System

```bash
# Start monitoring
python main.py
```

You should see:
```
🚀 Starting Late Corner Monitor...
🔍 Testing connections...
✅ Sportmonks API connected - found X live matches
✅ Telegram bot connected
✅ All systems ready. Starting match monitoring...
```

## 📱 Sample Alert

When conditions are met, you'll receive a Telegram message like:

```
🚨 LATE CORNER ALERT 🚨

Arsenal vs Chelsea
📊 Score: 1-1 | ⏱️ 87'
🏆 Premier League

🎯 ALERT SCORE: 8.5
(Threshold: 6)

📈 Focus Team: Arsenal
(Most likely to generate corners)

🔥 Key Conditions:
1. Favorite drawing after 80'
2. 6 shots on target in last 15min
3. 9 corners (SWEET SPOT)
4. 7 dangerous attacks in last 10min
5. Attacking sub after 70'

💰 BETTING RECOMMENDATION:
Asian Over 1 Corner
• Get money back if exactly 1 corner
• Win if 2+ corners
• Optimal entry: NOW (85th minute sweet spot)

📊 Live Corner Odds:
• Bet365: Over 1.5 Corners @ 1.85
• William Hill: Asian +1 Corner @ 1.90

🤖 Late Corner Bot | Time: 87'
```

## ⚙️ Configuration Options

You can adjust settings in `config.py`:

- `ALERT_THRESHOLD`: Minimum score to trigger alert (default: 6)
- `MIN_MINUTE_FOR_ALERT`: Don't alert before this minute (default: 85)
- `CORNER_SWEET_SPOT_MIN/MAX`: Optimal corner count range (default: 8-11)
- `LIVE_POLL_INTERVAL`: How often to check matches (default: 60 seconds)

## 🧪 Testing

To test the system:

```bash
# This will send a test message to your Telegram
python -c "
import asyncio
from telegram_bot import TelegramNotifier
async def test():
    bot = TelegramNotifier()
    await bot.test_connection()
asyncio.run(test())
"
```

## 📝 How It Works

1. **Discovery**: Every 5 minutes, finds new live matches past 70th minute
2. **Monitoring**: Every 60 seconds, analyzes tracked matches for corner opportunities  
3. **Scoring**: Applies comprehensive scoring matrix to live statistics
4. **Alerting**: At 85+ minutes, if score ≥ 6, sends Telegram alert with odds
5. **Cleanup**: Removes finished matches and prevents duplicate alerts

## 🎲 The Strategy

This tool implements the **"Asian Over 1 Corner at 85th minute"** strategy:

- **Why 85th minute?** Perfect balance of desperation vs. time remaining
- **Why Asian bet?** Get money back if exactly 1 corner occurs
- **Why this scoring system?** Combines statistical analysis with expert insights
- **Sweet spot logic**: 8-11 total corners indicates active game with room for more

## ⚠️ Important Notes

- This is a **tool for analysis**, not guaranteed profits
- Always practice responsible gambling
- Test thoroughly before live use
- Monitor API rate limits to avoid being blocked
- Corner betting can be volatile - use appropriate bankroll management

## 🔧 Troubleshooting

### No alerts appearing
- Check logs in `latecorners.log`
- Verify API keys are correct
- Ensure there are live matches past 70th minute
- Try lowering `ALERT_THRESHOLD` for testing

### Telegram not working
- Verify bot token and chat ID
- Make sure bot is not blocked
- Check internet connectivity

### API errors
- Verify Sportmonks subscription includes live data
- Check rate limiting (reduce `LIVE_POLL_INTERVAL` if needed)
- Ensure API key has sufficient calls remaining

## 📊 Success Metrics

The system tracks:
- Number of matches monitored
- Alerts triggered vs. actual corner outcomes
- API call efficiency
- Alert accuracy

Monitor the logs to analyze performance and adjust thresholds as needed.

---

**Good luck with your late corner betting! 🍀⚽** 
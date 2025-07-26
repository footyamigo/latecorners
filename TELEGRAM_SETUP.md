# 🤖 Telegram Corner Alert Setup Guide

## 📱 Step 1: Create Your Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Send** `/newbot` to BotFather
3. **Choose a name** for your bot (e.g., "Corner Alert Bot")
4. **Choose a username** (e.g., "your_corner_alert_bot")
5. **Copy the bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## 💬 Step 2: Get Your Chat ID

1. **Start a chat** with your new bot
2. **Send any message** to your bot (e.g., "Hello")
3. **Visit this URL** in your browser (replace `<YOUR_BOT_TOKEN>` with your actual token):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
4. **Find your chat ID** in the response (looks like: `"chat":{"id":123456789}`)
5. **Copy the chat ID number** (e.g., `123456789`)

## 📝 Step 3: Update Your .env File

Add these lines to your `.env` file:

```bash
# Existing SportMonks configuration
SPORTMONKS_API_KEY=your_existing_api_key

# NEW: Telegram configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

## 🧪 Step 4: Test Your Setup

Run the test script to verify everything works:

```bash
python telegram_test.py
```

## 🚨 Step 5: Start Getting Alerts!

Once setup is complete, your corner system will automatically send Telegram alerts when:

- ✅ Match reaches **85 minutes**
- ✅ Good corner betting conditions detected
- ✅ Asian corner odds available on bet365

## 📱 What Your Alerts Look Like

```
🚨 CORNER ALERT 🚨

⚽ Liverpool vs Manchester United
📊 Score: 1-1 (85')

🎯 ASIAN CORNER (OVER)
📈 Current: 8 corners
🔥 Confidence: HIGH
💡 Perfect corner count (8) - teams pushing for winner

💰 bet365 Asian Total Corners
✅ Live odds confirmed available

⚡ ACTION:
1. Open bet365
2. Search "Liverpool Manchester United"  
3. Go to Asian Corner market
4. Place OVER bet NOW

🕐 Alert: 20:45:30
```

## 🔧 Troubleshooting

- **Bot not responding?** Check your bot token
- **Test message not received?** Verify your chat ID
- **"Unauthorized" error?** Make sure you started a chat with your bot first
- **Still having issues?** Run `python telegram_test.py` for detailed diagnostics

---

**🎯 Ready to receive corner betting alerts directly on your phone!** 
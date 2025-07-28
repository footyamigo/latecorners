# 🚂 Railway MVP Deployment Guide

## ⚠️ CRITICAL: Fix Security Issue First

**Your Telegram bot token was exposed in git - regenerate it NOW:**

1. Open Telegram, message `@BotFather`
2. Send: `/revoke` → select your bot → confirm
3. Send: `/newbot` or `/token` to get a new token
4. **Write down the new token** - you'll need it for Railway

## 🚀 Deploy to Railway (5 minutes)

### Step 1: Connect to Railway
1. Go to [railway.app](https://railway.app) and sign up/login with GitHub
2. Click "Deploy from GitHub repo"
3. Select your `latecorners` repository

### Step 2: Configure Environment Variables
In Railway dashboard, go to **Variables** tab and add:

```
SPORTMONKS_API_KEY=your_sportmonks_api_key
TELEGRAM_BOT_TOKEN=your_NEW_regenerated_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### Step 3: Deploy
1. Railway will automatically build and deploy
2. Check the **Deployments** tab for progress
3. Look for "✅ Build completed" and "✅ Deployed"

### Step 4: Verify It's Working
1. In Railway dashboard, check **Logs** tab
2. Look for: `🚀 Starting Combined Late Corner System...`
3. Then: `🚨 Starting alert system...` and `🌐 Starting web dashboard...`
4. You should get a startup message in Telegram
5. Visit your Railway app URL to see the live dashboard

## 🎯 What This MVP Does

✅ **Monitors live football matches** every 60 seconds  
✅ **Sends Telegram alerts** when corner opportunities detected  
✅ **Live web dashboard** to view matches and stats
✅ **Automatic restarts** if anything crashes  
✅ **Health monitoring** built-in  
✅ **Zero maintenance** required  

## 💰 Railway Costs

- **Hobby Plan**: $5/month (perfect for MVP)
- **Pro Plan**: $20/month (if you need more resources)

## 🔧 Configuration (Optional)

You can adjust these in Railway Variables:

```
ALERT_THRESHOLD=6              # Lower = more alerts
MIN_MINUTE_FOR_ALERT=85       # Don't alert before 85th minute
LIVE_POLL_INTERVAL=60         # Check every 60 seconds
```

## 🚨 Troubleshooting

### No alerts coming through?
1. Check Railway **Logs** for errors
2. Verify API keys are correct in **Variables**
3. Make sure there are live matches (evenings/weekends)

### "Connection failed" errors?
1. Check your Sportmonks API quota at [sportmonks.com](https://sportmonks.com)
2. Verify subscription includes "Live Scores API"

### Telegram bot not responding?
1. Make sure you regenerated the bot token
2. Check you're using the correct chat ID
3. Message the bot directly to ensure it's not blocked

## 📱 Getting Your Chat ID

If you need to find your Telegram chat ID:
1. Message `@userinfobot` on Telegram
2. Copy the number it gives you
3. Add it to Railway Variables as `TELEGRAM_CHAT_ID`

## ✅ Success Checklist

- [ ] New Telegram bot token generated
- [ ] Repository connected to Railway
- [ ] Environment variables configured
- [ ] Deployment successful (green checkmark)
- [ ] Startup message received in Telegram
- [ ] Logs show "Starting match monitoring..."

**That's it! Your MVP is live and monitoring matches 24/7.** 🎉

## 🌐 Accessing Your Web Dashboard

After deployment, Railway will give you a URL like: `https://your-app-name.up.railway.app`

- **📱 Telegram alerts**: Automatic (no action needed)
- **🌐 Web dashboard**: Visit your Railway URL in any browser
- **📊 Live data**: See current matches, stats, and system status

---

## 🔮 Next Steps (When Ready)

After your MVP is running successfully:
1. **Monitor performance** for a week
2. **Track alert accuracy** manually
3. **Consider adding database** for historical tracking
4. **Scale up** if you want more features

**For now, just enjoy getting live corner betting alerts!** ⚽📱 
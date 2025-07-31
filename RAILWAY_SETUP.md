# 🚀 Railway Deployment Guide - PostgreSQL Setup

## 📋 Overview
This guide shows you how to deploy your Elite Corner Alert system on Railway with PostgreSQL for persistent data storage.

## 🎯 Step-by-Step Setup

### 1. **Add PostgreSQL to Railway**
1. Go to [railway.app](https://railway.app)
2. Login and select your project
3. Click **"Add Service"**
4. Select **"Database" → "PostgreSQL"**
5. ✅ Done! Railway automatically creates:
   - `DATABASE_URL` environment variable
   - Connection credentials
   - Persistent storage

### 2. **Verify Your Code is Ready**
Run this test locally first:
```bash
python test_postgres_connection.py
```

**Expected Output:**
```
🚀 CHECKING RAILWAY REQUIREMENTS...
✅ psycopg2-binary found in requirements.txt
✅ database_postgres.py exists
✅ database.py exists (import wrapper)
🎉 ALL RAILWAY REQUIREMENTS MET!
```

### 3. **Deploy to Railway**
```bash
# Standard deployment
git add .
git commit -m "Add PostgreSQL database support"
git push origin main
```

**Railway automatically:**
- ✅ Installs `psycopg2-binary`
- ✅ Creates PostgreSQL database
- ✅ Sets `DATABASE_URL` environment variable
- ✅ Starts your application

### 4. **Monitor Database Activity**
Watch your Railway logs for:
```
✅ PostgreSQL database initialized successfully
✅ Alert saved to PostgreSQL: 123456
📋 Found 0 unfinished alerts
📈 Stats: {'total_alerts': 0, 'wins': 0, 'losses': 0, 'refunds': 0, 'pending': 0, 'win_rate': 0}
```

---

## 🗄️ Database Features

### **Automatic Table Creation**
Your first alert will automatically create:
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fixture_id INTEGER NOT NULL,
    teams VARCHAR(255) NOT NULL,
    score_at_alert VARCHAR(50),
    minute_sent INTEGER,
    corners_at_alert INTEGER,
    elite_score FLOAT,
    over_line VARCHAR(20),
    over_odds VARCHAR(20),
    final_corners INTEGER DEFAULT NULL,
    result VARCHAR(20) DEFAULT NULL,
    checked_at TIMESTAMP DEFAULT NULL,
    match_finished BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Performance Tracking**
Your logs will show:
```
📊 DATABASE STATS:
   Total Alerts: 15
   Wins: 8 (53.3%)
   Losses: 4 (26.7%)
   Pending: 3 (20.0%)
   ROI: +12.4 units
```

---

## 🔍 Accessing Your Data

### **Via Railway Logs**
```bash
railway logs --follow
```

### **Via Railway Shell** (Advanced)
```bash
railway shell
python analyze_performance.py
```

### **Via Web Dashboard**
Your performance data appears automatically in your system logs.

---

## ✅ Benefits of PostgreSQL

### **vs SQLite:**
- ✅ **Guaranteed persistence** (no data loss on deployments)
- ✅ **Better performance** for concurrent access
- ✅ **Automatic backups** by Railway
- ✅ **Production-ready** and scalable
- ✅ **No file management** required

### **Data Safety:**
- ✅ **Railway manages backups**
- ✅ **No manual database files**
- ✅ **Automatic scaling**
- ✅ **24/7 monitoring**

---

## 🛠️ Troubleshooting

### **Common Issues:**

**1. Import Error:**
```
ModuleNotFoundError: No module named 'psycopg2'
```
**Fix:** Check `requirements.txt` includes `psycopg2-binary`

**2. Connection Error:**
```
❌ Database connection failed
```
**Fix:** Ensure PostgreSQL service is added to Railway project

**3. Environment Variable Missing:**
```
❌ DATABASE_URL environment variable not found
```
**Fix:** PostgreSQL service automatically creates this

---

## 🎉 Success Indicators

Look for these in your Railway logs:
```
✅ PostgreSQL database initialized successfully
✅ Alert saved to PostgreSQL: 123456
🔍 Checking results for 3 pending alerts...
📈 Performance: 8W-4L-3P (53% win rate)
```

---

## 📊 Performance Monitoring

Your system automatically tracks:
- **WIN:** Final corners > over line
- **LOSS:** Final corners < over line  
- **REFUND:** Final corners = over line (whole numbers only)
- **Win Rate:** (Wins / Completed bets) × 100
- **ROI:** Profit/loss tracking

**Ready to deploy? Your data will be safe with PostgreSQL!** 🚀 
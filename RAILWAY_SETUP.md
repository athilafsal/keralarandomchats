# 🚂 Complete Railway Setup Guide

This guide will help you set up your bot on Railway with all required services.

## Prerequisites

- Railway account ([railway.app](https://railway.app))
- GitHub repository connected (already done: `keralarandomchats`)
- Bot token from @BotFather

## Step-by-Step Setup

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose your repository: `athilafsal/keralarandomchats`
6. Railway will start deploying automatically

### Step 2: Add PostgreSQL Database

**This is REQUIRED - Railway will auto-set `DATABASE_URL`**

1. In your Railway project, click **"New"** button
2. Select **"Database"**
3. Choose **"Add PostgreSQL"**
4. Railway will automatically:
   - Create a PostgreSQL database
   - Set `DATABASE_URL` environment variable
   - Link it to your service

**✅ You'll see `DATABASE_URL` appear in your service's Variables tab automatically**

### Step 3: Add Redis

**This is REQUIRED - Railway will auto-set `REDIS_URL`**

1. In your Railway project, click **"New"** button again
2. Select **"Database"**
3. Choose **"Add Redis"**
4. Railway will automatically:
   - Create a Redis instance
   - Set `REDIS_URL` environment variable
   - Link it to your service

**✅ You'll see `REDIS_URL` appear in your service's Variables tab automatically**

### Step 4: Set Environment Variables

Go to your **service** (not the database services) → **"Variables"** tab

Add these variables:

1. **`BOT_TOKEN`**
   - Value: `8356283788:AAGLDJtWcGfRWvxk_JnPWJ1SlmgbhE7a8_0`
   - No quotes, no spaces

2. **`ADMIN_SECRET`**
   - Value: Create a strong password (at least 16 characters)
   - Example: Use a password generator
   - This is for admin access to your bot

3. **`WEBHOOK_URL`** (Optional but recommended)
   - Value: `https://web-production-88d3.up.railway.app/webhook`
   - This is your webhook URL

**Note:** `DATABASE_URL` and `REDIS_URL` are automatically set by Railway when you add the addons. You don't need to set them manually!

### Step 5: Verify Variables

Your Variables tab should show:

- ✅ `DATABASE_URL` (auto-set by PostgreSQL addon)
- ✅ `REDIS_URL` (auto-set by Redis addon)
- ✅ `BOT_TOKEN` (you set this)
- ✅ `ADMIN_SECRET` (you set this)
- ✅ `WEBHOOK_URL` (optional)

### Step 6: Initialize Database

After Railway deploys, initialize the database:

**Option A: Using Railway CLI**
```bash
railway run python init_db.py
```

**Option B: Using Railway Dashboard**
1. Go to your service → **"Deployments"** tab
2. Click on the latest deployment
3. Click **"View Logs"**
4. Look for database initialization messages

The app will also warn you if tables don't exist.

### Step 7: Set Telegram Webhook

Set the webhook in Telegram:

```bash
curl "https://api.telegram.org/bot8356283788:AAGLDJtWcGfRWvxk_JnPWJ1SlmgbhE7a8_0/setWebhook?url=https://web-production-88d3.up.railway.app/webhook"
```

**Expected response:**
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

### Step 8: Test Your Bot

1. Open Telegram
2. Find your bot
3. Send `/start`
4. The bot should respond! ✅

## Troubleshooting

### ❌ "DATABASE_URL not set" Error

**Solution:**
1. Make sure you added PostgreSQL addon (Step 2)
2. Check that PostgreSQL service is in the same Railway project
3. Verify in Variables tab that `DATABASE_URL` exists
4. If missing, add PostgreSQL addon again
5. Redeploy your service

### ❌ "REDIS_URL not set" Error

**Solution:**
1. Make sure you added Redis addon (Step 3)
2. Check that Redis service is in the same Railway project
3. Verify in Variables tab that `REDIS_URL` exists
4. If missing, add Redis addon again
5. Redeploy your service

### ❌ Bot Not Responding

1. **Check Railway Logs:**
   - Service → Deployments → Latest deployment → View Logs
   - Look for errors

2. **Verify Webhook:**
   ```bash
   curl "https://api.telegram.org/bot8356283788:AAGLDJtWcGfRWvxk_JnPWJ1SlmgbhE7a8_0/getWebhookInfo"
   ```

3. **Check Database:**
   - Make sure `init_db.py` was run
   - Check logs for database errors

### ❌ Service Keeps Crashing

1. Check Railway logs for specific error messages
2. Verify all environment variables are set
3. Make sure PostgreSQL and Redis addons are running
4. Check that your service is linked to the database services

## Quick Checklist

- [ ] Railway project created
- [ ] GitHub repo connected
- [ ] PostgreSQL addon added (auto-sets `DATABASE_URL`)
- [ ] Redis addon added (auto-sets `REDIS_URL`)
- [ ] `BOT_TOKEN` set in Variables
- [ ] `ADMIN_SECRET` set in Variables
- [ ] `WEBHOOK_URL` set in Variables (optional)
- [ ] Database initialized (`python init_db.py`)
- [ ] Webhook set in Telegram
- [ ] Bot tested with `/start`

## Your Current Setup

Based on your information:
- **Webhook URL:** `https://web-production-88d3.up.railway.app/webhook`
- **Bot Token:** `8356283788:AAGLDJtWcGfRWvxk_JnPWJ1SlmgbhE7a8_0`

**Still needed:**
- ✅ Add PostgreSQL addon (to get `DATABASE_URL`)
- ✅ Add Redis addon (to get `REDIS_URL`)
- ✅ Set `ADMIN_SECRET` variable
- ✅ Initialize database
- ✅ Set webhook in Telegram

## Need Help?

Check the logs in Railway dashboard for specific error messages. The improved error messages will guide you to the exact issue.


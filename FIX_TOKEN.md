# 🔧 Quick Fix: Invalid Token Error

## The Problem
```
telegram.error.InvalidToken: The token was rejected by the server.
HTTP/1.1 401 Unauthorized
```

## The Solution (5 Steps)

### Step 1: Get New Token
1. Go to https://t.me/BotFather
2. Send `/token`
3. Select your bot
4. Click "Revoke current token" → "Generate new token"
5. **Copy the NEW token immediately**

### Step 2: Update Railway
1. Open Railway dashboard
2. Go to your service → **Variables** tab
3. Find `BOT_TOKEN`
4. Click **Edit**
5. **Delete the old token completely**
6. Paste the NEW token (no spaces before/after)
7. Click **Save**

### Step 3: Verify Procfile
Make sure your `Procfile` contains:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Step 4: Redeploy
- Railway will auto-redeploy when you save the variable
- OR manually trigger: Deployments → Redeploy

### Step 5: Check Logs
Look for:
```
✅ Telegram bot initialized successfully
```

If you still see errors, the token might still be wrong. Double-check:
- No extra spaces
- No quotes around the token
- Copied the entire token (both parts: `numbers:letters`)

## Why This Happens
- Token was exposed in logs/publicly → Telegram revoked it
- Token was manually revoked in @BotFather
- Token has a typo or extra character
- Token is for a different bot

## Prevention
- Never commit tokens to Git
- Never share tokens publicly
- Use environment variables (Railway Variables tab)
- Regenerate tokens if exposed


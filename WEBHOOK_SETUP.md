# 🔗 How to Get and Set Your Webhook URL

## Step 1: Get Your Railway App URL

1. **Go to Railway Dashboard:**
   - Visit [railway.app](https://railway.app)
   - Sign in to your account

2. **Find Your Service:**
   - Click on your project
   - Click on your service (the one running the bot)

3. **Get the Domain:**
   - Go to the **"Settings"** tab
   - Scroll down to **"Networking"** section
   - Look for **"Domain"** or **"Custom Domain"**
   - You'll see something like: `your-app-name.up.railway.app`
   
   **OR**
   
   - Go to the **"Deployments"** tab
   - Click on the latest deployment
   - Look for the **"Public URL"** or **"Domain"**
   - It will look like: `https://your-app-name.up.railway.app`

4. **Copy the Full URL:**
   - Your webhook URL will be: `https://your-app-name.up.railway.app/webhook`
   - Make sure it includes:
     - `https://` (required by Telegram)
     - Your app domain (e.g., `your-app-name.up.railway.app`)
     - `/webhook` at the end

## Step 2: Set the Webhook in Telegram

Once you have your Railway URL, set it as the webhook:

### Option A: Using curl (Command Line)

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app-name.up.railway.app/webhook"
```

**Replace:**
- `<YOUR_BOT_TOKEN>` with your actual bot token (e.g., `8356283788:AAGLDJtWcGfRWvxk_JnPWJ1SlmgbhE7a8_0`)
- `your-app-name.up.railway.app` with your actual Railway domain

**Example:**
```bash
curl "https://api.telegram.org/bot8356283788:AAGLDJtWcGfRWvxk_JnPWJ1SlmgbhE7a8_0/setWebhook?url=https://keralarandomchats.up.railway.app/webhook"
```

**Expected Response:**
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

### Option B: Using Browser

Open this URL in your browser (replace with your values):
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app-name.up.railway.app/webhook
```

You should see: `{"ok":true,"result":true,"description":"Webhook was set"}`

### Option C: Verify Webhook is Set

Check if webhook is configured:
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

This will show you:
- Current webhook URL
- Last error (if any)
- Pending update count

## Step 3: Update Railway Environment Variable

1. **Go to Railway Dashboard:**
   - Your service → **"Variables"** tab

2. **Add/Update `WEBHOOK_URL`:**
   - Find `WEBHOOK_URL` (or create it if it doesn't exist)
   - Set the value to: `https://your-app-name.up.railway.app/webhook`
   - Click **"Save"**

   **Note:** This is optional but recommended for reference.

## Step 4: Test Your Bot

1. Open Telegram
2. Find your bot (search by username)
3. Send `/start`
4. If the bot responds, your webhook is working! ✅

## Troubleshooting

### ❌ Webhook not working?

1. **Check Railway Deployment:**
   - Make sure your app is deployed and running
   - Check the logs for errors

2. **Verify HTTPS:**
   - Telegram requires HTTPS
   - Railway provides HTTPS automatically
   - Make sure your URL starts with `https://`

3. **Check Webhook Endpoint:**
   - The endpoint must be `/webhook` (as defined in `main.py`)
   - Full URL: `https://your-domain.up.railway.app/webhook`

4. **Verify Bot Token:**
   - Make sure `BOT_TOKEN` is set correctly in Railway
   - Check Railway logs for token errors

5. **Check Webhook Info:**
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
   ```
   - Look for error messages
   - Check if `pending_update_count` is increasing (means webhook is receiving updates)

### Common Errors

- **"Webhook was set"** but bot doesn't respond:
  - Check Railway logs
  - Verify the app is running
  - Make sure database is initialized

- **"Bad Request" or "404":**
  - Check the URL format
  - Make sure `/webhook` is at the end
  - Verify HTTPS is used

- **"Unauthorized":**
  - Bot token is incorrect
  - Update `BOT_TOKEN` in Railway

## Quick Reference

**Your Webhook URL Format:**
```
https://[your-railway-domain]/webhook
```

**Set Webhook Command:**
```bash
curl "https://api.telegram.org/bot[BOT_TOKEN]/setWebhook?url=https://[your-railway-domain]/webhook"
```

**Check Webhook Status:**
```bash
curl "https://api.telegram.org/bot[BOT_TOKEN]/getWebhookInfo"
```


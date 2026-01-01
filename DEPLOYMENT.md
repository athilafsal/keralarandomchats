# Deployment Guide

## Quick Start

1. **Get Bot Token:**
   - Talk to [@BotFather](https://t.me/BotFather) on Telegram
   - Create a new bot: `/newbot`
   - Copy the bot token

2. **Set Up Railway:**
   - Go to [railway.app](https://railway.app)
   - Create new project
   - Connect your Git repository

3. **Add Services:**
   - Add PostgreSQL database (provides `DATABASE_URL`)
   - Add Redis (provides `REDIS_URL`)

4. **Configure Environment Variables:**
   - Go to your service → "Variables" tab
   - Add these variables:
     - **`BOT_TOKEN`** - Get this from [@BotFather](https://t.me/BotFather) on Telegram:
       1. Send `/newbot` to @BotFather
       2. Follow the prompts to create your bot
       3. Copy the token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
     - **`ADMIN_SECRET`** - Create a strong password (use a password generator, at least 16 characters)
     - **`WEBHOOK_URL`** - Leave empty for now, will set after deployment
   - **Important:** Never share these values publicly!

5. **Initialize Database:**
   ```bash
   railway run python init_db.py
   ```

6. **Set Webhook:**
   ```bash
   curl "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://your-app.up.railway.app/webhook"
   ```

## Testing

1. Start a chat with your bot on Telegram
2. Send `/start` to begin onboarding
3. Complete the registration flow
4. Use `/next` to find a chat partner

## Admin Access

1. Send `/admin <your_admin_secret>` to the bot
2. Admin session lasts 2 hours
3. Use `/admin list_online` to see statistics
4. Use `/admin help` for all admin commands

## Troubleshooting

### Common Errors

#### ❌ `telegram.error.InvalidToken: The token was rejected by the server`

**Cause:** The bot token is invalid, incorrect, or has been revoked by Telegram.

**Solutions:**
1. **Get a NEW token from @BotFather:**
   - Go to [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/token` to see your existing bots
   - Select your bot and choose "Revoke current token" → "Generate new token"
   - OR create a new bot with `/newbot`
   - Copy the NEW token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Update Railway environment variable:**
   - Go to Railway dashboard → Your service → Variables tab
   - Find `BOT_TOKEN`
   - Click "Edit" and paste the NEW token
   - Make sure there are NO extra spaces before/after the token
   - Click "Save"

3. **Redeploy:**
   - Railway will automatically redeploy when you save the variable
   - OR manually trigger a redeploy from the Deployments tab

4. **Verify the token format:**
   - Should be: `{numbers}:{letters_numbers_hyphens}`
   - Example: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - No spaces, no quotes, no special characters except `:` and alphanumeric

**Why this happens:**
- Token was copied incorrectly (typos, extra spaces)
- Token was exposed publicly (in logs, GitHub, etc.) and Telegram revoked it
- Token was manually revoked in @BotFather
- Token format is invalid

#### Other Issues

- **Bot not responding:** Check Railway logs and webhook URL
- **Database errors:** Ensure `init_db.py` was run
- **Redis errors:** Check Redis addon is attached and `REDIS_URL` is set
- **Webhook errors:** Verify the webhook URL is accessible (HTTPS required)
- **Application crashes on startup:** Check Railway logs for detailed error messages


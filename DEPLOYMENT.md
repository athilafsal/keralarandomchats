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
   - `BOT_TOKEN` - Your Telegram bot token
   - `ADMIN_SECRET` - Strong secret for admin access
   - `WEBHOOK_URL` - Set after deployment (e.g., `https://your-app.up.railway.app`)

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

- **Bot not responding:** Check Railway logs and webhook URL
- **Database errors:** Ensure `init_db.py` was run
- **Redis errors:** Check Redis addon is attached and `REDIS_URL` is set
- **Webhook errors:** Verify the webhook URL is accessible (HTTPS required)


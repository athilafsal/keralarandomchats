# Telegram Anonymous Chat Bot

An anonymous one-to-one text chat service for Telegram users in Kerala, with gender preferences, language filtering, referral system, and admin controls.

## Features

- Anonymous one-to-one text chat pairing
- Gender and language preference matching (Malayalam/English/Hindi)
- Referral system with feature unlocking (5 referrals = unlock premium features)
- Admin controls for moderation and user management
- Reporting and blocking system
- Rate limiting and spam detection
- Profanity filtering

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Telegram SDK**: python-telegram-bot
- **Database**: PostgreSQL (via Railway Postgres addon)
- **Queue**: Redis (via Railway Redis addon)
- **Deployment**: Railway

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```
5. Get your bot token from [@BotFather](https://t.me/BotFather) on Telegram
6. Set `BOT_TOKEN` and `ADMIN_SECRET` in `.env`

## Railway Deployment

1. **Create Railway Project:**
   - Go to [railway.app](https://railway.app) and create a new project
   - Connect your Git repository

2. **Add Database:**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway automatically provides `DATABASE_URL` environment variable

3. **Add Redis:**
   - Click "New" → "Database" → "Add Redis"
   - Railway automatically provides `REDIS_URL` environment variable

4. **Set Environment Variables:**
   - Go to your service → "Variables"
   - Add the following:
     - `BOT_TOKEN` - Your bot token from @BotFather
     - `ADMIN_SECRET` - A strong secret for admin authentication
     - `WEBHOOK_URL` - Set this after deployment (your Railway domain)

5. **Deploy:**
   - Railway will automatically deploy when you push to your repository
   - Check the "Deployments" tab for build logs

6. **Initialize Database:**
   - After first deployment, run database initialization:
     - Option A: Use Railway CLI: `railway run python init_db.py`
     - Option B: Add it to startup (see main.py - it will warn if tables don't exist)

7. **Set Telegram Webhook:**
   - Get your Railway domain from the service settings (e.g., `your-app.up.railway.app`)
   - Set the webhook:
     ```bash
     curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app.up.railway.app/webhook"
     ```
   - Update `WEBHOOK_URL` in Railway variables to match

## Database Initialization

For first-time setup, initialize the database:
```bash
python init_db.py
```

This creates all required tables. The application will warn if tables are missing.

## Development

Run locally:
```bash
uvicorn main:app --reload
```

## License

MIT


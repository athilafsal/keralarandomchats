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

1. **Clone the repository:**
   ```bash
   git clone https://github.com/athilafsal/randomchats.git
   cd randomchats
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Get your Bot Token:**
   - Talk to [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot` and follow the instructions
   - Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

5. **Create `.env` file:**
   ```bash
   # On Linux/Mac:
   cp .env.example .env
   
   # On Windows:
   copy .env.example .env
   ```

6. **Edit `.env` and add your credentials:**
   ```env
   BOT_TOKEN=your_actual_bot_token_from_botfather
   ADMIN_SECRET=your_strong_admin_password_here
   ```
   
   **Important:** 
   - Never commit the `.env` file to git (it's already in `.gitignore`)
   - Use a strong, random password for `ADMIN_SECRET`
   - The `DATABASE_URL` and `REDIS_URL` will be automatically provided by Railway when you add the addons

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
   - Go to your service → "Variables" tab
   - Click "New Variable" and add:
     - **`BOT_TOKEN`** - Your bot token from @BotFather (e.g., `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
     - **`ADMIN_SECRET`** - A strong, random password for admin access (e.g., use a password generator)
     - **`WEBHOOK_URL`** - Leave empty for now, set after deployment
   - **Note:** `DATABASE_URL` and `REDIS_URL` are automatically set by Railway when you add the addons

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


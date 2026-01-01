# 🗄️ Initialize Database - Quick Fix

## The Problem

Error: `relation "users" does not exist` or `relation "pairs" does not exist`

This means the database tables haven't been created yet.

## Solution: Run Database Initialization

### Option 1: Using Railway CLI (Recommended)

1. **Install Railway CLI** (if not already installed):
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Link to your project**:
   ```bash
   railway link
   ```
   Select your project when prompted.

4. **Run the initialization script**:
   ```bash
   railway run python init_db.py
   ```

5. **Expected output**:
   ```
   INFO - Creating database tables...
   INFO - Created users table
   INFO - Created pairs table
   INFO - Created referrals table
   INFO - Created admin_logs table
   INFO - Created messages table
   INFO - Created index on messages.created_at
   INFO - Created reports table
   INFO - ✅ Database initialization complete!
   ```

### Option 2: Using Railway Dashboard

1. Go to Railway dashboard
2. Click on your **web** service
3. Go to **"Deployments"** tab
4. Click on the latest deployment
5. Click **"View Logs"** or **"Shell"** (if available)
6. Run: `python init_db.py`

**Note:** Railway dashboard may not have a direct shell option. Option 1 (CLI) is more reliable.

### Option 3: Add to Startup (Automatic)

If you want the database to auto-initialize on first run, we can modify the code to do this automatically. However, it's better to run it manually once to ensure it works.

## Verify Tables Are Created

After running `init_db.py`, you can verify:

1. **Check Railway logs** - you should see "✅ Database initialization complete!"
2. **Test your bot** - send `/start` to your bot
3. **No more errors** - the "relation does not exist" errors should be gone

## What Gets Created

The script creates these tables:
- ✅ `users` - User accounts and preferences
- ✅ `pairs` - Active chat pairs
- ✅ `referrals` - Referral tracking
- ✅ `admin_logs` - Admin action logs
- ✅ `messages` - Chat message history
- ✅ `reports` - User reports

## Troubleshooting

### ❌ "DATABASE_URL not set" error

Make sure PostgreSQL addon is added and linked to your web service.

### ❌ "Connection refused" error

Make sure PostgreSQL service is online (green status).

### ❌ Script runs but tables still don't exist

1. Check which database you're connected to
2. Verify DATABASE_URL points to the correct database
3. Check Railway logs for any errors during initialization

## Quick Command Reference

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# Initialize database
railway run python init_db.py
```

After this, your bot should work! 🎉


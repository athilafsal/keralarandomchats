# 🔧 Fix: REDIS_URL Not Set (Even Though Redis Service Exists)

## The Problem

You have Redis service added in Railway, but `REDIS_URL` environment variable is not being set automatically.

## Solution: Link Redis Service to Your Web Service

### Step 1: Verify Services Are in Same Project

1. Make sure **Postgres**, **Redis**, and **web** services are all in the **same Railway project**
2. Check they're all in the **same environment** (e.g., "production")

### Step 2: Link Redis to Web Service

**Option A: Using Railway Dashboard (Recommended)**

1. Go to Railway dashboard
2. Click on your **web** service (not Redis)
3. Go to **"Settings"** tab
4. Scroll down to **"Service Connections"** or **"Variables"** section
5. Look for **"Reference Variables"** or **"Service Dependencies"**
6. You should see options to reference:
   - `${{Postgres.DATABASE_URL}}`
   - `${{Redis.REDIS_URL}}`
7. If you see Redis listed, click to add the reference
8. This will automatically create `REDIS_URL` variable

**Option B: Manual Variable Addition**

If the reference doesn't work:

1. Click on your **Redis** service
2. Go to **"Variables"** tab
3. Look for `REDIS_URL` or `REDISCLOUD_URL` or similar
4. Copy the value
5. Go to your **web** service → **"Variables"** tab
6. Click **"New Variable"**
7. Name: `REDIS_URL`
8. Value: Paste the Redis URL you copied
9. Click **"Save"**

**Option C: Check Redis Service Variables**

1. Click on **Redis** service
2. Go to **"Variables"** tab
3. Look for variables like:
   - `REDIS_URL`
   - `REDISCLOUD_URL`
   - `REDIS_HOST`
   - `REDIS_PORT`
4. If you see these, copy the `REDIS_URL` value
5. Add it to your **web** service variables

### Step 3: Verify Connection

After linking:

1. Go to **web** service → **"Variables"** tab
2. You should see `REDIS_URL` listed
3. The value should look like: `redis://default:password@host:port` or `rediss://...`

### Step 4: Redeploy

1. Railway should auto-redeploy when you add the variable
2. OR manually trigger: **Deployments** → **Redeploy**
3. Check the logs - the error should be gone!

## Alternative: Check Service Dependencies

In Railway's Architecture view:

1. Make sure the **web** service shows a connection arrow to **Redis**
2. If the arrow is dashed or missing, the services aren't properly linked
3. Try removing and re-adding the Redis service
4. Or check if there's a "Connect" or "Link" option

## Quick Fix Checklist

- [ ] Redis service is in the same project as web service
- [ ] Redis service is online (green status)
- [ ] Checked web service Variables tab for REDIS_URL
- [ ] Checked Redis service Variables tab for connection string
- [ ] Added REDIS_URL to web service (manually if needed)
- [ ] Redeployed the service
- [ ] Checked logs - error should be resolved

## Still Not Working?

If `REDIS_URL` still doesn't appear:

1. **Check Redis Service Type:**
   - Make sure you added "Redis" (not "Upstash Redis" or other variant)
   - Railway's standard Redis addon should auto-provide `REDIS_URL`

2. **Try Re-adding Redis:**
   - Remove the Redis service
   - Add it again: **New** → **Database** → **Add Redis**
   - Wait for it to provision
   - Check if `REDIS_URL` appears in web service variables

3. **Manual Redis URL Format:**
   If you need to construct it manually:
   ```
   redis://default:[password]@[host]:[port]
   ```
   You can find these values in the Redis service's Variables tab.

## Expected Result

After fixing, your **web** service Variables tab should show:
- ✅ `DATABASE_URL` (from Postgres)
- ✅ `REDIS_URL` (from Redis)
- ✅ `BOT_TOKEN` (you set)
- ✅ `ADMIN_SECRET` (you set)
- ✅ `WEBHOOK_URL` (you set)

Then the bot should start successfully! 🎉


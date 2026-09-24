# Database Setup Guide for Supabase on Render

## Problem
The error occurred because the DATABASE_URL environment variable was not correctly configured for your Supabase database connection on Render.

## Solution

### 1. Get Your Supabase Connection String

1. Go to your [Supabase Dashboard](https://app.supabase.com/)
2. Select your project
3. Click on **Project Settings** (gear icon)
4. Go to **Database**
5. Find the **Connection String** section
6. Copy the connection string

### 2. Configure Environment Variables on Render

1. Go to your [Render Dashboard](https://dashboard.render.com/)
2. Select your app
3. Click on the **Environment** tab
4. Add or update the `DATABASE_URL` variable with your connection string

### 3. Important: Fix the Connection String Format

Supabase connection strings often have the format:
```
postgresql://postgres.bkxkhxfsejootdbkrgjs:password@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
```

This is **INCORRECT**. The username should be just `postgres`, not `postgres.project-id`.

**Correct format:**
```
postgresql://postgres:YOUR_PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
```

Or use the direct connection string (find in Supabase project settings):
```
postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:6543/postgres
```

### 4. Additional Steps

#### Allow External Connections in Supabase
1. In Supabase Dashboard → Project Settings → Database
2. Go to **Connection Pooling**
3. Ensure the mode is set to **Transaction** (recommended for web apps)
4. Note the port (usually 6543)

#### Test Your Database Connection Locally
```bash
cd backend
python test_db_config.py
```

This will verify your DATABASE_URL is correctly configured.

## Changes Made

The following improvements were added to prevent this issue:

1. **Enhanced error messages** in `database.py` with clear instructions for Supabase setup
2. **Connection validation** on startup to catch configuration errors early
3. **Connection string format warning** to detect common mistakes
4. **Improved logging** with specific guidance for the correct username format

## Files Modified

- `backend/database.py` - Added connection testing and better error handling
- `backend/main.py` - Improved startup error messages
- `backend/test_db_config.py` - New test script for database configuration
- `backend/SETUP_DATABASE.md` - This guide

## Common Issues and Fixes

### Issue: "tenant/user not found"
**Fix:** Change the username from `postgres.project-id` to `postgres`

### Issue: "connection refused"
**Fix:** Check that your Supabase project is active and accepting connections

### Issue: "password authentication failed"
**Fix:** Reset your Supabase database password and update DATABASE_URL

### Issue: "FATAL: no pg_hba.conf entry"
**Fix:** Ensure your IP is whitelisted in Supabase Network Access settings

## Testing the Fix

After setting up the correct DATABASE_URL, restart your Render service and verify:

1. The app should start without the database connection error
2. The `/health` endpoint should return `"database": "ok"`
3. Database tables should be automatically created on first startup

## Getting Help

If you're still having issues:

1. Check the Render logs for detailed error messages
2. Test your connection string using `psql` or a database client
3. Verify Supabase project status and network settings
4. Ensure you're using the correct credentials
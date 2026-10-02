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

### 3. Keep the Supabase Connection Details

For a persistent Render web service, use the **Session Pooler** connection
string shown in Supabase under **Connect**. Render may not be able to reach the
direct database endpoint over IPv6. Copy the pooler host, port, and username
exactly as supplied; the username may include the project reference. The backend
selects `psycopg2` without rewriting those URL components.

### 4. Additional Steps

#### Choose the Pooler Mode
Use Session Pooler for this persistent Render service. Transaction Pooler is
intended for short-lived/serverless connections; if you select it, use its exact
host, port, and username from the Supabase dashboard.

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
3. **Pooler URL handling** preserves the host, port, username, and query parameters
4. **Improved logging** with specific guidance for the correct username format

## Files Modified

- `backend/database.py` - Added connection testing and better error handling
- `backend/main.py` - Improved startup error messages
- `backend/test_db_config.py` - New test script for database configuration
- `backend/SETUP_DATABASE.md` - This guide

## Common Issues and Fixes

### Issue: "tenant/user not found"
**Fix:** Use the username shown in the selected Supabase connection string. Pooler usernames may include the project reference.

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
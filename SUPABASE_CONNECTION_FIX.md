# Supabase Connection Fix

## Problem

The error `(ENOIDENTIFIER) no tenant identifier provided (external_id or sni_hostname required)` occurs when using Supabase's connection pooler endpoint (`pooler.supabase.com`) without proper SSL configuration.

## Root Cause

This project uses **psycopg2**, which is a different PostgreSQL driver than **psycopg3**. The two drivers have different connection parameters:

- **psycopg3** supports `sslhostname` parameter
- **psycopg2** does NOT support `sslhostname` parameter

## Solution

The `database.py` file now:
1. Checks if you're using the Supabase connection pooler (`pooler.supabase.com`)
2. Automatically extracts the project ID from your connection string
3. **Converts the pooler URL to a direct database connection URL** for psycopg2 compatibility
4. This avoids psycopg2's lack of `sslhostname` support

## What Changed

### Before
- Connection to `pooler.supabase.com` was failing
- psycopg2 was rejecting `sslhostname` parameter if manually added
- Error: "invalid dsn: invalid connection option 'sslhostname'"

### After
- Pooler URLs are automatically converted to direct connection URLs
- Uses format: `db.PROJECT_ID.supabase.co:5432` instead of `pooler.supabase.com:6543`
- Works seamlessly with psycopg2

## Connection String Formats

### For Connection Pooler (Auto-converted)
```
postgresql://postgres:YOUR_PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require
```
This will be automatically converted to:
```
postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres?sslmode=require
```

### For Direct Connection (Recommended for psycopg2)
```
postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres?sslmode=require
```

## Finding Your Project ID

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Project Settings (gear icon)
4. Find your Project ID
5. Use it in your connection string as: `db.YOUR_PROJECT_ID.supabase.co`

## Testing the Fix

1. Deploy the updated code to Render
2. The app will automatically convert pooler URLs to direct connections
3. Check the logs to ensure the app starts successfully with "Database connection established successfully"
4. If the connection still fails, double-check that your DATABASE_URL environment variable is correctly set
5. The updated code will show warnings if it can't extract the project ID automatically

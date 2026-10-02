# Supabase Connection Fix

## Driver Selection

The backend installs `psycopg2-binary`. Its SQLAlchemy URL must explicitly select
the `psycopg2` driver; otherwise SQLAlchemy 2 may try to import psycopg 3 and
fail with `ModuleNotFoundError: No module named 'psycopg'`.

The backend changes only the URL scheme to `postgresql+psycopg2://`. It does not
rewrite the username, host, port, database, or query parameters. In particular,
Supabase pooler URLs remain pooler URLs. If `sslmode` is missing, the backend
adds `sslmode=require`.

## Connection String Formats

### Session Pooler for Render

Render may not be able to route to Supabase's direct IPv6 endpoint. For a
persistent Render web service, use the **Session Pooler** connection string
shown in Supabase under **Connect**. Copy its host, port, and username exactly;
the pooler username may include the project reference. The backend only selects
the psycopg2 driver and does not rewrite those URL components.

```
postgresql://POOLER_USER:YOUR_PASSWORD@POOLER_HOST:POOLER_PORT/postgres?sslmode=require
```

Transaction Pooler URLs can also be used when appropriate; use the exact URL
Supabase provides for the selected pooler mode.

### Direct Connection
```
postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres?sslmode=require
```

## Finding Your Project ID

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Project Settings (gear icon)
4. Find your Project ID
5. Use it in your connection string as: `db.YOUR_PROJECT_ID.supabase.co`

## Deployment

After deploying, check for `Database connection established successfully`. If
connection fails, verify the `DATABASE_URL` host, port, username, password, and
SSL settings in the Supabase dashboard. Startup diagnostics redact the password.

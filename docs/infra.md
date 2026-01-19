# Infrastructure & Deployment

This document covers deployment and infrastructure setup for the Personal Health Data application.

## Table of Contents
- [Render.com Deployment](#rendercom-deployment)
- [Database Options](#database-options)
- [Environment Variables Reference](#environment-variables-reference)

---

## Render.com Deployment

### Prerequisites

1. **GitHub Repository**: Code must be pushed to GitHub
2. **Render.com Account**: Sign up at [render.com](https://render.com)
3. **PostgreSQL Database**: Create a PostgreSQL instance in Render (free tier available)
4. **Google Sheets**: Health data sheet must be accessible via CSV export

### Step 1: Create PostgreSQL Database

1. In Render.com dashboard, click "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `joeys-health` (or your preferred name)
   - **Database**: `joeys_health`
   - **User**: `admin` (or your preferred user)
   - **Region**: Choose closest to your location
   - **Plan**: Free tier (256 MB RAM, 0.1 CPU, 1 GB storage) or paid
3. Click "Create Database"
4. **Save the connection details** - you'll need:
   - Internal Database URL (for production)
   - External Database URL (for local connections)

### Step 2: Create Web Service

1. In Render.com dashboard, click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure service:
   - **Name**: `personal-health-data` (or your preferred name)
   - **Region**: Same as your database
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Runtime**: Python 3
   - **Build Command**: `uv sync --frozen && uv cache prune --ci`
   - **Start Command**: `make deploy-prod`

### Step 3: Configure Environment Variables

In the "Environment" section, add these variables:

#### Required Variables

```bash
# Database Configuration
USE_SQLITE=False

# PostgreSQL Connection (use Internal URL from your database)
PG_CONNECTION_URL_INTERNAL=postgresql://admin:PASSWORD@dpg-xxxxx-a/joeys_health

# Google Sheets Data Source
SHEET_ID=your_google_sheet_id_here
```

#### Optional Variables

```bash
# Active environment (defaults to 'production' if not set)
ACTIVE_ENV=production

# External PostgreSQL URL (for local development access)
PG_CONNECTION_URL_EXTERNAL=postgresql://admin:PASSWORD@dpg-xxxxx-a.virginia-postgres.render.com/joeys_health

# Individual PostgreSQL components (for reference, not used directly)
PG_HOST=dpg-xxxxx-a
PG_PORT=5432
PG_USER=admin
PG_PASSWORD=your_password
PG_DATABASE=joeys_health

# Migration flag (only set to True if migrating from existing SQLite data)
PG_INIT_MIGRATE_SQLITE=False

# Debug mode (leave False for production)
DEBUG=False
```

**Where to find your connection URLs:**
- Go to your PostgreSQL database in Render dashboard
- Scroll to "Connections" section
- Copy "Internal Database URL" for `PG_CONNECTION_URL_INTERNAL`
- Copy "External Database URL" for `PG_CONNECTION_URL_EXTERNAL`

### Step 4: Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Run the build command (`uv sync`)
   - Start the application with Gunicorn
3. Monitor the deployment logs for any errors

### Step 5: Initialize Database

After deployment succeeds, initialize the database:

**Option A: Via Web UI**
1. Open your deployed app URL
2. Click "Initialize Database" button
3. Wait for initialization to complete

**Option B: Via Render Shell**
1. In Render dashboard, go to your web service
2. Click "Shell" tab
3. Run: `uv run python -m lib.cli init`

**Option C: Via Migration (if you have existing SQLite data)**
1. Set `PG_INIT_MIGRATE_SQLITE=True` in environment variables
2. Click "Initialize Database" in the app
3. After migration completes, set `PG_INIT_MIGRATE_SQLITE=False`

### Step 6: Verify Deployment

1. Visit your app URL: `https://your-service-name.onrender.com`
2. Check that the dashboard loads
3. Verify "Last Updated" shows a timestamp
4. Check that charts display data

---

## Database Options

### PostgreSQL (Production - Render.com)

**Pros:**
- Persistent storage (survives deployments)
- No file system required
- Proper production database
- Free tier available

**Cons:**
- Requires setup and configuration
- Slightly more complex than SQLite

**Configuration:**
```bash
USE_SQLITE=False
PG_CONNECTION_URL_INTERNAL=postgresql://...
```

### SQLite (Local Development)

**Pros:**
- Simple, no setup required
- Fast for local testing
- File-based (easy to backup)

**Cons:**
- Cannot persist on Render.com (ephemeral filesystem)
- Not suitable for production deployment

**Configuration:**
```bash
USE_SQLITE=True
# No PostgreSQL variables needed
```

---

## Environment Variables Reference

### Core Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `USE_SQLITE` | No | `False` | Set to `True` to use SQLite, `False` for PostgreSQL |
| `ACTIVE_ENV` | No | `production` | Environment name: `local`, `production`, `staging`, `test` |
| `SHEET_ID` | Yes | - | Google Sheets ID for health data source |
| `DEBUG` | No | `False` | Enable debug mode (verbose logging) |

### PostgreSQL Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PG_CONNECTION_URL_INTERNAL` | Yes* | - | PostgreSQL URL for production/staging/test environments |
| `PG_CONNECTION_URL_EXTERNAL` | No | - | PostgreSQL URL for local/other environments |
| `PG_HOST` | No | - | PostgreSQL hostname (for reference only) |
| `PG_PORT` | No | `5432` | PostgreSQL port (for reference only) |
| `PG_USER` | No | - | PostgreSQL username (for reference only) |
| `PG_PASSWORD` | No | - | PostgreSQL password (for reference only) |
| `PG_DATABASE` | No | - | PostgreSQL database name (for reference only) |

\* Required when `USE_SQLITE=False` and `ACTIVE_ENV` is `production`, `staging`, or `test`

### Migration Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PG_INIT_MIGRATE_SQLITE` | No | `False` | Set to `True` to migrate existing SQLite data to PostgreSQL on initialization |

### Connection URL Selection Logic

The app automatically selects the correct PostgreSQL connection URL based on `ACTIVE_ENV`:

- `production`, `staging`, `test` → uses `PG_CONNECTION_URL_INTERNAL`
- `local`, or any other value → uses `PG_CONNECTION_URL_EXTERNAL`

**Why two URLs?**
- **Internal**: Used within Render.com infrastructure (faster, private network)
- **External**: Used from local machine or external services (public internet)

---

## Troubleshooting

### Database Connection Errors

**Error:** `ConnectionRefusedError` or `could not connect to server`

**Solution:**
1. Verify `PG_CONNECTION_URL_INTERNAL` is correct
2. Check that PostgreSQL instance is running in Render
3. Ensure `USE_SQLITE=False` is set

### Database Not Initialized

**Error:** Dashboard shows "Database not initialized"

**Solution:**
1. Click "Initialize Database" button in the app
2. Or run `uv run python -m lib.cli init` in Render shell

### Build Failures

**Error:** `ModuleNotFoundError: No module named 'psycopg2'`

**Solution:**
1. Ensure build command is: `uv sync --frozen && uv cache prune --ci`
2. Verify `psycopg2-binary` is in `pyproject.toml` dependencies

### Missing Environment Variables

**Error:** `ValueError: PG_CONNECTION_URL_INTERNAL is required`

**Solution:**
1. Go to Render dashboard → your service → Environment
2. Add missing `PG_CONNECTION_URL_INTERNAL` variable
3. Redeploy

---

## Maintenance

### Updating Data

The app automatically syncs data from Google Sheets when you click "Sync Database" button.

### Backups

**PostgreSQL on Render.com:**
- Free tier: No automatic backups
- Paid tier: Daily backups included
- Manual backup: Use `pg_dump` via Render shell

**Local SQLite:**
- Automatic temporary backups during sync
- Manual backup: Copy `db.db` file

### Monitoring

**Check Application Logs:**
1. Go to Render dashboard → your service
2. Click "Logs" tab
3. Monitor for errors or issues

**Check Database Status:**
1. In the app, view "Last Updated" timestamp
2. Or run: `uv run python -m lib.cli status`

---

## Cost Estimates

### Render.com Free Tier
- **Web Service**: Free (spins down after 15 min of inactivity)
- **PostgreSQL**: Free (256 MB RAM, 1 GB storage)
- **Total**: $0/month

### Render.com Paid Tier (Recommended for Always-On)
- **Web Service**: $7/month (Starter - always on, 512 MB RAM)
- **PostgreSQL**: $7/month (Starter - 1 GB RAM, 10 GB storage, daily backups)
- **Total**: $14/month

---

## Security Notes

1. **Never commit credentials** - `.env` files are gitignored
2. **Use environment variables** - All secrets should be in Render's environment config
3. **Connection URLs contain passwords** - Keep them secure
4. **HTTPS only** - Render provides free SSL certificates
5. **Private PostgreSQL** - Use internal URL in production for better security

---

## Additional Resources

- [Render.com Documentation](https://render.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

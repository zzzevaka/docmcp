# DocMCP - Railway Deployment Guide

This guide will walk you through deploying DocMCP to Railway in production mode.

## Quick Start (TL;DR)

For experienced users:

1. **Create Railway Project** → Add PostgreSQL database
2. **Create Backend Service**:
   - New → Empty Service → GitHub repo
   - Settings → Build → Dockerfile → Path: `deploy/Dockerfile.backend`
   - Add env vars: `APP_ENV=production`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
3. **Create Frontend Service**:
   - New → Empty Service → GitHub repo
   - Settings → Build → Dockerfile → Path: `deploy/Dockerfile.frontend`
   - Add env vars: `VITE_API_BASE_URL=<backend-url>/api`, `VITE_GOOGLE_CLIENT_ID`
4. **Update Google OAuth** with Railway URLs
5. **Deploy!**

> **Important**: This is a monorepo. You must manually create each service and specify the Dockerfile path. Auto-detection won't work.

## Architecture Overview

DocMCP consists of three main components:

- **Backend**: FastAPI application (Python 3.11)
- **Frontend**: React SPA with Vite (served via Nginx)
- **Database**: PostgreSQL 15

## Prerequisites

1. [Railway Account](https://railway.app/) (free tier available)
2. [Railway CLI](https://docs.railway.app/develop/cli) (optional, for local deployment)
3. Git repository with your code
4. Google OAuth credentials (for authentication)

## Deployment Steps

### Step 1: Create a New Railway Project

1. Go to [Railway](https://railway.app/)
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your DocMCP repository
5. Railway will automatically detect the project

### Step 2: Add PostgreSQL Database

1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will create and provision the database
4. The `DATABASE_URL` environment variable will be automatically created

### Step 3: Configure Backend Service

1. In your project, click "New" → "Empty Service"
2. Select "Deploy from GitHub repo"
3. Choose your repository
4. Configure the service:
   - **Service Name**: `backend`
   - **Root Directory**: Leave empty (project root)
   - Go to **Settings** → **Build**
   - Set **Builder**: `Dockerfile`
   - Set **Dockerfile Path**: `deploy/Dockerfile.backend`
   - Click "Save"

5. Add environment variables (Settings → Variables):
   ```
   APP_ENV=production
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```

   > Note: `DATABASE_URL` is automatically set by Railway when you link the database

5. Configure health check (Settings → Healthcheck):
   - **Path**: `/health`
   - **Timeout**: 10 seconds
   - **Interval**: 30 seconds

6. Click "Deploy"

### Step 4: Configure Frontend Service

1. In your project, click "New" → "Empty Service"
2. Select "Deploy from GitHub repo"
3. Choose your repository
4. Configure the service:
   - **Service Name**: `frontend`
   - **Root Directory**: Leave empty (project root)
   - Go to **Settings** → **Build**
   - Set **Builder**: `Dockerfile`
   - Set **Dockerfile Path**: `deploy/Dockerfile.frontend`
   - Click "Save"

5. Add environment variables (Settings → Variables):
   ```
   VITE_API_BASE_URL=https://your-backend-url.railway.app/api
   VITE_GOOGLE_CLIENT_ID=your-google-client-id
   ```

   > Important: Replace `your-backend-url.railway.app` with your actual backend URL from Step 3

5. Configure build arguments (Settings → Build):
   - Add the same environment variables as build args

6. Configure health check (Settings → Healthcheck):
   - **Path**: `/health`
   - **Timeout**: 10 seconds
   - **Interval**: 30 seconds

7. Click "Deploy"

### Step 5: Configure Google OAuth

You need to update your Google OAuth settings to allow Railway URLs:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" → "Credentials"
3. Select your OAuth 2.0 Client ID
4. Add authorized JavaScript origins:
   ```
   https://your-frontend-url.railway.app
   ```
5. Add authorized redirect URIs:
   ```
   https://your-frontend-url.railway.app
   https://your-frontend-url.railway.app/auth/callback
   ```
6. Save changes

### Step 6: Update Frontend Environment Variable

After getting the backend URL:

1. Go to Frontend service → Settings → Variables
2. Update `VITE_API_BASE_URL`:
   ```
   VITE_API_BASE_URL=https://your-backend-url.railway.app/api
   ```
3. Trigger a new deployment (Deployments → Redeploy)

### Step 7: Verify Deployment

1. Open your frontend URL (e.g., `https://your-frontend-url.railway.app`)
2. Try logging in with Google OAuth
3. Check that you can create and view documents
4. Verify the MCP integration works

## Environment Variables Reference

### Backend Service

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_ENV` | Application environment | `production` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | `123456789.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | `GOCSPX-xxxxx` |

### Frontend Service

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `https://backend.railway.app/api` |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth Client ID | `123456789.apps.googleusercontent.com` |

## Alternative Deployment: Using Railway CLI

For monorepo projects like DocMCP, you need to create services first and then deploy:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Create a new project
railway init

# Add PostgreSQL
railway add --database postgres

# For each service, you'll need to:
# 1. Create the service in Railway UI first
# 2. Link to it and deploy

# Example for backend:
railway link  # Select your project and backend service
railway up --dockerfile deploy/Dockerfile.backend

# For frontend (in a new terminal or after unlinking):
railway link  # Select your project and frontend service
railway up --dockerfile deploy/Dockerfile.frontend
```

Note: Railway CLI works best when you've already created services via the UI for monorepo projects.

## Troubleshooting

### "Railpack could not determine how to build the app"

This error occurs when Railway tries to auto-detect your project type. For monorepo projects:

**Solution 1: Use Railway UI (Recommended)**
1. Create services manually via Railway UI
2. Set **Builder** to `Dockerfile` in Settings → Build
3. Specify the correct **Dockerfile Path** for each service

**Solution 2: Deploy via CLI**
```bash
# Create service in UI first, then:
railway link  # Select your service
railway up --dockerfile deploy/Dockerfile.backend  # or frontend
```

**Why this happens:**
- DocMCP is a monorepo with multiple services
- Railway's auto-detection doesn't work with multiple Dockerfiles
- You need to explicitly tell Railway which Dockerfile to use for each service

### Database Connection Issues

If the backend can't connect to the database:

1. Verify `DATABASE_URL` is correctly set
2. Check that the database service is healthy
3. Look at backend logs: `railway logs --service backend`

### Frontend Can't Reach Backend

If API calls fail:

1. Verify `VITE_API_BASE_URL` points to the correct backend URL
2. Check CORS settings in the backend
3. Ensure both services are deployed and healthy

### Google OAuth Not Working

If OAuth fails:

1. Verify authorized origins and redirect URIs in Google Console
2. Check that `GOOGLE_CLIENT_ID` matches in both frontend and backend
3. Ensure URLs use HTTPS (Railway provides this automatically)

### Build Failures

If builds fail:

1. Check build logs in Railway dashboard
2. Verify Dockerfile paths are correct
3. Ensure all dependencies are listed in `package.json` or `pyproject.toml`

## Monitoring and Logs

Railway provides built-in monitoring:

- **Logs**: Click on a service → "Logs" tab
- **Metrics**: View CPU, Memory, and Network usage
- **Deployments**: Track deployment history and rollback if needed

## Database Migrations

Migrations run automatically when the backend starts (see `Dockerfile.backend`).

To run migrations manually:

```bash
# Using Railway CLI
railway run --service backend alembic upgrade head
```

## Scaling

Railway allows you to scale your services:

1. Go to Service → Settings
2. Adjust resources (RAM, CPU)
3. Enable autoscaling if needed

## Cost Optimization

Railway free tier includes:
- $5 free credit per month
- Shared CPU and RAM
- 100 GB bandwidth

For production:
- Upgrade to Pro plan ($20/month)
- Consider optimizing Docker images
- Use caching strategies

## Security Best Practices

1. **Never commit secrets**: Use Railway environment variables
2. **Use different OAuth credentials** for production
3. **Enable Railway's built-in DDoS protection**
4. **Regularly update dependencies**
5. **Monitor logs for suspicious activity**

## Backup and Recovery

Railway provides:
- Automatic daily database backups (Pro plan)
- Point-in-time recovery
- Manual backup via CLI:

```bash
railway run --service postgres pg_dump > backup.sql
```

## Next Steps

After deployment:

1. Set up custom domain (Railway Settings → Domains)
2. Configure SSL (automatic with Railway)
3. Set up monitoring and alerts
4. Configure backup strategy
5. Test MCP integration with Claude Desktop

## Support

- [Railway Documentation](https://docs.railway.app/)
- [DocMCP GitHub Issues](https://github.com/yourusername/docmcp/issues)
- [Railway Discord](https://discord.gg/railway)

## Files in This Directory

- `Dockerfile.backend` - Production Dockerfile for FastAPI backend
- `Dockerfile.frontend` - Production Dockerfile for React frontend with Nginx
- `nginx.frontend.conf` - Nginx configuration for serving static frontend
- `railway.toml` - Railway service configuration (copy to project root)
- `railway.json` - Railway build configuration
- `docker-compose.prod.yml` - Local production testing setup
- `.dockerignore` - Optimize Docker build context
- `README.md` - This comprehensive deployment guide
- `RAILWAY_COMMANDS.md` - Railway CLI commands cheat sheet

## Additional Notes

### Using railway.toml (Optional)

The included `railway.toml` can automatically configure services. To use it:

1. Place it in your repository root (not in deploy/)
2. Commit and push
3. Railway will auto-detect and configure services

### Manual Docker Builds

To test the production builds locally:

```bash
# Build backend
docker build -f deploy/Dockerfile.backend -t docmcp-backend .

# Build frontend
docker build -f deploy/Dockerfile.frontend \
  --build-arg VITE_API_BASE_URL=/api \
  --build-arg VITE_GOOGLE_CLIENT_ID=your-client-id \
  -t docmcp-frontend .

# Run backend
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e GOOGLE_CLIENT_ID=... \
  -e GOOGLE_CLIENT_SECRET=... \
  docmcp-backend

# Run frontend
docker run -p 80:80 docmcp-frontend
```

### Environment-Specific Builds

For different environments (staging, production):

1. Create separate Railway projects
2. Use different environment variables
3. Deploy from different Git branches

---

**Happy Deploying! 🚀**

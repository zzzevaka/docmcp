# Railway Commands Cheat Sheet

Quick reference for deploying DocMCP to Railway.

## Initial Setup

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project (creates railway.json)
railway init
```

## Creating Services via UI

**Recommended approach for monorepo projects like DocMCP.**

### Backend Service

1. Railway Dashboard → New → Empty Service
2. Connect GitHub repository
3. Settings → Build:
   - Builder: `Dockerfile`
   - Dockerfile Path: `deploy/Dockerfile.backend`
4. Settings → Variables:
   ```
   APP_ENV=production
   GOOGLE_CLIENT_ID=<your-client-id>
   GOOGLE_CLIENT_SECRET=<your-secret>
   ```
5. Settings → Healthcheck:
   - Path: `/health`
   - Timeout: 10s
   - Interval: 30s

### Frontend Service

1. Railway Dashboard → New → Empty Service
2. Connect GitHub repository
3. Settings → Build:
   - Builder: `Dockerfile`
   - Dockerfile Path: `deploy/Dockerfile.frontend`
4. Settings → Variables:
   ```
   VITE_API_BASE_URL=https://<backend-url>.railway.app/api
   VITE_GOOGLE_CLIENT_ID=<your-client-id>
   ```
5. Settings → Healthcheck:
   - Path: `/health`
   - Timeout: 10s
   - Interval: 30s

### PostgreSQL Database

1. Railway Dashboard → New → Database → PostgreSQL
2. Done! `DATABASE_URL` automatically available to backend

## CLI Deployment (After UI Setup)

```bash
# Link to backend service
railway link
# Select: project > backend service

# Deploy backend
railway up --dockerfile deploy/Dockerfile.backend

# View logs
railway logs

# Open service URL
railway open
```

```bash
# Link to frontend service (in new terminal or after unlink)
railway link
# Select: project > frontend service

# Deploy frontend
railway up --dockerfile deploy/Dockerfile.frontend

# View logs
railway logs

# Open service URL
railway open
```

## Environment Variables

```bash
# List all variables
railway variables

# Set a variable
railway variables set APP_ENV=production

# Delete a variable
railway variables delete OLD_VAR

# View specific variable
railway variables get DATABASE_URL
```

## Logs and Monitoring

```bash
# View live logs
railway logs

# Follow logs
railway logs --follow

# Filter logs
railway logs --filter "error"

# View specific deployment logs
railway logs --deployment <deployment-id>
```

## Database Operations

```bash
# Connect to PostgreSQL
railway connect postgres

# Run migrations
railway run --service backend alembic upgrade head

# Create database backup
railway run --service postgres pg_dump > backup.sql

# Execute SQL
railway run --service postgres psql -c "SELECT * FROM users LIMIT 5;"
```

## Deployment Management

```bash
# List deployments
railway deployments

# Rollback to previous deployment
railway rollback

# View deployment status
railway status

# Redeploy current version
railway up
```

## Project Management

```bash
# List all projects
railway list

# Switch project
railway link

# Unlink current project
railway unlink

# View project info
railway project

# Delete project (careful!)
railway project delete
```

## Domain Configuration

```bash
# Add custom domain
railway domain add example.com

# List domains
railway domain list

# Remove domain
railway domain remove example.com
```

## Local Development with Railway

```bash
# Run command with Railway environment
railway run npm run dev

# Load Railway env vars into shell
railway run bash

# Pull environment variables to .env file
railway vars > .env
```

## Troubleshooting Commands

```bash
# Check service health
railway status

# View build logs
railway logs --deployment <deployment-id>

# SSH into running container (if available)
railway shell

# View all service info
railway service
```

## Multi-Service Deployment Script

Create a script `deploy-all.sh`:

```bash
#!/bin/bash

echo "Deploying DocMCP to Railway..."

# Deploy backend
echo "Deploying backend..."
railway link --project <project-id> --service backend
railway up --dockerfile deploy/Dockerfile.backend

# Deploy frontend
echo "Deploying frontend..."
railway link --project <project-id> --service frontend
railway up --dockerfile deploy/Dockerfile.frontend

echo "Deployment complete!"
echo "Check status:"
railway status
```

Make it executable:
```bash
chmod +x deploy-all.sh
./deploy-all.sh
```

## Common Issues

### "Railpack could not determine how to build"
- Use Railway UI to create services
- Set Builder to Dockerfile
- Specify Dockerfile path

### Build failing
```bash
# Check build logs
railway logs --deployment <deployment-id>

# Try local build
docker build -f deploy/Dockerfile.backend .
```

### Environment variables not updating
```bash
# Force redeploy
railway up

# Or trigger via UI
# Settings → Redeploy
```

### Can't connect to database
```bash
# Verify DATABASE_URL
railway variables get DATABASE_URL

# Test connection
railway run --service backend python -c "from app.database import engine; print(engine.url)"
```

## Useful Links

- [Railway Documentation](https://docs.railway.app/)
- [Railway CLI Reference](https://docs.railway.app/develop/cli)
- [Railway Templates](https://railway.app/templates)

---

For complete deployment guide, see [README.md](README.md).

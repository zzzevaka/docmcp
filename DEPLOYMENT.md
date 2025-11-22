# Deployment Guide

## Railway Deployment (Production)

For complete Railway deployment instructions, see **[deploy/README.md](deploy/README.md)**.

### Quick Deploy Steps:

1. **Prerequisites**:
   - Railway account
   - Google OAuth credentials
   - GitHub repository

2. **Create Services** in Railway UI:
   - PostgreSQL database
   - Backend service (Dockerfile: `deploy/Dockerfile.backend`)
   - Frontend service (Dockerfile: `deploy/Dockerfile.frontend`)

3. **Configure Environment Variables**:
   - Backend: `APP_ENV`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - Frontend: `VITE_API_BASE_URL`, `VITE_GOOGLE_CLIENT_ID`

4. **Deploy and Verify**

### Important Notes:

⚠️ **This is a monorepo project**. Railway's auto-detection won't work. You must:
- Create each service manually via Railway UI
- Set Builder to "Dockerfile" in Settings → Build
- Specify the correct Dockerfile path for each service

### Files for Production:

All production configuration is in the `deploy/` directory:
- `Dockerfile.backend` - Production backend container
- `Dockerfile.frontend` - Production frontend container with Nginx
- `nginx.frontend.conf` - Nginx configuration
- `railway.toml` - Railway configuration
- `docker-compose.prod.yml` - Local testing of prod builds
- `README.md` - **Detailed deployment guide**

### Local Development

For local development, use the standard docker-compose:

```bash
docker-compose up
```

Access at: http://localhost:9080

### Testing Production Builds Locally

```bash
cd deploy
docker-compose -f docker-compose.prod.yml up
```

Access at: http://localhost:8080

---

📚 **Full Documentation**: [deploy/README.md](deploy/README.md)

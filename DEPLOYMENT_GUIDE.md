# MozzieSpot AI - Cloud Deployment Guide

This guide walks you through deploying the MozzieSpot AI project to Render (Backend) and Vercel (Frontend).

## Prerequisites

- GitHub account with this repository pushed
- Render account (https://render.com)
- Vercel account (https://vercel.com)

## Step 1: Deploy Backend to Render

### 1.1 Create Render Account & Connect GitHub
1. Go to [Render](https://render.com) and create an account
2. Connect your GitHub account
3. Grant Render permission to access your repositories

### 1.2 Deploy Backend Service
1. Click **New +** → **Web Service**
2. Select your `mozziespot2-advanced` repository
3. Configure:
   - **Name**: `mozziespot-backend`
   - **Region**: Choose closest to your users
   - **Runtime**: Python
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -b 0.0.0.0:$PORT run:app`
   - **Plan**: Free (or paid for better uptime)

### 1.3 Set Environment Variables in Render
1. In the Web Service dashboard, go to **Environment** tab
2. Add all variables from `.env.example`:

```
FLASK_ENV=production
DATA_DIR=/app/sample-data
JWT_SECRET=[GENERATE A SECURE SECRET KEY]
TELEGRAM_BOT_TOKEN=[Your bot token or leave empty]
TELEGRAM_CHAT_ID=[Your chat ID or leave empty]
SMTP_HOST=[Your SMTP server]
SMTP_PORT=587
SMTP_USER=[Your email]
SMTP_PASSWORD=[Your app password]
ALERT_FROM_EMAIL=alerts@mozziespot.ai
GOOGLE_MAPS_API_KEY=[Your API key or leave empty]
COPERNICUS_STAC_URL=https://stac.dataspace.copernicus.eu/v1
AWS_SENTINEL_STAC_URL=https://earth-search.aws.element84.com/v1
MOZZIESPOT_REAL_DOWNLOAD=0
```

### 1.4 Get Your Backend URL
After deployment, note the URL:
```
https://mozziespot-backend.onrender.com
```

You'll need this for the frontend configuration.

---

## Step 2: Deploy Frontend to Vercel

### 2.1 Deploy to Vercel
1. Go to [Vercel](https://vercel.com)
2. Click **Add New** → **Project**
3. Select your `mozziespot2-advanced` repository
4. Configure:
   - **Project Name**: `mozziespot-frontend`
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

### 2.2 Set Environment Variables in Vercel
1. In project **Settings** → **Environment Variables**
2. Add:
```
VITE_API_BASE_URL=https://mozziespot-backend.onrender.com
```

### 2.3 Configure API Rewrites (Optional)
If you want `/api/*` requests to proxy to your backend:

In Vercel settings, you can add rewrites. Alternatively, update `src/lib/api.ts` to use the environment variable:

```typescript
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

---

## Step 3: Production Checklist

Before going to production:

- [ ] Replace default JWT secret with a secure random string
  ```bash
  openssl rand -hex 32
  ```
- [ ] Configure Telegram bot token and chat ID for alerts
- [ ] Set up SMTP credentials for email alerts
- [ ] Add Google Maps API key for location features
- [ ] Verify Sentinel-2 STAC connectivity (uses free public endpoints)
- [ ] Test deployment with sample data
- [ ] Monitor logs for errors

---

## Step 4: Monitor & Maintain

### Render Dashboard
- View logs: Dashboard → **Logs** tab
- Manual deploy: **Manual Deploy** → **Latest Commit**
- Check metrics: **Metrics** tab

### Vercel Dashboard
- View logs: **Deployments** → Click deployment → **Logs**
- Redeploy: Click deploy → **Redeploy**
- Monitor analytics: **Analytics** tab

---

## Troubleshooting

### Backend won't start on Render
- Check `run.py` exists in the `backend` directory
- Verify `gunicorn` is in `requirements.txt`
- Review logs in Render dashboard

### Frontend can't connect to backend
- Verify `VITE_API_BASE_URL` is set correctly in Vercel
- Check backend service is running on Render
- Verify CORS headers are enabled in FastAPI

### CORS errors
Add to `backend/app/api/routes.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-vercel-domain.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Rollback & Recovery

### Revert to Previous Version on Render
1. Go to **Deployments** in Render dashboard
2. Click on a previous deployment
3. Click **Redeploy**

### Revert to Previous Version on Vercel
1. Go to **Deployments** tab
2. Click on the deployment you want to restore
3. Click **Promote to Production**

---

## Local Testing Before Deployment

Test the production configuration locally:

```bash
# Backend
cd backend
pip install -r requirements.txt
gunicorn -b 0.0.0.0:8000 run:app

# Frontend (new terminal)
cd frontend
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

Visit `http://localhost:5173` and test the application.

---

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)

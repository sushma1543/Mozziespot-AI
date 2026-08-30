# MozzieSpot AI - Deployment Checklist

## Pre-Deployment Steps (Local)

- [ ] Push all changes to GitHub
- [ ] Test locally with `docker compose up --build`
- [ ] Verify all environment variables are set correctly
- [ ] Run backend tests: `python -m pytest backend/tests/`
- [ ] Build frontend successfully: `npm run build` in frontend directory

## Deploy Backend to Render

### Step 1: Render Setup
- [ ] Log in to [Render.com](https://render.com)
- [ ] Connect GitHub account (if not already connected)
- [ ] Go to **Dashboard** → **New +** → **Web Service**

### Step 2: Configure Service
- [ ] Select your `mozziespot2-advanced` repository
- [ ] Name: `mozziespot-backend`
- [ ] Root Directory: `backend`
- [ ] Runtime: Python
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `gunicorn -b 0.0.0.0:$PORT run:app`

### Step 3: Environment Variables
Copy all variables from `.env.example` to Render:

```
FLASK_ENV=production
JWT_SECRET=[generate with: openssl rand -hex 32]
TELEGRAM_BOT_TOKEN=[optional]
TELEGRAM_CHAT_ID=[optional]
SMTP_HOST=[optional]
SMTP_PORT=587
SMTP_USER=[optional]
SMTP_PASSWORD=[optional]
ALERT_FROM_EMAIL=alerts@mozziespot.ai
GOOGLE_MAPS_API_KEY=[optional]
COPERNICUS_STAC_URL=https://stac.dataspace.copernicus.eu/v1
AWS_SENTINEL_STAC_URL=https://earth-search.aws.element84.com/v1
MOZZIESPOT_REAL_DOWNLOAD=0
```

### Step 4: Deploy
- [ ] Click **Create Web Service**
- [ ] Wait for deployment to complete
- [ ] Note the backend URL: `https://mozziespot-backend.onrender.com`
- [ ] Test endpoint: `https://mozziespot-backend.onrender.com/api/status`

---

## Deploy Frontend to Vercel

### Step 1: Vercel Setup
- [ ] Log in to [Vercel.com](https://vercel.com)
- [ ] Connect GitHub account (if not already connected)
- [ ] Go to **Add New** → **Project**

### Step 2: Configure Project
- [ ] Select `mozziespot2-advanced` repository
- [ ] Project Name: `mozziespot-frontend`
- [ ] Framework Preset: **Vite**
- [ ] Root Directory: `frontend`
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `dist`
- [ ] **IMPORTANT**: Don't change Install Command

### Step 3: Environment Variables
- [ ] Add to **Settings** → **Environment Variables**:

```
VITE_API_BASE_URL=https://mozziespot-backend.onrender.com
```

### Step 4: Deploy
- [ ] Click **Deploy**
- [ ] Wait for deployment to complete
- [ ] Note the frontend URL: `https://mozziespot-frontend.vercel.app`
- [ ] Test the application

---

## Post-Deployment Verification

### Backend Health Check
```bash
curl https://mozziespot-backend.onrender.com/api/status
```

Expected response:
```json
{
  "status": "operational",
  "modules": [...]
}
```

### Frontend Access
- [ ] Open `https://mozziespot-frontend.vercel.app`
- [ ] Check browser console for errors
- [ ] Test State Risk view
- [ ] Test satellite search
- [ ] Test location geocoding

### Check Logs
**Render Backend:**
- Dashboard → Logs tab
- Look for startup errors
- Verify all imports work

**Vercel Frontend:**
- Dashboard → Deployments → Click deployment
- Check Build Logs and Runtime Logs
- Verify API calls succeed

---

## Troubleshooting

### Backend Won't Start
1. Check Render logs: **Dashboard** → **Logs**
2. Verify `gunicorn` is in `requirements.txt`
3. Ensure `run.py` imports are correct
4. Test locally: `pip install -r requirements.txt && gunicorn run:app`

### Frontend Can't Connect to Backend
1. Verify `VITE_API_BASE_URL` is set in Vercel
2. Check browser console for CORS errors
3. Test backend is running: `curl $BACKEND_URL/api/status`
4. If CORS errors, may need to update Flask CORS configuration

### Slow Startup on Render
- Free tier Render instances sleep after 15 minutes of inactivity
- First request after sleep takes 30+ seconds (normal)
- Upgrade to paid plan to prevent sleeping

### API Calls Fail with 404
- Verify backend URL format in `VITE_API_BASE_URL`
- Check API endpoints exist in `backend/app/api/routes.py`
- Ensure all routes are registered with `/api` prefix

---

## Redeployment

### After Code Changes

**Backend:**
1. Push to GitHub
2. Render → **Manual Deploy** → **Latest Commit** (or auto-deploys)

**Frontend:**
1. Push to GitHub
2. Vercel → **Deployments** → **Redeploy** or wait for auto-deployment

### Rollback to Previous Version

**Render:**
- Dashboard → Deployments tab → Click previous → Redeploy

**Vercel:**
- Deployments tab → Click previous → Promote to Production

---

## Production Checklist

### Security
- [ ] Changed default JWT_SECRET (generate: `openssl rand -hex 32`)
- [ ] All API keys are in environment variables (not in code)
- [ ] HTTPS is enabled (automatic on Render/Vercel)
- [ ] Flask CORS is configured for frontend domain only

### Performance
- [ ] Frontend uses production build (Vite build)
- [ ] Backend uses production WSGI (gunicorn)
- [ ] Caching headers configured if needed

### Monitoring
- [ ] Set up Render/Vercel alerts
- [ ] Monitor error logs regularly
- [ ] Test critical flows weekly

### Data
- [ ] Database backup strategy planned
- [ ] Satellite cache strategy configured
- [ ] Sample data loading works

---

## Support

For issues:
1. Check logs in Render and Vercel dashboards
2. Review DEPLOYMENT_GUIDE.md for detailed setup
3. Check GitHub issues for similar problems
4. Verify environment variables match `.env.example`

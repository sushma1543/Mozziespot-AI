# Deployment

## Docker

```bash
docker compose up --build
```

## Render Backend

1. Create a new Web Service.
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn -b 0.0.0.0:$PORT run:app`
5. Add environment variables from `.env.example`.

## Vercel Frontend

1. Import the repository.
2. Root directory: `frontend`
3. Build command: `npm run build`
4. Output directory: `dist`
5. Configure API rewrites to the deployed backend.

## Production Checklist

- Replace default JWT secret.
- Configure Telegram bot token and chat id.
- Configure SMTP credentials.
- Connect PostGIS database.
- Add trained model weights.
- Validate detections with local field survey data.


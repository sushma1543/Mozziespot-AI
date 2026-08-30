from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

from app import create_app


app = FastAPI(
    title="MozzieSpot AI Advanced API",
    version="2.0.0",
    description="FastAPI entrypoint for satellite mosquito-risk mapping, analytics, alerts, and exports.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/fastapi-health")
def fastapi_health():
    return {"status": "ok", "service": "mozziespot-ai-fastapi"}


app.mount("/", WSGIMiddleware(create_app()))

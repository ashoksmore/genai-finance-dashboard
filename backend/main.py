import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.models import init_db
from routes.explain import router as explain_router
from routes.kpis import router as kpis_router
from routes.upload import router as upload_router


def _cors_allow_origins() -> list[str]:
    """Comma-separated origins in CORS_ALLOW_ORIGINS, or sensible dev defaults."""
    raw = (os.getenv("CORS_ALLOW_ORIGINS") or "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


app = FastAPI(title="Finance Health Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(upload_router, prefix="/api")
app.include_router(kpis_router, prefix="/api")
app.include_router(explain_router, prefix="/api")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "finance-dashboard",
        "version": "1.0.0",
    }


@app.get("/")
def root():
    return {
        "message": "Finance Dashboard API - visit /docs for Swagger UI",
    }

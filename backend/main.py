"""
EnterpriseOps AI — FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database.postgres import create_tables
from backend.database.qdrant import ensure_collection_async
from backend.api import auth, documents, workflow, reports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Starting EnterpriseOps AI...")

    # Ensure directories exist
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    Path("credentials").mkdir(exist_ok=True)

    # Initialize database tables
    await create_tables()
    logger.info("✅ Database tables ready")

    # Initialize Qdrant collection
    try:
        await ensure_collection_async()
        logger.info("✅ Qdrant collection ready")
    except Exception as e:
        logger.warning(f"⚠️  Qdrant not available: {e} — vector search will be limited")

    yield

    logger.info("👋 Shutting down EnterpriseOps AI")


app = FastAPI(
    title="EnterpriseOps AI",
    description="Autonomous Multi-Agent Enterprise Operations Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(workflow.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "EnterpriseOps AI",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


# ── Static files (optional for production) ────────────────────────────────────
if Path("frontend/dist").exists():
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

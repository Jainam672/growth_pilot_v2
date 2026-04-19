from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import logging
import sys

load_dotenv()

# ─── Configure Logging ───────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('growthpilot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
logger.info("🚀 Initializing GrowthPilot Backend...")

from database import Base, engine
from routers import auth_routes, idea_routes, ai_routes, dashboard_routes, settings_routes, chat_routes
from auth import get_current_user
from schemas import UserOut
import models

# Create all database tables
logger.info("📊 Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to create database tables: {e}", exc_info=True)
    raise

app = FastAPI(
    title="GrowthPilot API",
    description="🚀 AI-Powered Business Mentor — FastAPI Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ────────────────────────────────────────────────────
logger.info("⚙️ Configuring CORS...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Lock this down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("✅ CORS middleware configured")

# ─── Routers ─────────────────────────────────────────────────
logger.info("🔌 Loading routers...")
app.include_router(auth_routes.router,      prefix="/auth",      tags=["🔐 Auth"])
app.include_router(idea_routes.router,      prefix="/idea",      tags=["💡 Ideas"])
app.include_router(ai_routes.router,        prefix="/ai",        tags=["🤖 AI Engine"])
app.include_router(dashboard_routes.router, prefix="/dashboard", tags=["📊 Dashboard"])
app.include_router(settings_routes.router,  prefix="/settings",  tags=["⚙️ Settings"])
app.include_router(chat_routes.router,      prefix="/chat",      tags=["💬 Chat"])
logger.info("✅ All routers loaded successfully")


# ─── Protected /me route ─────────────────────────────────────
@app.get("/me", response_model=UserOut, tags=["🔐 Auth"])
def get_me(current_user: models.User = Depends(get_current_user)):
    """Get logged-in user's profile."""
    logger.debug(f"User {current_user.id} fetched their profile")
    return current_user


@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    logger.info("🎉 GrowthPilot Backend started successfully!")
    logger.info("📖 API Docs available at: http://localhost:8000/docs")
    logger.info("🔒 Auth routes: /auth/register, /auth/login")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown event."""
    logger.info("🛑 GrowthPilot Backend shutting down...")


# ─── Health Check ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "status": "running",
        "app": "GrowthPilot API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

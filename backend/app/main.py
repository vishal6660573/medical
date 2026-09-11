from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logs import logger
from app.database.database import create_tables

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.patients import router as patients_router
from app.api.routes.chatbot_route import router as chatbot_router
from app.api.routes.admin import router as admin_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Smart Healthcare Platform — disease prediction, patient records, and medical chatbot",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logger.info("Starting Smart Healthcare Platform...")
    create_tables()
    logger.info("Database tables created/verified ✅")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(chatbot_router)
app.include_router(admin_router)

@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs"
    }

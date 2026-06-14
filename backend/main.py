"""
Enterprise AI Workflow Intelligence Platform
Main FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import init_db
from app.api.routes import (
    auth,
    documents,
    workflow,
    analytics,
    chat,
    users,
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    logger.info("Database initialized successfully")
    yield
    logger.info("Shutting down application")


def create_application() -> FastAPI:
    """Factory function to create the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        ## Enterprise AI Workflow Intelligence Platform

        An AI-powered enterprise automation system for:
        - **Document Processing** - Intelligent extraction from invoices, contracts, reports
        - **RAG Knowledge Assistant** - Context-aware Q&A from company documents
        - **Workflow Automation** - AI-driven approval & risk assessment
        - **Business Analytics** - Real-time enterprise dashboard
        - **Risk & Compliance** - Automated compliance scoring

        ### Authentication
        Use `/api/auth/login` to get a JWT token, then use `Bearer <token>` in the Authorization header.
        """,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # API Routes
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(users.router, prefix="/api/users", tags=["Users"])
    app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
    app.include_router(workflow.router, prefix="/api/workflow", tags=["Workflow"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
    app.include_router(chat.router, prefix="/api/chat", tags=["RAG Chat"])

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "application": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "operational",
            "docs": "/api/docs",
        }

    @app.get("/api/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "service": settings.APP_NAME,
        }

    return app


app = create_application()

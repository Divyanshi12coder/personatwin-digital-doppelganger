import logging

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DB
from app.core.config import get_settings
from app.services.ai import get_ai_service
from app.services.embeddings import get_embedder

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health(db: DB) -> dict[str, object]:
    settings = get_settings()
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except SQLAlchemyError as exc:
        logger.error("Health check database error: %s", exc)
        database = "unavailable"
    ai = get_ai_service()
    return {
        "status": "ok" if database == "ok" else "degraded",
        "database": database,
        "database_engine": "sqlite" if settings.is_sqlite else "postgresql+pgvector",
        "ai": {"mode": ai.mode, "provider": ai.provider.name, "model": ai.provider.model},
        "embeddings": get_embedder().name,
        "version": "1.0.0",
    }

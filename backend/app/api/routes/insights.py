from typing import Annotated, Any

from fastapi import APIRouter, Query

from app.api.deps import DB, CurrentUser
from app.services import insights as insights_service

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/overview")
def overview(user: CurrentUser, db: DB) -> dict[str, Any]:
    data = insights_service.overview(db, user)
    db.commit()
    return data


@router.get("/analytics")
def analytics(user: CurrentUser, db: DB, days: Annotated[int, Query(ge=7, le=365)] = 90) -> dict[str, Any]:
    return insights_service.analytics(db, user, days)

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.forecast import linear_forecast
from core.metrics import compute_kpis
from db.session import get_db

router = APIRouter()


@router.get("/kpis")
def get_kpis(
    period: str = Query(default="2025"),
    db: Session = Depends(get_db),
):
    kpis = compute_kpis(db)

    if not kpis:
        raise HTTPException(
            status_code=404,
            detail="No data found. Upload a CSV first.",
        )

    months_elapsed = len(kpis["monthly_trend"])
    months_remaining = max(1, 12 - months_elapsed)

    forecast = linear_forecast(kpis["monthly_trend"], months_remaining)

    return {
        "period": period,
        "kpis": kpis,
        "forecast": forecast,
        "generated_at": datetime.utcnow().isoformat(),
    }

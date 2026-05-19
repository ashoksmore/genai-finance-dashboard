from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.forecast import linear_forecast
from core.metrics import compute_kpis
from db.session import get_db

_backend = Path(__file__).resolve().parent.parent
load_dotenv(_backend / "db" / ".env")
load_dotenv(_backend / ".env")

router = APIRouter()


def _build_local_explanation(question: str, facts_json: dict) -> str:
    """Return a deterministic, local explanation with KPI facts only."""
    variance_pct = facts_json["variance_pct"]
    projected_eoy = facts_json["projected_eoy"]
    overrun = facts_json["forecast_overrun"]
    overruns = facts_json["overruns"][:3]
    overrun_names = ", ".join(
        f"{item['department']} ({item['variance_pct']}%)" for item in overruns
    ) or "none"

    recommendation = "maintain current controls"
    if variance_pct > 10 or overrun > 0:
        recommendation = "freeze discretionary spend and review top overrun departments"
    elif variance_pct > 3:
        recommendation = "tighten monthly budget variance reviews"

    prompt_hint = question.strip()
    return (
        f"You asked: {prompt_hint}. Current totals are budget {facts_json['total_budget']} and actual {facts_json['total_actual']}, "
        f"with variance {variance_pct}%. Projected year-end spend is {projected_eoy} and projected overrun is {overrun}. "
        f"Top overrun departments: {overrun_names}. Recommendation: {recommendation}."
    )


class ExplainRequest(BaseModel):
    question: str


@router.post("/explain")
def post_explain(
    request: ExplainRequest,
    db: Session = Depends(get_db),
):
    kpis = compute_kpis(db)

    if not kpis:
        raise HTTPException(
            status_code=503,
            detail="No data available. Upload a CSV first.",
        )

    months_elapsed = len(kpis["monthly_trend"])
    months_remaining = max(1, 12 - months_elapsed)
    forecast = linear_forecast(kpis["monthly_trend"], months_remaining)

    facts_json = {
        "total_budget": kpis["total_budget"],
        "total_actual": kpis["total_actual"],
        "variance_pct": kpis["variance_pct"],
        "forecast_overrun": forecast["forecast_overrun"] if forecast else 0,
        "projected_eoy": forecast["projected_eoy"] if forecast else 0,
        "dept_summary": kpis["dept_summary"],
        "overruns": kpis["overruns"],
        "monthly_trend": kpis["monthly_trend"],
    }

    return {
        "answer": _build_local_explanation(request.question, facts_json),
        "grounded_on": "deterministic_kpis_local",
        "facts_snapshot": facts_json,
        "mode": "local_offline",
    }

from collections import defaultdict
import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from sqlalchemy.orm import Session

from db.models import LedgerEntry


def compute_kpis(db: Session) -> dict:
    """All KPIs computed deterministically in Python.
    GenAI only receives the output of this function — never raw data."""

    rows = db.query(LedgerEntry).all()

    if not rows:
        return {}

    total_budget = sum(r.budget for r in rows)
    total_actual = sum(r.actual for r in rows)
    variance = total_actual - total_budget
    variance_pct = (
        round((variance / total_budget) * 100, 1) if total_budget > 0 else 0
    )

    dept_agg: dict[str, dict[str, float]] = defaultdict(
        lambda: {"budget": 0.0, "actual": 0.0}
    )
    for r in rows:
        dept_agg[r.department]["budget"] += r.budget
        dept_agg[r.department]["actual"] += r.actual

    dept_summary: list[dict] = []
    for dept, sums in sorted(dept_agg.items()):
        b = sums["budget"]
        a = sums["actual"]
        v = a - b
        vpct = round((v / b) * 100, 1) if b > 0 else 0.0
        if vpct > 10:
            status = "overrun"
        elif 5 < vpct <= 10:
            status = "watch"
        elif vpct < -5:
            status = "under"
        else:
            status = "on_track"
        dept_summary.append(
            {
                "department": dept,
                "budget": round(b, 2),
                "actual": round(a, 2),
                "variance": round(v, 2),
                "variance_pct": vpct,
                "status": status,
            }
        )

    period_agg: dict[str, dict[str, float]] = defaultdict(
        lambda: {"budget": 0.0, "actual": 0.0}
    )
    for r in rows:
        period_agg[r.period]["budget"] += r.budget
        period_agg[r.period]["actual"] += r.actual

    monthly_trend = [
        {
            "period": p,
            "budget": round(s["budget"], 2),
            "actual": round(s["actual"], 2),
        }
        for p, s in sorted(period_agg.items(), key=lambda x: x[0])
    ]

    overruns = [d for d in dept_summary if d["status"] == "overrun"]

    return {
        "total_budget": round(total_budget, 2),
        "total_actual": round(total_actual, 2),
        "variance": round(variance, 2),
        "variance_pct": variance_pct,
        "dept_summary": dept_summary,
        "monthly_trend": monthly_trend,
        "overruns": overruns,
    }


if __name__ == "__main__":
    class _MockQuery:
        def __init__(self, rows: list[LedgerEntry]) -> None:
            self._rows = rows

        def all(self) -> list[LedgerEntry]:
            return self._rows

    class _MockSession:
        def __init__(self, rows: list[LedgerEntry]) -> None:
            self._rows = rows

        def query(self, model):  # noqa: ANN001
            assert model is LedgerEntry
            return _MockQuery(self._rows)

    mock_rows = [
        LedgerEntry(
            period="2025-01",
            department="Engineering",
            category="Payroll",
            budget=100_000.0,
            actual=116_000.0,
        ),
        LedgerEntry(
            period="2025-01",
            department="Marketing",
            category="Ads",
            budget=50_000.0,
            actual=54_000.0,
        ),
        LedgerEntry(
            period="2025-02",
            department="Engineering",
            category="Cloud",
            budget=20_000.0,
            actual=19_000.0,
        ),
        LedgerEntry(
            period="2025-02",
            department="Sales",
            category="Travel",
            budget=30_000.0,
            actual=28_000.0,
        ),
    ]

    out = compute_kpis(_MockSession(mock_rows))
    import json

    print(json.dumps(out, indent=2))

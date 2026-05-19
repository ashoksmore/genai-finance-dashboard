def linear_forecast(trend: list[dict], months_remaining: int) -> dict:
    """Linear MVP forecast. Production replacement: Prophet or Azure ML."""

    if len(trend) < 2:
        return {}

    window = trend[-3:] if len(trend) >= 3 else trend
    avg_monthly_burn = sum(item["actual"] for item in window) / len(window)

    ytd_actual = sum(item["actual"] for item in trend)
    ytd_budget = sum(item["budget"] for item in trend)

    projected_eoy = ytd_actual + (avg_monthly_burn * months_remaining)
    full_year_budget = ytd_budget * (12 / len(trend))
    forecast_overrun = round(projected_eoy - full_year_budget)

    return {
        "avg_monthly_burn": round(avg_monthly_burn),
        "projected_eoy": round(projected_eoy),
        "full_year_budget": round(full_year_budget),
        "forecast_overrun": forecast_overrun,
        "months_remaining": months_remaining,
        "method": "linear_3month_avg",
    }


if __name__ == "__main__":
    import json

    sample_trend = [
        {"period": "2025-01", "budget": 100_000, "actual": 95_000},
        {"period": "2025-02", "budget": 105_000, "actual": 102_000},
        {"period": "2025-03", "budget": 110_000, "actual": 108_000},
        {"period": "2025-04", "budget": 108_000, "actual": 112_000},
        {"period": "2025-05", "budget": 112_000, "actual": 115_000},
    ]
    result = linear_forecast(sample_trend, months_remaining=7)
    print(json.dumps(result, indent=2))

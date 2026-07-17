"""
Lightweight autonomous monitor.

This runs independently of the chat agent: it inspects budget status and
raises alerts on its own, the way a background "watcher" agent would in a
larger system. Kept rule-based (no LLM call) so it's instant and free to run
on every dashboard refresh.
"""

from data_store import store


def generate_alerts(month: str | None = None):
    alerts = []
    for row in store.budget_status(month):
        pct = row["percent_used"]
        if pct >= 100:
            alerts.append({
                "severity": "high",
                "category": row["category"],
                "message": f"{row['category']} is over budget: ${row['spent']:.2f} spent of a ${row['limit']:.2f} limit.",
            })
        elif pct >= 80:
            alerts.append({
                "severity": "medium",
                "category": row["category"],
                "message": f"{row['category']} is at {pct:.0f}% of its ${row['limit']:.2f} budget.",
            })

    totals = store.totals(month)
    if totals["net"] < 0:
        alerts.append({
            "severity": "high",
            "category": "Cash Flow",
            "message": f"Spending exceeded income by ${abs(totals['net']):.2f} this period.",
        })

    return alerts

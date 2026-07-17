"""
Very small in-memory data layer.

In a real product this would be a database. For this base project we load a
CSV of sample transactions into memory once at startup and expose simple
functions to read/write it. Swap this module out for a real DB layer without
touching the agent or the API routes.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_transactions.csv"

# Default monthly budgets by category (editable at runtime via the API).
DEFAULT_BUDGETS = {
    "Groceries": 350.00,
    "Dining": 150.00,
    "Transport": 120.00,
    "Entertainment": 60.00,
    "Utilities": 250.00,
    "Shopping": 200.00,
    "Health": 100.00,
    "Housing": 1800.00,
}


class Store:
    def __init__(self):
        self.df = pd.read_csv(DATA_PATH, parse_dates=["date"])
        self.budgets = dict(DEFAULT_BUDGETS)
        self._next_id = len(self.df)

    # ---------- transactions ----------
    def all_transactions(self):
        df = self.df.sort_values("date", ascending=False).copy()
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        return df.to_dict(orient="records")

    def add_transaction(self, description: str, category: str, amount: float, type_: str = "debit", date: str | None = None):
        row = {
            "date": pd.to_datetime(date or datetime.utcnow().date()),
            "description": description,
            "category": category,
            "amount": float(amount),
            "type": type_,
        }
        self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)
        return row

    # ---------- analytics ----------
    def spending_by_category(self, month: str | None = None):
        df = self.df[self.df["type"] == "debit"].copy()
        if month:
            df = df[df["date"].dt.strftime("%Y-%m") == month]
        grouped = df.groupby("category")["amount"].sum().round(2).to_dict()
        return grouped

    def totals(self, month: str | None = None):
        df = self.df.copy()
        if month:
            df = df[df["date"].dt.strftime("%Y-%m") == month]
        income = df[df["type"] == "credit"]["amount"].sum()
        expenses = df[df["type"] == "debit"]["amount"].sum()
        return {
            "income": round(float(income), 2),
            "expenses": round(float(expenses), 2),
            "net": round(float(income - expenses), 2),
        }

    # ---------- budgets ----------
    def get_budgets(self):
        return dict(self.budgets)

    def set_budget(self, category: str, amount: float):
        self.budgets[category] = float(amount)
        return self.budgets

    def budget_status(self, month: str | None = None):
        spending = self.spending_by_category(month)
        status = []
        for category, limit in self.budgets.items():
            spent = round(float(spending.get(category, 0.0)), 2)
            status.append({
                "category": category,
                "limit": limit,
                "spent": spent,
                "remaining": round(limit - spent, 2),
                "percent_used": round((spent / limit) * 100, 1) if limit else 0,
            })
        return status


# Singleton store shared by the whole app (fine for a demo / base project).
store = Store()

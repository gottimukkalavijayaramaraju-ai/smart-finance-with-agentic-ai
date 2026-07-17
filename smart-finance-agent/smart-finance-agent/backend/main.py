import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from data_store import store
from alerts import generate_alerts
from agent import FinanceAgent

app = FastAPI(title="Smart Finance Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = None  # lazily created so the server can start even without an API key set


def get_agent() -> FinanceAgent:
    global agent
    if agent is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise HTTPException(
                status_code=500,
                detail="ANTHROPIC_API_KEY is not set. Add it to a .env file in backend/ (see .env.example).",
            )
        agent = FinanceAgent()
    return agent


# ---------- schemas ----------
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class BudgetRequest(BaseModel):
    category: str
    amount: float


# ---------- API routes ----------
@app.get("/api/transactions")
def get_transactions():
    return store.all_transactions()


@app.get("/api/summary")
def get_summary(month: str | None = None):
    return {
        "totals": store.totals(month),
        "by_category": store.spending_by_category(month),
    }


@app.get("/api/budgets")
def get_budgets(month: str | None = None):
    return store.budget_status(month)


@app.post("/api/budgets")
def set_budget(req: BudgetRequest):
    return store.set_budget(req.category, req.amount)


@app.get("/api/alerts")
def get_alerts(month: str | None = None):
    return generate_alerts(month)


@app.post("/api/chat")
def chat(req: ChatRequest):
    result = get_agent().chat(req.message, req.history)
    return result


# ---------- serve the simple frontend ----------
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

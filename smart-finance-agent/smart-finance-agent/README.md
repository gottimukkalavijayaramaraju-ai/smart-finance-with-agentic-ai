# Smart Finance Agent — Base Project

A minimal but complete starting point for an agentic personal-finance app.

- **Backend:** FastAPI + an agentic loop built on Claude's tool-use API.
  The agent doesn't just chat — it calls real tools against your data
  (get transactions, compute budget status, add a transaction, set a budget)
  and grounds its answers in the results.
- **Autonomous alerts:** a small rule-based monitor (`alerts.py`) flags
  categories that are over or near their budget, independent of the chat agent.
- **Data:** in-memory store seeded from `data/sample_transactions.csv`
  (swap for a real database later — the rest of the app doesn't need to change).
- **Frontend:** a single-page dashboard (spending summary, budget bars,
  alerts, transaction list) with a chat panel wired to the agent.

## Project structure

```
smart-finance-agent/
├── backend/
│   ├── main.py           FastAPI app & routes
│   ├── agent.py          The agentic loop (Claude + tools)
│   ├── tools.py          Tool schemas + implementations the agent can call
│   ├── alerts.py         Rule-based autonomous budget monitor
│   ├── data_store.py     In-memory data layer (pandas)
│   ├── requirements.txt
│   └── .env.example
├── data/
│   └── sample_transactions.csv
└── frontend/
    └── index.html        Dashboard + chat UI (no build step, plain JS)
```

## Setup

1. **Install dependencies**

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Add your API key**

   ```bash
   cp .env.example .env
   # then edit .env and paste your key:
   # ANTHROPIC_API_KEY=sk-ant-...
   ```

   Get a key from the [Claude Console](https://console.anthropic.com/).
   The dashboard (summary, budgets, alerts, transactions) works without a
   key — only the chat panel needs one, since it calls the Claude API.

3. **Run the server**

   ```bash
   python main.py
   ```

   Then open **http://localhost:8000** in your browser.

## How the agent works

`agent.py` implements a standard agentic loop:

1. The user's message is sent to Claude along with a list of tool schemas
   (`tools.py`) describing what the agent is allowed to do.
2. If Claude decides it needs data, it responds with one or more `tool_use`
   requests instead of a final answer.
3. The backend executes those tools against `data_store.py` and sends the
   results back to Claude.
4. This repeats (up to `MAX_AGENT_STEPS`) until Claude has enough
   information to give a final, grounded answer.

Try asking things like:

- "How much have I spent on dining this month?"
- "Am I over budget anywhere?"
- "Set my entertainment budget to $80."
- "Add a $40 dinner expense under Dining."
- "What's driving my spending up this month?"

## Extending this base project

- **Real database:** replace `data_store.py`'s pandas store with SQLAlchemy
  models — nothing in `tools.py`, `agent.py`, or `main.py` needs to change
  as long as the function signatures stay the same.
- **More tools:** add a function + schema entry in `tools.py` and the agent
  gains the capability automatically — no changes to the agent loop needed.
- **Scheduled monitoring:** call `alerts.generate_alerts()` on a cron job or
  background task and push notifications instead of only checking on page load.
- **Multi-agent:** split `tools.py` into domain-specific tool sets (budgeting,
  investing, bill tracking) and route requests to specialized agents.
- **Auth & real accounts:** connect a provider like Plaid instead of the CSV,
  keeping the same tool interface.

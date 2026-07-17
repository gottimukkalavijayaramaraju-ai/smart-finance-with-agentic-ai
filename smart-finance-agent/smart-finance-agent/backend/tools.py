"""
Tools the finance agent is allowed to call.

Each tool is described with a JSON schema (for Claude's tool-use API) and
implemented as a plain Python function against the in-memory data_store.
Add a new capability by: 1) writing the function, 2) adding its schema to
TOOL_SCHEMAS, 3) adding a branch in execute_tool.
"""

from data_store import store

TOOL_SCHEMAS = [
    {
        "name": "get_transactions",
        "description": "Get the list of recent transactions, optionally filtered by category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Optional category to filter by, e.g. 'Dining'."},
                "limit": {"type": "integer", "description": "Max number of transactions to return.", "default": 20},
            },
        },
    },
    {
        "name": "get_spending_summary",
        "description": "Get total income, total expenses, and net cash flow for a given month.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "Month in YYYY-MM format. Omit for all-time."},
            },
        },
    },
    {
        "name": "get_spending_by_category",
        "description": "Get total spending broken down by category for a given month.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "Month in YYYY-MM format. Omit for all-time."},
            },
        },
    },
    {
        "name": "get_budget_status",
        "description": "Get each budget category's limit, amount spent, remaining balance, and percent used.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "Month in YYYY-MM format. Omit for all-time."},
            },
        },
    },
    {
        "name": "set_budget",
        "description": "Create or update the monthly budget limit for a category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["category", "amount"],
        },
    },
    {
        "name": "add_transaction",
        "description": "Record a new transaction (expense or income).",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "category": {"type": "string"},
                "amount": {"type": "number"},
                "type": {"type": "string", "enum": ["debit", "credit"], "default": "debit"},
            },
            "required": ["description", "category", "amount"],
        },
    },
]


def execute_tool(name: str, tool_input: dict):
    if name == "get_transactions":
        txns = store.all_transactions()
        category = tool_input.get("category")
        if category:
            txns = [t for t in txns if t["category"].lower() == category.lower()]
        limit = tool_input.get("limit", 20)
        return txns[:limit]

    if name == "get_spending_summary":
        return store.totals(tool_input.get("month"))

    if name == "get_spending_by_category":
        return store.spending_by_category(tool_input.get("month"))

    if name == "get_budget_status":
        return store.budget_status(tool_input.get("month"))

    if name == "set_budget":
        return store.set_budget(tool_input["category"], tool_input["amount"])

    if name == "add_transaction":
        return store.add_transaction(
            description=tool_input["description"],
            category=tool_input["category"],
            amount=tool_input["amount"],
            type_=tool_input.get("type", "debit"),
        )

    raise ValueError(f"Unknown tool: {name}")

"""
The agent itself.

This is a small agentic loop: we hand Claude the user's message plus a set
of finance tools, let it call whichever tools it needs (possibly several,
possibly none), feed the results back, and repeat until it produces a final
text answer. This is the core "agentic AI" pattern -- the model decides what
actions to take, rather than us hardcoding the logic.
"""

import os
from anthropic import Anthropic
from tools import TOOL_SCHEMAS, execute_tool

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
MAX_AGENT_STEPS = 6

SYSTEM_PROMPT = """You are a helpful, precise personal finance assistant embedded in a
budgeting app. You can call tools to look up the user's real transactions, spending
summaries, and budget status, or to record a new transaction or budget.

Rules:
- Always call a tool to get real numbers before making claims about the user's finances.
  Never guess or invent amounts.
- When you set a budget or add a transaction, confirm what you did in plain language.
- Keep answers concise and concrete: use actual figures from the tools.
- If the user asks for advice, ground it in the numbers you retrieved (e.g. which
  category is over budget, trends across categories).
"""


class FinanceAgent:
    def __init__(self, api_key: str | None = None):
        # Falls back to ANTHROPIC_API_KEY env var if not passed explicitly.
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()

    def chat(self, user_message: str, history: list[dict] | None = None) -> dict:
        messages = list(history or [])
        messages.append({"role": "user", "content": user_message})

        tool_calls_made = []

        for _ in range(MAX_AGENT_STEPS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )

            if response.stop_reason != "tool_use":
                final_text = "".join(
                    block.text for block in response.content if block.type == "text"
                )
                messages.append({"role": "assistant", "content": response.content})
                return {
                    "reply": final_text,
                    "tool_calls": tool_calls_made,
                    "history": messages,
                }

            # Model wants to use one or more tools: execute each and report results back.
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                result = execute_tool(block.name, block.input)
                tool_calls_made.append({"tool": block.name, "input": block.input, "result": result})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })
            messages.append({"role": "user", "content": tool_results})

        return {
            "reply": "I wasn't able to finish that request in the allotted steps -- could you rephrase or narrow it down?",
            "tool_calls": tool_calls_made,
            "history": messages,
        }

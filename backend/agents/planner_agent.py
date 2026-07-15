"""
Planner Agent — Converts user prompt into a structured execution plan.
Uses LLM to decompose complex requests into ordered sub-tasks.
"""
import json
import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.state import AgentState, get_llm

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are an Enterprise Operations AI Planner.
Your job is to analyze a user's business request and break it down into a structured execution plan.

The available agents and their capabilities are:
1. knowledge_agent: Retrieve information from enterprise documents (policies, handbooks, reports)
2. sql_agent: Query and analyze business data from the PostgreSQL database
3. analytics_agent: Perform statistical analysis, compute KPIs, generate charts
4. report_agent: Generate professional executive reports in Markdown
5. email_agent: Send emails via Gmail with attachments
6. slack_agent: Send Slack notifications to channels
7. github_agent: Create GitHub issues or pull requests

Respond ONLY with valid JSON in this exact format:
{
  "analysis": "Brief description of what the user wants",
  "sub_tasks": [
    "Short description of task 1",
    "Short description of task 2"
  ],
  "agents_needed": ["knowledge_agent", "sql_agent", "analytics_agent", "report_agent", "email_agent", "slack_agent"],
  "priority": "high|medium|low",
  "requires_sql": true|false,
  "requires_rag": true|false,
  "requires_email": true|false,
  "requires_slack": true|false,
  "requires_github": true|false
}
"""


async def planner_agent(state: AgentState) -> Dict[str, Any]:
    """
    Planner Agent node — decomposes user prompt into an execution plan.
    """
    logger.info(f"[Planner] Processing task {state['task_id']}")

    llm = get_llm()
    prompt = state["prompt"]

    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=f"User request: {prompt}"),
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content.strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        plan = json.loads(content)
        logger.info(f"[Planner] Plan created: {plan.get('analysis', '')[:100]}")

        return {
            "plan": plan,
            "sub_tasks": plan.get("sub_tasks", []),
            "messages": [HumanMessage(content=f"Plan created: {plan.get('analysis', '')}")],
        }

    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"[Planner] Error: {e}")
        # Fallback plan
        fallback_plan = {
            "analysis": f"Processing request: {prompt[:100]}",
            "sub_tasks": [
                "Retrieve relevant enterprise documents",
                "Query business database if applicable",
                "Perform analytics",
                "Generate report",
                "Send notifications",
            ],
            "agents_needed": ["knowledge_agent", "sql_agent", "analytics_agent", "report_agent", "email_agent", "slack_agent"],
            "priority": "medium",
            "requires_sql": True,
            "requires_rag": True,
            "requires_email": True,
            "requires_slack": True,
            "requires_github": False,
        }
        return {
            "plan": fallback_plan,
            "sub_tasks": fallback_plan["sub_tasks"],
            "errors": [str(e)],
        }

"""
LangGraph StateGraph — wires all agents into the EnterpriseOps pipeline.

Flow:
  START → planner → knowledge → sql → analytics → report
        → human_approval (interrupt) → email → slack → github → END
"""
import asyncio
import json
import logging
import time
from typing import Any, Dict, Literal

import redis
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.agents.state import AgentState
from backend.agents.planner_agent import planner_agent
from backend.agents.knowledge_agent import knowledge_agent
from backend.agents.sql_agent import sql_agent
from backend.agents.analytics_agent import analytics_agent
from backend.agents.report_agent import report_agent
from backend.agents.email_agent import email_agent
from backend.agents.slack_agent import slack_agent
from backend.agents.github_agent import github_agent
from backend.config import settings

logger = logging.getLogger(__name__)


# ── Agent wrapper that publishes log events to Redis pub/sub ─────────────────

def make_logged_agent(agent_fn, agent_name: str):
    """Wraps an agent function to publish SSE-compatible log events to Redis."""

    async def logged_agent(state: AgentState) -> Dict[str, Any]:
        task_id = state["task_id"]
        channel = f"workflow:{task_id}"

        r = redis.Redis.from_url(settings.REDIS_URL)

        # Publish "running" event
        _publish(r, channel, {
            "type": "agent_start",
            "agent": agent_name,
            "status": "running",
            "message": f"{agent_name} started...",
            "timestamp": time.time(),
        })

        start_time = time.time()
        result = {}
        error = None

        try:
            result = await agent_fn(state)
            elapsed_ms = (time.time() - start_time) * 1000

            # Publish "success" event
            _publish(r, channel, {
                "type": "agent_complete",
                "agent": agent_name,
                "status": "success",
                "message": _extract_message(result, agent_name),
                "execution_time_ms": elapsed_ms,
                "timestamp": time.time(),
            })

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            error = str(e)
            logger.error(f"[{agent_name}] Unhandled error: {e}", exc_info=True)

            _publish(r, channel, {
                "type": "agent_error",
                "agent": agent_name,
                "status": "failed",
                "message": f"Error: {error}",
                "execution_time_ms": elapsed_ms,
                "timestamp": time.time(),
            })
            result = {"errors": [error]}

        finally:
            r.close()

        return result

    logged_agent.__name__ = agent_name
    return logged_agent


def _publish(r, channel: str, data: dict):
    try:
        r.publish(channel, json.dumps(data))
    except Exception as e:
        logger.warning(f"Redis publish failed: {e}")


def _extract_message(result: dict, agent_name: str) -> str:
    """Extract a human-readable message from agent result."""
    for key in ("email_message", "slack_message", "analytics_summary", "sql_summary"):
        if result.get(key):
            return str(result[key])[:200]
    msgs = result.get("messages", [])
    if msgs:
        return str(msgs[-1].content)[:200]
    return f"{agent_name} completed successfully."


# ── Human Approval Node ───────────────────────────────────────────────────────

async def human_approval_node(state: AgentState) -> Dict[str, Any]:
    """
    Interrupt point: waits for manager approval via Redis key.
    The workflow is paused here until /workflow/{id}/approve or /reject is called.
    """
    task_id = state["task_id"]
    channel = f"workflow:{task_id}"
    r = redis.Redis.from_url(settings.REDIS_URL)

    # Signal that approval is needed
    _publish(r, channel, {
        "type": "awaiting_approval",
        "agent": "Human Approval",
        "status": "paused",
        "message": "Workflow paused — awaiting manager approval to send email/Slack/GitHub.",
        "timestamp": time.time(),
    })

    logger.info(f"[HumanApproval] Task {task_id} is awaiting approval")

    # Poll for approval (max 24 hours = 86400s)
    max_wait = 86400
    poll_interval = 2
    elapsed = 0
    approval_key = f"approval:{task_id}"

    while elapsed < max_wait:
        decision = r.get(approval_key)
        if decision:
            decision = decision.decode()
            r.delete(approval_key)
            r.close()
            logger.info(f"[HumanApproval] Task {task_id}: {decision}")
            return {"approval_status": decision}
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    r.close()
    logger.warning(f"[HumanApproval] Task {task_id} timed out waiting for approval")
    return {"approval_status": "rejected"}


def route_after_approval(state: AgentState) -> Literal["email", "end_rejected"]:
    """Conditional edge: approved → email, rejected → end."""
    return "email" if state.get("approval_status") == "approved" else "end_rejected"


async def end_rejected_node(state: AgentState) -> Dict[str, Any]:
    """Terminal node for rejected workflows."""
    task_id = state["task_id"]
    r = redis.Redis.from_url(settings.REDIS_URL)
    _publish(r, f"workflow:{task_id}", {
        "type": "rejected",
        "agent": "System",
        "status": "failed",
        "message": "Workflow rejected by manager. Email/Slack/GitHub actions cancelled.",
        "timestamp": time.time(),
    })
    r.close()
    return {}


# ── Build the Graph ───────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Construct and compile the LangGraph multi-agent pipeline."""
    graph = StateGraph(AgentState)

    # Add nodes (wrapped for logging)
    graph.add_node("planner", make_logged_agent(planner_agent, "Planner"))
    graph.add_node("knowledge", make_logged_agent(knowledge_agent, "Knowledge"))
    graph.add_node("sql", make_logged_agent(sql_agent, "SQL"))
    graph.add_node("analytics", make_logged_agent(analytics_agent, "Analytics"))
    graph.add_node("report", make_logged_agent(report_agent, "Report"))
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("email", make_logged_agent(email_agent, "Email"))
    graph.add_node("slack", make_logged_agent(slack_agent, "Slack"))
    graph.add_node("github", make_logged_agent(github_agent, "GitHub"))
    graph.add_node("end_rejected", end_rejected_node)

    # Linear edges
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "knowledge")
    graph.add_edge("knowledge", "sql")
    graph.add_edge("sql", "analytics")
    graph.add_edge("analytics", "report")
    graph.add_edge("report", "human_approval")

    # Conditional routing after approval
    graph.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {"email": "email", "end_rejected": "end_rejected"},
    )

    graph.add_edge("email", "slack")
    graph.add_edge("slack", "github")
    graph.add_edge("github", END)
    graph.add_edge("end_rejected", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# Singleton compiled graph
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_pipeline(
    task_id: str,
    user_id: str,
    prompt: str,
) -> AgentState:
    """
    Execute the full multi-agent pipeline.
    Returns the final state after all agents complete.
    """
    graph = get_graph()

    initial_state: AgentState = {
        "task_id": task_id,
        "user_id": user_id,
        "prompt": prompt,
        "plan": None,
        "sub_tasks": None,
        "rag_context": None,
        "retrieved_chunks": None,
        "sql_query": None,
        "sql_results": None,
        "sql_summary": None,
        "kpis": None,
        "chart_paths": None,
        "analytics_summary": None,
        "report_markdown": None,
        "report_path": None,
        "email_sent": None,
        "email_message": None,
        "slack_sent": None,
        "slack_message": None,
        "github_issue_url": None,
        "approval_status": None,
        "errors": [],
        "messages": [],
    }

    config = {"configurable": {"thread_id": task_id}}

    final_state = await graph.ainvoke(initial_state, config=config)
    return final_state

"""
Slack Agent — Posts workflow completion notifications to Slack channels.
Operates in mock mode if SLACK_BOT_TOKEN is not configured.
"""
import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage

from backend.agents.state import AgentState
from backend.config import settings

logger = logging.getLogger(__name__)


async def slack_agent(state: AgentState) -> Dict[str, Any]:
    """Slack Agent node — sends workflow status notification."""
    task_id = state["task_id"]
    logger.info(f"[Slack] Processing task {task_id}")

    plan = state.get("plan", {})
    if not plan.get("requires_slack", True):
        return {"slack_sent": False, "slack_message": "Slack notification not required."}

    # Build rich Slack message
    message_blocks = _build_slack_blocks(state)
    channel = settings.SLACK_DEFAULT_CHANNEL

    if settings.mock_slack:
        logger.info(f"[Slack] MOCK MODE — Would post to {channel}")
        logger.info(f"[Slack] Message: {message_blocks[0].get('text', {}).get('text', '')[:200]}")
        return {
            "slack_sent": True,
            "slack_message": f"[MOCK] Slack notification drafted for {channel}",
            "messages": [HumanMessage(content=f"Slack notification sent (mock mode) to {channel}")],
        }

    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError

        client = WebClient(token=settings.SLACK_BOT_TOKEN)
        response = client.chat_postMessage(
            channel=channel,
            blocks=message_blocks,
            text=f"EnterpriseOps AI: Workflow {task_id[:8]} completed",
        )

        if response["ok"]:
            logger.info(f"[Slack] Message posted to {channel}")
            return {
                "slack_sent": True,
                "slack_message": f"Slack notification sent to {channel}",
                "messages": [HumanMessage(content=f"Slack notification sent to {channel}")],
            }
        else:
            raise Exception(f"Slack API error: {response.get('error')}")

    except Exception as e:
        logger.error(f"[Slack] Error: {e}")
        return {
            "slack_sent": False,
            "slack_message": f"Slack notification failed: {str(e)}",
            "errors": [str(e)],
        }


def _build_slack_blocks(state: AgentState) -> list:
    """Build Slack Block Kit formatted message."""
    kpis = state.get("kpis", {})
    analytics = state.get("analytics_summary", "")

    # KPI fields
    kpi_fields = []
    if "total_revenue" in kpis:
        kpi_fields.append({"type": "mrkdwn", "text": f"*Revenue*\n${kpis['total_revenue']:,.0f}"})
    if "yoy_revenue_growth_pct" in kpis:
        growth = kpis["yoy_revenue_growth_pct"]
        emoji = "📈" if growth >= 0 else "📉"
        kpi_fields.append({"type": "mrkdwn", "text": f"*YoY Growth*\n{emoji} {growth:+.1f}%"})
    if "profit_margin_pct" in kpis:
        kpi_fields.append({"type": "mrkdwn", "text": f"*Profit Margin*\n{kpis['profit_margin_pct']:.1f}%"})
    if "total_units_sold" in kpis:
        kpi_fields.append({"type": "mrkdwn", "text": f"*Units Sold*\n{kpis['total_units_sold']:,}"})

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🤖 EnterpriseOps AI — Workflow Complete", "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Request:* {state['prompt'][:200]}"},
        },
        {"type": "divider"},
    ]

    if kpi_fields:
        blocks.append({
            "type": "section",
            "fields": kpi_fields[:4],  # Slack allows max 10 fields per section
        })

    if analytics:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Analytics:* {analytics[:500]}"},
        })

    # Status fields
    status_fields = []
    if state.get("sql_results"):
        status_fields.append({"type": "mrkdwn", "text": f"✅ *SQL:* {len(state['sql_results'])} rows analyzed"})
    if state.get("rag_context") and "No relevant" not in state["rag_context"]:
        chunks = len(state.get("retrieved_chunks", []))
        status_fields.append({"type": "mrkdwn", "text": f"✅ *Knowledge:* {chunks} document chunks retrieved"})
    if state.get("report_path"):
        status_fields.append({"type": "mrkdwn", "text": "✅ *Report:* Executive report generated"})
    if state.get("email_sent"):
        status_fields.append({"type": "mrkdwn", "text": f"✅ *Email:* {state.get('email_message', 'Sent')}"})

    if status_fields:
        blocks.append({"type": "section", "fields": status_fields})

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"Task ID: `{state['task_id']}` | Powered by EnterpriseOps AI"}],
    })

    return blocks

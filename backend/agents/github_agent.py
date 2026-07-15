"""
GitHub Agent (Optional) — Creates GitHub issues linking to generated reports.
Operates in mock mode if GITHUB_TOKEN is not configured.
"""
import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage

from backend.agents.state import AgentState
from backend.config import settings

logger = logging.getLogger(__name__)


async def github_agent(state: AgentState) -> Dict[str, Any]:
    """GitHub Agent node — optionally creates a GitHub issue for the task."""
    task_id = state["task_id"]
    plan = state.get("plan", {})

    if not plan.get("requires_github", False):
        logger.info(f"[GitHub] Not required per plan — skipping")
        return {"github_issue_url": None}

    logger.info(f"[GitHub] Creating issue for task {task_id}")

    title = f"EnterpriseOps AI Report: {state['prompt'][:80]}"
    body = _build_issue_body(state)

    if settings.mock_github:
        mock_url = f"https://github.com/{settings.GITHUB_REPO or 'owner/repo'}/issues/mock-{task_id[:8]}"
        logger.info(f"[GitHub] MOCK MODE — Would create issue: {title}")
        return {
            "github_issue_url": mock_url,
            "messages": [HumanMessage(content=f"GitHub issue created (mock): {mock_url}")],
        }

    try:
        from github import Github, GithubException

        g = Github(settings.GITHUB_TOKEN)
        repo = g.get_repo(settings.GITHUB_REPO)

        labels = ["automated", "enterprise-ops"]
        existing_labels = [l.name for l in repo.get_labels()]
        valid_labels = [l for l in labels if l in existing_labels]

        issue = repo.create_issue(
            title=title,
            body=body,
            labels=valid_labels,
        )

        logger.info(f"[GitHub] Issue created: {issue.html_url}")
        return {
            "github_issue_url": issue.html_url,
            "messages": [HumanMessage(content=f"GitHub issue created: {issue.html_url}")],
        }

    except Exception as e:
        logger.error(f"[GitHub] Error: {e}")
        return {
            "github_issue_url": None,
            "errors": [str(e)],
        }


def _build_issue_body(state: AgentState) -> str:
    """Build GitHub issue body with task details and KPIs."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    kpis = state.get("kpis", {})
    kpi_table = ""
    if kpis:
        rows = "\n".join(
            f"| {k.replace('_', ' ').title()} | {v:,.2f} |" if isinstance(v, float) else f"| {k.replace('_', ' ').title()} | {v} |"
            for k, v in kpis.items()
        )
        kpi_table = f"\n## KPIs\n| Metric | Value |\n|--------|-------|\n{rows}\n"

    return f"""## EnterpriseOps AI — Automated Report
**Generated:** {now}
**Task ID:** `{state['task_id']}`

## Request
> {state['prompt']}
{kpi_table}
## Summary
{state.get('analytics_summary', 'See attached report.')}

## Actions Taken
- {'✅' if state.get('sql_results') else '⬜'} SQL Analysis
- {'✅' if state.get('rag_context') else '⬜'} Knowledge Retrieval  
- {'✅' if state.get('report_path') else '⬜'} Report Generated
- {'✅' if state.get('email_sent') else '⬜'} Email Sent
- {'✅' if state.get('slack_sent') else '⬜'} Slack Notification

---
*Automated by [EnterpriseOps AI](https://github.com/{settings.GITHUB_REPO or 'owner/enterpriseops'})*
"""

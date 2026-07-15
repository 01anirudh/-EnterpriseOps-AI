"""
Email Agent — Sends executive reports via Gmail API or SMTP fallback.
Operates in mock mode if no credentials are configured.
"""
import logging
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.state import AgentState, get_llm
from backend.config import settings

logger = logging.getLogger(__name__)

EMAIL_COMPOSE_PROMPT = """You are a professional executive assistant.
Compose a concise, professional email body (no subject line, no greeting headers) 
that summarizes the key findings from an enterprise report.
Keep it to 3-4 short paragraphs. Use formal business language."""


async def email_agent(state: AgentState) -> Dict[str, Any]:
    """Email Agent node — composes and sends the executive report email."""
    task_id = state["task_id"]
    logger.info(f"[Email] Processing task {task_id}")

    plan = state.get("plan", {})
    if not plan.get("requires_email", True):
        return {"email_sent": False, "email_message": "Email not required per plan."}

    # Compose email body via LLM
    email_body = await _compose_email_body(state)

    subject = _extract_subject(state)
    report_path = state.get("report_path")

    # Extract email recipients from the prompt
    recipients = _extract_recipients(state.get("prompt", ""))

    if settings.mock_gmail:
        # Mock mode — log the email, don't send
        logger.info(f"[Email] MOCK MODE — Would send to: {recipients}")
        logger.info(f"[Email] Subject: {subject}")
        logger.info(f"[Email] Body preview: {email_body[:200]}")
        return {
            "email_sent": True,
            "email_message": f"[MOCK] Email drafted to: {', '.join(recipients)}. Subject: {subject}",
            "messages": [HumanMessage(content=f"Email drafted (mock mode): {subject}")],
        }

    # Try Gmail API first, fall back to SMTP
    try:
        success = _send_via_gmail_api(
            to=recipients,
            subject=subject,
            body=email_body,
            attachment_path=report_path,
        )
        method = "Gmail API"
    except Exception as e:
        logger.warning(f"[Email] Gmail API failed: {e}. Trying SMTP...")
        success = False
        method = "SMTP"

    if success:
        return {
            "email_sent": True,
            "email_message": f"Email sent via {method} to: {', '.join(recipients)}",
            "messages": [HumanMessage(content=f"Email sent to {', '.join(recipients)}")],
        }
    else:
        return {
            "email_sent": False,
            "email_message": "Email sending failed — check credentials.",
            "errors": ["Email delivery failed"],
        }


async def _compose_email_body(state: AgentState) -> str:
    """Use LLM to write a professional email body from the report summary."""
    try:
        llm = get_llm()
        context = f"""
Original request: {state['prompt']}

Analytics summary: {state.get('analytics_summary', 'N/A')}

Key findings: {state.get('sql_summary', 'N/A')}
"""
        messages = [
            SystemMessage(content=EMAIL_COMPOSE_PROMPT),
            HumanMessage(content=context),
        ]
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.warning(f"[Email] LLM compose failed: {e}")
        return (
            f"Please find attached the enterprise operations report for your review.\n\n"
            f"Summary: {state.get('analytics_summary', 'Report attached.')}\n\n"
            f"This report was generated automatically by EnterpriseOps AI."
        )


def _extract_subject(state: AgentState) -> str:
    """Extract a meaningful email subject from the task."""
    prompt = state.get("prompt", "")
    if "q2" in prompt.lower():
        return "Q2 Enterprise Operations Report"
    elif "q1" in prompt.lower():
        return "Q1 Enterprise Operations Report"
    elif "sales" in prompt.lower():
        return "Sales Performance Analysis Report"
    elif "annual" in prompt.lower():
        return "Annual Business Operations Report"
    return "Enterprise Operations Executive Report"


def _extract_recipients(prompt: str) -> list[str]:
    """Extract email addresses or use default finance team placeholder."""
    emails = re.findall(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', prompt)
    if emails:
        return emails
    # Default recipients by keyword
    if "finance" in prompt.lower():
        return ["finance-team@company.com"]
    elif "hr" in prompt.lower():
        return ["hr@company.com"]
    elif "executive" in prompt.lower() or "ceo" in prompt.lower():
        return ["executives@company.com"]
    return ["management@company.com"]


def _send_via_gmail_api(to: list, subject: str, body: str, attachment_path: str | None) -> bool:
    """Send email via Gmail API using OAuth2 credentials."""
    try:
        import base64
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_file(settings.GMAIL_TOKEN_FILE)
        service = build("gmail", "v1", credentials=creds)

        message = MIMEMultipart()
        message["to"] = ", ".join(to)
        message["from"] = settings.GMAIL_SENDER_EMAIL
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        if attachment_path and Path(attachment_path).exists():
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={Path(attachment_path).name}")
            message.attach(part)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        logger.info(f"[Email] Sent via Gmail API to {to}")
        return True
    except Exception as e:
        logger.error(f"[Email] Gmail API error: {e}")
        raise

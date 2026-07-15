"""
Report Agent — Generates professional executive reports using LLM.
Outputs Markdown and converts to PDF using ReportLab.
"""
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.state import AgentState, get_llm
from backend.config import settings

logger = logging.getLogger(__name__)

REPORT_SYSTEM_PROMPT = """You are a senior business analyst and report writer at a Fortune 500 company.
Generate a professional executive report in Markdown format.

Structure the report with:
1. Executive Summary (2-3 paragraphs)
2. Key Performance Indicators (bullet points with metrics)
3. Data Analysis Findings (detailed insights from SQL results)
4. Enterprise Policy Context (from RAG knowledge base)
5. Year-over-Year Comparison (if data available)
6. Recommendations (3-5 actionable items)
7. Conclusion

Formatting rules:
- Use ## for sections, ### for subsections
- Use **bold** for key metrics and important terms
- Include specific numbers and percentages from the data
- Keep a professional, data-driven tone
- Length: 600-1000 words
"""


async def report_agent(state: AgentState) -> Dict[str, Any]:
    """Report Agent node — generates executive Markdown report."""
    task_id = state["task_id"]
    logger.info(f"[Report] Generating report for task {task_id}")

    llm = get_llm()

    # Compile all context from upstream agents
    prompt_context = _build_report_context(state)

    messages = [
        SystemMessage(content=REPORT_SYSTEM_PROMPT),
        HumanMessage(content=prompt_context),
    ]

    try:
        start_time = time.time()
        response = await llm.ainvoke(messages)
        report_markdown = response.content
        gen_time = time.time() - start_time

        # Add report header
        header = _build_report_header(state)
        full_report = f"{header}\n\n{report_markdown}"

        # Save markdown file
        report_path = _save_report(task_id, full_report)

        # Convert to PDF
        _save_report_pdf(task_id, full_report, report_path)

        logger.info(f"[Report] Generated {len(full_report)} chars in {gen_time:.1f}s → {report_path}")

        return {
            "report_markdown": full_report,
            "report_path": str(report_path),
            "messages": [HumanMessage(content=f"Executive report generated ({len(full_report)} chars).")],
        }

    except Exception as e:
        logger.error(f"[Report] Error: {e}")
        # Generate a minimal fallback report
        fallback = _generate_fallback_report(state)
        report_path = _save_report(task_id, fallback)
        return {
            "report_markdown": fallback,
            "report_path": str(report_path),
            "errors": [str(e)],
        }


def _build_report_context(state: AgentState) -> str:
    """Compile all upstream agent outputs into a single context string for the LLM."""
    parts = [f"Generate an executive report for this business request:\n\n**{state['prompt']}**\n"]

    if state.get("analytics_summary"):
        parts.append(f"\n## Analytics Summary\n{state['analytics_summary']}")

    if state.get("kpis"):
        kpis = state["kpis"]
        kpi_lines = [f"- **{k.replace('_', ' ').title()}**: {v:,.2f}" if isinstance(v, float) else f"- **{k.replace('_', ' ').title()}**: {v}" for k, v in kpis.items()]
        parts.append(f"\n## KPI Data\n" + "\n".join(kpi_lines))

    if state.get("sql_summary"):
        parts.append(f"\n## SQL Query Results Summary\n{state['sql_summary']}")

    if state.get("sql_results"):
        # Include first 10 rows as sample
        import json
        sample = state["sql_results"][:10]
        parts.append(f"\n## Sample Data (first {len(sample)} rows)\n```json\n{json.dumps(sample, indent=2, default=str)}\n```")

    if state.get("rag_context"):
        parts.append(f"\n## Enterprise Knowledge Base Context\n{state['rag_context'][:2000]}")

    return "\n".join(parts)


def _build_report_header(state: AgentState) -> str:
    now = datetime.now().strftime("%B %d, %Y %H:%M UTC")
    return f"""# Enterprise Operations Report
**Generated:** {now}
**Task ID:** `{state['task_id']}`
**Request:** {state['prompt'][:200]}

---"""


def _save_report(task_id: str, content: str) -> Path:
    reports_dir = Path(settings.REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"report_{task_id}.md"
    path.write_text(content, encoding="utf-8")
    return path


def _save_report_pdf(task_id: str, markdown_content: str, md_path: Path):
    """Convert Markdown report to PDF using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_LEFT, TA_CENTER

        pdf_path = md_path.with_suffix(".pdf")
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle("Title", parent=styles["Title"],
                                     fontSize=18, textColor=colors.HexColor("#1e293b"),
                                     spaceAfter=12)
        h2_style = ParagraphStyle("H2", parent=styles["Heading2"],
                                  fontSize=13, textColor=colors.HexColor("#6366f1"),
                                  spaceBefore=16, spaceAfter=6)
        body_style = ParagraphStyle("Body", parent=styles["Normal"],
                                    fontSize=10, leading=16,
                                    textColor=colors.HexColor("#1e293b"))

        for line in markdown_content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# "):
                story.append(Paragraph(stripped[2:], title_style))
            elif stripped.startswith("## "):
                story.append(Spacer(1, 8))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
                story.append(Paragraph(stripped[3:], h2_style))
            elif stripped.startswith("### "):
                story.append(Paragraph(f"<b>{stripped[4:]}</b>", body_style))
            elif stripped.startswith("- ") or stripped.startswith("* "):
                story.append(Paragraph(f"&bull; {stripped[2:]}", body_style))
            elif stripped.startswith("**") and stripped.endswith("**"):
                story.append(Paragraph(f"<b>{stripped[2:-2]}</b>", body_style))
            elif stripped == "---":
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
            elif stripped:
                story.append(Paragraph(stripped, body_style))
            else:
                story.append(Spacer(1, 6))

        doc.build(story)
        logger.info(f"[Report] PDF saved: {pdf_path}")
    except Exception as e:
        logger.warning(f"[Report] PDF generation failed: {e}")


def _generate_fallback_report(state: AgentState) -> str:
    """Minimal report when LLM fails."""
    now = datetime.now().strftime("%B %d, %Y")
    return f"""# Enterprise Operations Report
**Date:** {now}
**Task:** {state['prompt'][:200]}

---

## Executive Summary
Analysis was completed based on available enterprise data.

## Analytics Results
{state.get('analytics_summary', 'No analytics data available.')}

## SQL Query Summary
{state.get('sql_summary', 'No database results available.')}

## Enterprise Knowledge
{(state.get('rag_context') or 'No documents retrieved.')[:500]}

---
*Report generated by EnterpriseOps AI*
"""

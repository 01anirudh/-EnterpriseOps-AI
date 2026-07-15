"""
Shared LangGraph state and LLM factory for the EnterpriseOps agent pipeline.
"""
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, TypedDict, Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from backend.config import settings

logger = logging.getLogger(__name__)


# ── LLM Factory ──────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.1):
    """Return the configured LLM (Gemini or OpenAI fallback)."""
    if settings.GOOGLE_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.info("Using Google Gemini LLM")
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature,
        )
    elif settings.OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        logger.info("Using OpenAI GPT-4o LLM")
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
        )
    else:
        logger.warning("No LLM API key configured — using mock LLM")
        return MockLLM()


class MockLLM:
    """Simple mock LLM for testing without API keys."""

    def invoke(self, messages):
        from langchain_core.messages import AIMessage
        return AIMessage(content="[MOCK] This is a simulated LLM response for development.")

    async def ainvoke(self, messages):
        from langchain_core.messages import AIMessage
        return AIMessage(content="[MOCK] This is a simulated LLM response for development.")


# ── LangGraph State ───────────────────────────────────────────────────────────

class AgentState(TypedDict):
    """Shared state passed between all agents in the LangGraph pipeline."""

    # Task metadata
    task_id: str
    user_id: str
    prompt: str

    # Planner output
    plan: Optional[Dict[str, Any]]
    sub_tasks: Optional[List[str]]

    # Knowledge Agent output
    rag_context: Optional[str]
    retrieved_chunks: Optional[List[Dict]]

    # SQL Agent output
    sql_query: Optional[str]
    sql_results: Optional[List[Dict]]
    sql_summary: Optional[str]

    # Analytics Agent output
    kpis: Optional[Dict[str, Any]]
    chart_paths: Optional[List[str]]
    analytics_summary: Optional[str]

    # Report Agent output
    report_markdown: Optional[str]
    report_path: Optional[str]

    # Communication outputs
    email_sent: Optional[bool]
    email_message: Optional[str]
    slack_sent: Optional[bool]
    slack_message: Optional[str]
    github_issue_url: Optional[str]

    # Control flow
    approval_status: Optional[str]  # None | "approved" | "rejected"
    errors: Optional[List[str]]

    # Message history (LangGraph built-in)
    messages: Annotated[List[BaseMessage], add_messages]

"""
Knowledge Agent — Retrieves relevant document chunks from the RAG pipeline.
Performs semantic search over Qdrant and enriches the pipeline context.
"""
import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage

from backend.agents.state import AgentState
from backend.rag.retriever import retrieve_relevant_chunks, build_rag_context

logger = logging.getLogger(__name__)


async def knowledge_agent(state: AgentState) -> Dict[str, Any]:
    """
    Knowledge Agent node — semantic document retrieval for enterprise RAG.
    """
    task_id = state["task_id"]
    user_id = state["user_id"]
    prompt = state["prompt"]

    logger.info(f"[Knowledge] Retrieving context for task {task_id}")

    # Build a refined retrieval query from both the prompt and planner output
    plan = state.get("plan", {})
    analysis = plan.get("analysis", prompt)
    query = f"{prompt}\n\n{analysis}"

    try:
        # Retrieve top-8 chunks
        chunks = await retrieve_relevant_chunks(
            query=query,
            user_id=user_id,
            top_k=8,
            min_score=0.2,
        )

        if not chunks:
            logger.info(f"[Knowledge] No relevant documents found for task {task_id}")
            rag_context = "No relevant enterprise documents found. Proceeding with available data."
            retrieved = []
        else:
            logger.info(f"[Knowledge] Found {len(chunks)} relevant chunks")
            rag_context = build_context_string(chunks)
            retrieved = [c.to_dict() for c in chunks]

        return {
            "rag_context": rag_context,
            "retrieved_chunks": retrieved,
            "messages": [
                HumanMessage(content=f"Knowledge retrieved: {len(chunks)} document chunks found.")
            ],
        }

    except Exception as e:
        logger.error(f"[Knowledge] Error: {e}")
        return {
            "rag_context": "Document retrieval temporarily unavailable.",
            "retrieved_chunks": [],
            "errors": [str(e)],
        }


def build_context_string(chunks) -> str:
    """Format retrieved chunks into a clean context block."""
    parts = []
    for i, chunk in enumerate(chunks):
        parts.append(
            f"[Document: {chunk.filename} | Relevance: {chunk.score:.2f}]\n{chunk.text}"
        )
    return "\n\n---\n\n".join(parts)

"""
SQL Agent — Generates and executes SQL queries against the PostgreSQL database.
Uses LLM to convert natural language to SQL, then executes and summarizes results.
"""
import json
import logging
import time
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import text, create_engine
from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.state import AgentState, get_llm
from backend.config import settings

logger = logging.getLogger(__name__)

SQL_SCHEMA = """
Available tables in the enterprise database:

1. sales (quarterly sales data)
   - id SERIAL PRIMARY KEY
   - year INTEGER (e.g., 2023, 2024)
   - quarter VARCHAR(4) (Q1, Q2, Q3, Q4)
   - region VARCHAR(100) (North, South, East, West, International)
   - product_category VARCHAR(100)
   - revenue DECIMAL(15,2)
   - units_sold INTEGER
   - cost DECIMAL(15,2)
   - profit DECIMAL(15,2)
   - sales_rep VARCHAR(100)
   - created_at TIMESTAMP

2. employees
   - id SERIAL PRIMARY KEY
   - name VARCHAR(255)
   - department VARCHAR(100)
   - role VARCHAR(100)
   - salary DECIMAL(10,2)
   - hire_date DATE
   - performance_score FLOAT (1.0-5.0)
   - is_active BOOLEAN

3. projects
   - id SERIAL PRIMARY KEY
   - name VARCHAR(255)
   - department VARCHAR(100)
   - budget DECIMAL(12,2)
   - spent DECIMAL(12,2)
   - status VARCHAR(50) (planning, active, completed, on_hold)
   - start_date DATE
   - end_date DATE
"""

SQL_SYSTEM_PROMPT = f"""You are an expert SQL analyst for an enterprise database.
Given a user request, generate a safe, read-only SQL query (SELECT only).

{SQL_SCHEMA}

Rules:
- Use only SELECT statements
- Always include a LIMIT (max 1000 rows)
- Use proper aggregation (GROUP BY, ORDER BY) for summary queries
- For year-over-year comparisons, join the same table with different year filters
- Return ONLY the SQL query, no explanation, no markdown fences

Example format:
SELECT year, quarter, SUM(revenue) as total_revenue FROM sales WHERE year IN (2023, 2024) GROUP BY year, quarter ORDER BY year, quarter;
"""


async def sql_agent(state: AgentState) -> Dict[str, Any]:
    """
    SQL Agent node — NL→SQL generation and execution.
    """
    task_id = state["task_id"]
    prompt = state["prompt"]
    plan = state.get("plan", {})

    logger.info(f"[SQL] Processing task {task_id}")

    # Check if SQL is needed per planner
    if not plan.get("requires_sql", True):
        logger.info("[SQL] SQL not required per plan — skipping")
        return {"sql_results": [], "sql_summary": "SQL analysis not required for this task."}

    llm = get_llm()

    messages = [
        SystemMessage(content=SQL_SYSTEM_PROMPT),
        HumanMessage(content=f"User request: {prompt}\n\nPlan analysis: {plan.get('analysis', '')}"),
    ]

    try:
        # Generate SQL
        response = await llm.ainvoke(messages)
        sql_query = response.content.strip()

        # Clean up any accidental markdown fences
        if "```" in sql_query:
            lines = sql_query.split("\n")
            sql_query = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            )
        sql_query = sql_query.strip()

        logger.info(f"[SQL] Generated query: {sql_query[:200]}")

        # Execute query
        start_time = time.time()
        results_df, error = _execute_query(sql_query)
        execution_time = (time.time() - start_time) * 1000

        if error:
            # Try a simpler fallback query
            logger.warning(f"[SQL] Query failed: {error}. Trying fallback.")
            fallback_sql = "SELECT year, quarter, region, SUM(revenue) as total_revenue, SUM(profit) as total_profit FROM sales GROUP BY year, quarter, region ORDER BY year, quarter LIMIT 100;"
            results_df, error2 = _execute_query(fallback_sql)
            sql_query = fallback_sql
            if error2:
                return {
                    "sql_query": sql_query,
                    "sql_results": [],
                    "sql_summary": f"Database query failed: {error}",
                    "errors": [error],
                }

        # Convert to records
        results_list = results_df.to_dict(orient="records")

        # Summarize results
        summary = _summarize_results(results_df, prompt)

        logger.info(f"[SQL] Returned {len(results_list)} rows in {execution_time:.0f}ms")

        return {
            "sql_query": sql_query,
            "sql_results": results_list,
            "sql_summary": summary,
            "messages": [HumanMessage(content=f"SQL executed: {len(results_list)} rows returned. {summary}")],
        }

    except Exception as e:
        logger.error(f"[SQL] Error: {e}")
        return {
            "sql_query": "",
            "sql_results": [],
            "sql_summary": f"SQL processing error: {str(e)}",
            "errors": [str(e)],
        }


def _execute_query(sql: str):
    """Execute a SELECT query using a sync SQLAlchemy engine. Returns (DataFrame, error)."""
    try:
        engine = create_engine(settings.DATABASE_SYNC_URL)
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), conn)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)


def _summarize_results(df: pd.DataFrame, prompt: str) -> str:
    """Generate a text summary of SQL results."""
    if df.empty:
        return "Query returned no results."

    lines = [f"Query returned {len(df)} rows with {len(df.columns)} columns."]

    # Numeric summary
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    for col in numeric_cols[:4]:
        total = df[col].sum()
        avg = df[col].mean()
        if total > 1000:
            lines.append(f"  • {col}: Total={total:,.2f}, Avg={avg:,.2f}")
        else:
            lines.append(f"  • {col}: Total={total:.2f}, Avg={avg:.2f}")

    return " ".join(lines)

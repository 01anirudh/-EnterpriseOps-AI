"""
Analytics Agent — Computes KPIs, performs trend analysis, generates charts.
Uses Pandas and Matplotlib on top of SQL Agent results.
"""
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from langchain_core.messages import HumanMessage

from backend.agents.state import AgentState
from backend.config import settings

logger = logging.getLogger(__name__)

# Apply a clean style
sns.set_theme(style="darkgrid", palette="husl")
plt.rcParams.update({
    "figure.facecolor": "#0f172a",
    "axes.facecolor": "#1e293b",
    "axes.edgecolor": "#334155",
    "axes.labelcolor": "#e2e8f0",
    "xtick.color": "#94a3b8",
    "ytick.color": "#94a3b8",
    "text.color": "#e2e8f0",
    "grid.color": "#334155",
    "figure.dpi": 120,
})


async def analytics_agent(state: AgentState) -> Dict[str, Any]:
    """Analytics Agent node — KPIs, trend analysis, and chart generation."""
    task_id = state["task_id"]
    sql_results = state.get("sql_results", [])

    logger.info(f"[Analytics] Processing task {task_id} with {len(sql_results)} SQL rows")

    if not sql_results:
        return {
            "kpis": {},
            "chart_paths": [],
            "analytics_summary": "No data available for analysis.",
            "messages": [HumanMessage(content="Analytics: No SQL data to analyze.")],
        }

    df = pd.DataFrame(sql_results)
    kpis = {}
    chart_paths = []
    chart_dir = Path(settings.REPORTS_DIR) / "charts" / task_id
    chart_dir.mkdir(parents=True, exist_ok=True)

    # ── Revenue KPIs ─────────────────────────────────────────────────────────
    if "revenue" in df.columns:
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
        df["profit"] = pd.to_numeric(df.get("profit", pd.Series()), errors="coerce")

        kpis["total_revenue"] = float(df["revenue"].sum())
        kpis["avg_revenue"] = float(df["revenue"].mean())
        kpis["max_revenue"] = float(df["revenue"].max())

        if "profit" in df.columns and df["profit"].notna().any():
            kpis["total_profit"] = float(df["profit"].sum())
            total_rev = df["revenue"].sum()
            kpis["profit_margin_pct"] = float(
                (df["profit"].sum() / total_rev * 100) if total_rev > 0 else 0
            )

        # ── YoY Analysis ─────────────────────────────────────────────────────
        if "year" in df.columns:
            years = sorted(df["year"].unique())
            if len(years) >= 2:
                current_year = years[-1]
                prev_year = years[-2]
                curr_rev = df[df["year"] == current_year]["revenue"].sum()
                prev_rev = df[df["year"] == prev_year]["revenue"].sum()
                if prev_rev > 0:
                    yoy_growth = ((curr_rev - prev_rev) / prev_rev) * 100
                    kpis["yoy_revenue_growth_pct"] = round(float(yoy_growth), 2)
                    kpis["current_year_revenue"] = float(curr_rev)
                    kpis["previous_year_revenue"] = float(prev_rev)

        # ── Chart 1: Revenue by Quarter/Year ─────────────────────────────────
        if "year" in df.columns and "quarter" in df.columns:
            pivot = df.groupby(["year", "quarter"])["revenue"].sum().reset_index()
            chart_path = _plot_revenue_by_quarter(pivot, chart_dir)
            if chart_path:
                chart_paths.append(str(chart_path))

        # ── Chart 2: Revenue by Region ────────────────────────────────────────
        if "region" in df.columns:
            region_df = df.groupby("region")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
            chart_path = _plot_region_bar(region_df, chart_dir)
            if chart_path:
                chart_paths.append(str(chart_path))

    # ── Unit Sales KPIs ───────────────────────────────────────────────────────
    if "units_sold" in df.columns:
        df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")
        kpis["total_units_sold"] = int(df["units_sold"].sum())

    # ── Build summary text ────────────────────────────────────────────────────
    summary = _build_analytics_summary(kpis)
    logger.info(f"[Analytics] KPIs computed: {list(kpis.keys())}, charts: {len(chart_paths)}")

    return {
        "kpis": kpis,
        "chart_paths": chart_paths,
        "analytics_summary": summary,
        "messages": [HumanMessage(content=f"Analytics complete. {summary}")],
    }


def _plot_revenue_by_quarter(df: pd.DataFrame, chart_dir: Path) -> str | None:
    try:
        fig, ax = plt.subplots(figsize=(10, 5))
        years = df["year"].unique()
        colors = ["#6366f1", "#f59e0b", "#10b981", "#ef4444"]

        for i, year in enumerate(sorted(years)):
            year_df = df[df["year"] == year]
            ax.plot(
                year_df["quarter"],
                year_df["revenue"] / 1e6,
                marker="o",
                linewidth=2.5,
                markersize=7,
                label=str(year),
                color=colors[i % len(colors)],
            )
            ax.fill_between(
                year_df["quarter"],
                year_df["revenue"] / 1e6,
                alpha=0.1,
                color=colors[i % len(colors)],
            )

        ax.set_title("Quarterly Revenue Comparison", fontsize=14, fontweight="bold", color="#f1f5f9")
        ax.set_xlabel("Quarter", fontsize=11)
        ax.set_ylabel("Revenue ($ Millions)", fontsize=11)
        ax.legend(title="Year", fontsize=10)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.1f}M"))
        plt.tight_layout()

        path = chart_dir / "quarterly_revenue.png"
        fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        return str(path)
    except Exception as e:
        logger.error(f"Chart error: {e}")
        return None


def _plot_region_bar(df: pd.DataFrame, chart_dir: Path) -> str | None:
    try:
        fig, ax = plt.subplots(figsize=(8, 5))
        colors = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"]
        bars = ax.barh(
            df["region"],
            df["revenue"] / 1e6,
            color=[colors[i % len(colors)] for i in range(len(df))],
            edgecolor="none",
        )
        for bar in bars:
            ax.text(
                bar.get_width() + 0.1,
                bar.get_y() + bar.get_height() / 2,
                f"${bar.get_width():.1f}M",
                va="center",
                fontsize=9,
                color="#94a3b8",
            )
        ax.set_title("Revenue by Region", fontsize=14, fontweight="bold", color="#f1f5f9")
        ax.set_xlabel("Revenue ($ Millions)", fontsize=11)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}M"))
        plt.tight_layout()

        path = chart_dir / "revenue_by_region.png"
        fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        return str(path)
    except Exception as e:
        logger.error(f"Chart error: {e}")
        return None


def _build_analytics_summary(kpis: Dict) -> str:
    parts = []
    if "total_revenue" in kpis:
        parts.append(f"Total Revenue: ${kpis['total_revenue']:,.0f}")
    if "yoy_revenue_growth_pct" in kpis:
        growth = kpis["yoy_revenue_growth_pct"]
        arrow = "▲" if growth >= 0 else "▼"
        parts.append(f"YoY Growth: {arrow} {abs(growth):.1f}%")
    if "profit_margin_pct" in kpis:
        parts.append(f"Profit Margin: {kpis['profit_margin_pct']:.1f}%")
    if "total_units_sold" in kpis:
        parts.append(f"Units Sold: {kpis['total_units_sold']:,}")
    return " | ".join(parts) if parts else "Analysis complete."

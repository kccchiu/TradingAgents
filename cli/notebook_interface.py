"""Notebook-friendly interface for running trading analysis.

This module provides functions and classes to run the TradingAgents analysis
within Jupyter notebooks or as Python functions, allowing programmatic control
over analyst selections, model options, and other analysis parameters.
"""

import datetime
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from enum import Enum
import time
from functools import wraps

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.layout import Layout
from rich.spinner import Spinner
from rich.table import Table
from rich import box
from rich.rule import Rule
from collections import deque

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from cli.models import AnalystType
from cli.stats_handler import StatsCallbackHandler

console = Console()


class AnalystSelection(Enum):
    """Available analyst options."""
    MARKET = "market"
    SOCIAL = "social"
    NEWS = "news"
    FUNDAMENTALS = "fundamentals"


class ResearchDepth(Enum):
    """Research depth levels."""
    SHALLOW = 1
    MEDIUM = 3
    DEEP = 5


class NotebookAnalysisConfig:
    """Configuration for notebook-based analysis."""
    
    def __init__(self,
        ticker: str,
        analysis_date: Optional[str] = None,
        selected_analysts: Optional[List[AnalystSelection]] = None,
        research_depth: ResearchDepth = ResearchDepth.MEDIUM,
        llm_provider: str = "openai",
        backend_url: str = "https://api.openai.com/v1",
        shallow_thinker: str = "gpt-4.1",
        deep_thinker: str = "gpt-5",
        google_thinking_level: Optional[str] = None,
        openai_reasoning_effort: Optional[str] = None,
    ):
        """Initialize analysis configuration.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'SPY')
            analysis_date: Date for analysis in YYYY-MM-DD format. Defaults to today.
            selected_analysts: List of analyst types to run. Defaults to all.
            research_depth: Depth of research (SHALLOW, MEDIUM, DEEP)
            llm_provider: LLM provider name (openai, google, anthropic, xai, openrouter, ollama)
            backend_url: Backend API URL for the LLM provider
            shallow_thinker: Model name for quick thinking
            deep_thinker: Model name for deep thinking
            google_thinking_level: For Google Gemini (high/minimal)
            openai_reasoning_effort: For OpenAI (high/medium/low)
        """
        self.ticker = ticker.upper()
        self.analysis_date = analysis_date or datetime.datetime.now().strftime("%Y-%m-%d")
        self.selected_analysts = selected_analysts or [
            AnalystSelection.MARKET,
            AnalystSelection.SOCIAL,
            AnalystSelection.NEWS,
            AnalystSelection.FUNDAMENTALS,
        ]
        self.research_depth = research_depth
        self.llm_provider = llm_provider.lower()
        self.backend_url = backend_url
        self.shallow_thinker = shallow_thinker
        self.deep_thinker = deep_thinker
        self.google_thinking_level = google_thinking_level
        self.openai_reasoning_effort = openai_reasoning_effort
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for graph processing."""
        return {
            "ticker": self.ticker,
            "analysis_date": self.analysis_date,
            "analysts": self.selected_analysts,
            "research_depth": self.research_depth.value,
            "llm_provider": self.llm_provider,
            "backend_url": self.backend_url,
            "shallow_thinker": self.shallow_thinker,
            "deep_thinker": self.deep_thinker,
            "google_thinking_level": self.google_thinking_level,
            "openai_reasoning_effort": self.openai_reasoning_effort,
        }


class NotebookMessageBuffer:
    """Message buffer optimized for notebook display."""
    
    ANALYST_MAPPING = {
        "market": "Market Analyst",
        "social": "Social Analyst",
        "news": "News Analyst",
        "fundamentals": "Fundamentals Analyst",
    }
    
    REPORT_SECTIONS = {
        "market_report": ("market", "Market Analyst"),
        "sentiment_report": ("social", "Social Analyst"),
        "news_report": ("news", "News Analyst"),
        "fundamentals_report": ("fundamentals", "Fundamentals Analyst"),
        "investment_plan": (None, "Research Manager"),
        "trader_investment_plan": (None, "Trader"),
        "final_trade_decision": (None, "Portfolio Manager"),
    }
    
    def __init__(self, max_length: int = 100):
        self.messages = deque(maxlen=max_length)
        self.tool_calls = deque(maxlen=max_length)
        self.agent_status = {}
        self.report_sections = {}
        self.selected_analysts = []
        self.final_report = None
        self._last_message_id = None
    
    def init_for_analysis(self, selected_analysts: List[str]):
        """Initialize for analysis with selected analysts."""
        self.selected_analysts = [a.lower() for a in selected_analysts]
        self.agent_status = {}
        self.report_sections = {}
        
        # Add selected analysts to status
        for analyst_key in self.selected_analysts:
            if analyst_key in self.ANALYST_MAPPING:
                self.agent_status[self.ANALYST_MAPPING[analyst_key]] = "pending"
        
        # Add fixed teams
        fixed_teams = {
            "Bull Researcher": "pending",
            "Bear Researcher": "pending",
            "Research Manager": "pending",
            "Trader": "pending",
            "Aggressive Analyst": "pending",
            "Neutral Analyst": "pending",
            "Conservative Analyst": "pending",
            "Portfolio Manager": "pending",
        }
        self.agent_status.update(fixed_teams)
        
        # Initialize report sections
        for section, (analyst_key, _) in self.REPORT_SECTIONS.items():
            if analyst_key is None or analyst_key in self.selected_analysts:
                self.report_sections[section] = None
        
        self.messages.clear()
        self.tool_calls.clear()
        self._last_message_id = None
        self.final_report = None
    
    def add_message(self, message_type: str, content: str):
        """Add a message to the buffer."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.messages.append((timestamp, message_type, content))
    
    def add_tool_call(self, tool_name: str, args: Dict):
        """Add a tool call to the buffer."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.tool_calls.append((timestamp, tool_name, args))
    
    def update_agent_status(self, agent: str, status: str):
        """Update agent status."""
        if agent in self.agent_status:
            self.agent_status[agent] = status
    
    def update_report_section(self, section_name: str, content: str):
        """Update a report section."""
        if section_name in self.report_sections:
            self.report_sections[section_name] = content
    
    def build_final_report(self):
        """Build the final consolidated report."""
        report_parts = []
        
        # Analyst Team Reports
        analyst_sections = ["market_report", "sentiment_report", "news_report", "fundamentals_report"]
        if any(self.report_sections.get(section) for section in analyst_sections):
            report_parts.append("## Analyst Team Reports")
            if self.report_sections.get("market_report"):
                report_parts.append(f"### Market Analysis\n{self.report_sections['market_report']}")
            if self.report_sections.get("sentiment_report"):
                report_parts.append(f"### Social Sentiment\n{self.report_sections['sentiment_report']}")
            if self.report_sections.get("news_report"):
                report_parts.append(f"### News Analysis\n{self.report_sections['news_report']}")
            if self.report_sections.get("fundamentals_report"):
                report_parts.append(f"### Fundamentals Analysis\n{self.report_sections['fundamentals_report']}")
        
        # Research Team Reports
        if self.report_sections.get("investment_plan"):
            report_parts.append("## Research Team Decision")
            report_parts.append(self.report_sections['investment_plan'])
        
        # Trading Team Reports
        if self.report_sections.get("trader_investment_plan"):
            report_parts.append("## Trading Team Plan")
            report_parts.append(self.report_sections['trader_investment_plan'])
        
        # Portfolio Management Decision
        if self.report_sections.get("final_trade_decision"):
            report_parts.append("## Portfolio Management Decision")
            report_parts.append(self.report_sections['final_trade_decision'])
        
        self.final_report = "\n\n".join(report_parts) if report_parts else None
        return self.final_report


def run_notebook_analysis(
    config: NotebookAnalysisConfig,
    show_progress: bool = True,
    save_report: bool = False,
    save_path: Optional[Path] = None,
) -> Tuple[Dict, Optional[str]]:
    """Run trading analysis from a notebook.
    
    Args:
        config: NotebookAnalysisConfig with analysis parameters
        show_progress: Whether to display live progress (requires terminal)
        save_report: Whether to save the report to disk
        save_path: Path to save report (uses default if not provided)
    
    Returns:
        Tuple of (final_state, final_report_text)
    """ 
    # Create config with selected research depth
    graph_config = DEFAULT_CONFIG.copy()
    graph_config["max_debate_rounds"] = config.research_depth.value
    graph_config["max_risk_discuss_rounds"] = config.research_depth.value
    graph_config["quick_think_llm"] = config.shallow_thinker
    graph_config["deep_think_llm"] = config.deep_thinker
    graph_config["backend_url"] = config.backend_url
    graph_config["llm_provider"] = config.llm_provider
    graph_config["google_thinking_level"] = config.google_thinking_level
    graph_config["openai_reasoning_effort"] = config.openai_reasoning_effort
    
    # Create stats callback handler
    stats_handler = StatsCallbackHandler()
    
    # Convert analyst selections to lowercase keys
    selected_analyst_keys = [a.value for a in config.selected_analysts]
    
    # Initialize the graph
    graph = TradingAgentsGraph(
        selected_analyst_keys,
        config=graph_config,
        debug=True,
        callbacks=[stats_handler],
    )
    
    # Initialize message buffer
    message_buffer = NotebookMessageBuffer()
    message_buffer.init_for_analysis(selected_analyst_keys)
    
    # Track start time
    start_time = time.time()
    
    console.print(Panel(
        f"[bold green]Starting Analysis[/bold green]\n"
        f"Ticker: {config.ticker}\n"
        f"Date: {config.analysis_date}\n"
        f"Analysts: {', '.join(a.value.title() for a in config.selected_analysts)}\n"
        f"Depth: {config.research_depth.name}",
        border_style="green",
        padding=(1, 2)
    ))
    
    # Initialize state and stream the analysis
    init_agent_state = graph.propagator.create_initial_state(
        config.ticker, config.analysis_date
    )
    args = graph.propagator.get_graph_args(callbacks=[stats_handler])
    
    trace = []
    stream_count = 0
    
    for chunk in graph.graph.stream(init_agent_state, **args):
        stream_count += 1
        
        # Update report sections from chunk
        for section_key in message_buffer.report_sections.keys():
            if section_key in chunk and chunk[section_key]:
                message_buffer.update_report_section(section_key, chunk[section_key])
        
        # Show progress if enabled
        if show_progress and stream_count % 5 == 0:
            elapsed = time.time() - start_time
            console.print(f"[dim]Progress: {stream_count} updates, {elapsed:.1f}s elapsed[/dim]")
        
        trace.append(chunk)
    
    # Get final state
    final_state = trace[-1] if trace else {}
    
    # Build final report
    message_buffer.build_final_report()
    
    # Calculate elapsed time
    elapsed = time.time() - start_time
    console.print(Panel(
        f"[bold green]Analysis Complete![/bold green]\n"
        f"Elapsed Time: {int(elapsed // 60):02d}:{int(elapsed % 60):02d}\n"
        f"Chunks Processed: {len(trace)}",
        border_style="green",
        padding=(1, 2)
    ))
    
    # Save report if requested
    report_file = None
    if save_report:
        report_file = _save_notebook_report(
            final_state,
            config.ticker,
            save_path or Path.cwd() / "notebook_reports"
        )
        console.print(f"[green]Report saved to: {report_file}[/green]")
    
    return final_state, message_buffer.final_report


def _save_notebook_report(
    final_state: Dict,
    ticker: str,
    save_path: Path
) -> Path:
    """Save analysis report to disk."""
    save_path.mkdir(parents=True, exist_ok=True)
    
    # Build sections
    sections = []
    
    # Analyst reports
    analysts_dir = save_path / "1_analysts"
    analyst_parts = []
    
    if final_state.get("market_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "market.md").write_text(final_state["market_report"])
        analyst_parts.append(("Market Analyst", final_state["market_report"]))
    
    if final_state.get("sentiment_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "sentiment.md").write_text(final_state["sentiment_report"])
        analyst_parts.append(("Social Analyst", final_state["sentiment_report"]))
    
    if final_state.get("news_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "news.md").write_text(final_state["news_report"])
        analyst_parts.append(("News Analyst", final_state["news_report"]))
    
    if final_state.get("fundamentals_report"):
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "fundamentals.md").write_text(final_state["fundamentals_report"])
        analyst_parts.append(("Fundamentals Analyst", final_state["fundamentals_report"]))
    
    if analyst_parts:
        content = "\n\n".join(f"### {name}\n{text}" for name, text in analyst_parts)
        sections.append(f"## I. Analyst Team Reports\n\n{content}")
    
    # Research team
    if final_state.get("investment_debate_state"):
        research_dir = save_path / "2_research"
        debate = final_state["investment_debate_state"]
        research_parts = []
        
        if debate.get("bull_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bull.md").write_text(debate["bull_history"])
            research_parts.append(("Bull Researcher", debate["bull_history"]))
        
        if debate.get("bear_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bear.md").write_text(debate["bear_history"])
            research_parts.append(("Bear Researcher", debate["bear_history"]))
        
        if debate.get("judge_decision"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "manager.md").write_text(debate["judge_decision"])
            research_parts.append(("Research Manager", debate["judge_decision"]))
        
        if research_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in research_parts)
            sections.append(f"## II. Research Team Decision\n\n{content}")
    
    # Trading team
    if final_state.get("trader_investment_plan"):
        trading_dir = save_path / "3_trading"
        trading_dir.mkdir(exist_ok=True)
        (trading_dir / "trader.md").write_text(final_state["trader_investment_plan"])
        sections.append(f"## III. Trading Team Plan\n\n### Trader\n{final_state['trader_investment_plan']}")
    
    # Risk management
    if final_state.get("risk_debate_state"):
        risk_dir = save_path / "4_risk"
        risk = final_state["risk_debate_state"]
        risk_parts = []
        
        if risk.get("aggressive_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "aggressive.md").write_text(risk["aggressive_history"])
            risk_parts.append(("Aggressive Analyst", risk["aggressive_history"]))
        
        if risk.get("conservative_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "conservative.md").write_text(risk["conservative_history"])
            risk_parts.append(("Conservative Analyst", risk["conservative_history"]))
        
        if risk.get("neutral_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "neutral.md").write_text(risk["neutral_history"])
            risk_parts.append(("Neutral Analyst", risk["neutral_history"]))
        
        if risk_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in risk_parts)
            sections.append(f"## IV. Risk Management Team Decision\n\n{content}")
        
        # Portfolio manager
        if risk.get("judge_decision"):
            portfolio_dir = save_path / "5_portfolio"
            portfolio_dir.mkdir(exist_ok=True)
            (portfolio_dir / "decision.md").write_text(risk["judge_decision"])
            sections.append(f"## V. Portfolio Manager Decision\n\n### Portfolio Manager\n{risk['judge_decision']}")
    
    # Write consolidated report
    header = f"# Trading Analysis Report: {ticker}\n\nGenerated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report_file = save_path / "complete_report.md"
    report_file.write_text(header + "\n\n".join(sections))
    
    return report_file


def display_notebook_report(final_state: Dict) -> None:
    """Display analysis report in notebook-friendly format."""
    console.print(Rule("Complete Analysis Report", style="bold green"))
    
    # Analyst Team Reports
    analysts = []
    if final_state.get("market_report"):
        analysts.append(("Market Analyst", final_state["market_report"]))
    if final_state.get("sentiment_report"):
        analysts.append(("Social Analyst", final_state["sentiment_report"]))
    if final_state.get("news_report"):
        analysts.append(("News Analyst", final_state["news_report"]))
    if final_state.get("fundamentals_report"):
        analysts.append(("Fundamentals Analyst", final_state["fundamentals_report"]))
    
    if analysts:
        console.print(Panel("[bold]I. Analyst Team Reports[/bold]", border_style="cyan"))
        for title, content in analysts:
            console.print(Panel(Markdown(content), title=title, border_style="blue", padding=(1, 2)))
    
    # Research Team Reports
    if final_state.get("investment_debate_state"):
        debate = final_state["investment_debate_state"]
        research = []
        if debate.get("bull_history"):
            research.append(("Bull Researcher", debate["bull_history"]))
        if debate.get("bear_history"):
            research.append(("Bear Researcher", debate["bear_history"]))
        if debate.get("judge_decision"):
            research.append(("Research Manager", debate["judge_decision"]))
        if research:
            console.print(Panel("[bold]II. Research Team Decision[/bold]", border_style="magenta"))
            for title, content in research:
                console.print(Panel(Markdown(content), title=title, border_style="blue", padding=(1, 2)))
    
    # Trading Team
    if final_state.get("trader_investment_plan"):
        console.print(Panel("[bold]III. Trading Team Plan[/bold]", border_style="yellow"))
        console.print(Panel(Markdown(final_state["trader_investment_plan"]), title="Trader", border_style="blue", padding=(1, 2)))
    
    # Risk Management Team
    if final_state.get("risk_debate_state"):
        risk = final_state["risk_debate_state"]
        risk_reports = []
        if risk.get("aggressive_history"):
            risk_reports.append(("Aggressive Analyst", risk["aggressive_history"]))
        if risk.get("conservative_history"):
            risk_reports.append(("Conservative Analyst", risk["conservative_history"]))
        if risk.get("neutral_history"):
            risk_reports.append(("Neutral Analyst", risk["neutral_history"]))
        if risk_reports:
            console.print(Panel("[bold]IV. Risk Management Team Decision[/bold]", border_style="red"))
            for title, content in risk_reports:
                console.print(Panel(Markdown(content), title=title, border_style="blue", padding=(1, 2)))
        
        # Portfolio Manager Decision
        if risk.get("judge_decision"):
            console.print(Panel("[bold]V. Portfolio Manager Decision[/bold]", border_style="green"))
            console.print(Panel(Markdown(risk["judge_decision"]), title="Portfolio Manager", border_style="blue", padding=(1, 2)))

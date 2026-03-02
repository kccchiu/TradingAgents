# Notebook Interface Documentation

## Overview

The Notebook Interface allows you to run TradingAgents analysis directly from Jupyter notebooks or as Python functions, without using the CLI. This is useful for:

- **Batch Processing**: Analyze multiple tickers programmatically
- **Custom Workflows**: Integrate analysis into larger data pipelines
- **Interactive Development**: Explore analysis results dynamically in notebooks
- **Automation**: Schedule regular analysis runs

## Quick Start

### Basic Usage

```python
from cli.notebook_interface import (
    NotebookAnalysisConfig,
    AnalystSelection,
    ResearchDepth,
    run_notebook_analysis,
    display_notebook_report,
)

# Create configuration
config = NotebookAnalysisConfig(
    ticker="AAPL",
    selected_analysts=[
        AnalystSelection.MARKET,
        AnalystSelection.NEWS,
        AnalystSelection.FUNDAMENTALS,
    ],
    research_depth=ResearchDepth.MEDIUM,
)

# Run analysis
final_state, report_text = run_notebook_analysis(config)

# Display results
display_notebook_report(final_state)
```

## Core Components

### 1. NotebookAnalysisConfig

Configuration class for the analysis.

**Parameters:**

- `ticker` (str): Stock ticker symbol (e.g., 'AAPL', 'SPY'). Required.
- `analysis_date` (str, optional): Date in YYYY-MM-DD format. Defaults to today.
- `selected_analysts` (List[AnalystSelection], optional): Analysts to use. Defaults to all.
- `research_depth` (ResearchDepth, optional): Analysis depth. Defaults to MEDIUM.
- `llm_provider` (str, optional): LLM service. Options: openai, google, anthropic, xai, openrouter, ollama. Defaults to "openai".
- `backend_url` (str, optional): API endpoint. Defaults to OpenAI's URL.
- `shallow_thinker` (str, optional): Fast thinking model. Defaults to "gpt-4.1".
- `deep_thinker` (str, optional): Deep reasoning model. Defaults to "gpt-5".
- `google_thinking_level` (str, optional): For Gemini only. Options: "high", "minimal".
- `openai_reasoning_effort` (str, optional): For OpenAI only. Options: "high", "medium", "low".

**Example:**

```python
config = NotebookAnalysisConfig(
    ticker="MSFT",
    analysis_date="2024-01-15",
    selected_analysts=[
        AnalystSelection.MARKET,
        AnalystSelection.FUNDAMENTALS,
    ],
    research_depth=ResearchDepth.DEEP,
    llm_provider="google",
    backend_url="https://generativelanguage.googleapis.com/v1",
    shallow_thinker="gemini-2.5-flash",
    deep_thinker="gemini-3-pro-preview",
    google_thinking_level="high",
)
```

### 2. AnalystSelection (Enum)

Available analyst teams:

- `MARKET`: Market trends, technical analysis, price movements
- `SOCIAL`: Social media sentiment, retail investor trends
- `NEWS`: News sentiment, press releases, market news
- `FUNDAMENTALS`: Company financials, earnings, growth metrics

**Example:**

```python
analysts = [
    AnalystSelection.MARKET,
    AnalystSelection.NEWS,
]
```

### 3. ResearchDepth (Enum)

Analysis thoroughness levels:

- `SHALLOW` (value: 1): Quick research, 1 debate round
- `MEDIUM` (value: 3): Balanced, 3 debate rounds (default)
- `DEEP` (value: 5): Comprehensive, 5 debate rounds

**Example:**

```python
depth = ResearchDepth.DEEP
```

### 4. run_notebook_analysis(config, show_progress, save_report, save_path)

Execute the analysis.

**Parameters:**

- `config` (NotebookAnalysisConfig): Analysis configuration. Required.
- `show_progress` (bool, optional): Display progress updates. Defaults to True.
- `save_report` (bool, optional): Save report to disk. Defaults to False.
- `save_path` (Path, optional): Where to save report. Defaults to "./notebook_reports".

**Returns:**

- `final_state` (Dict): Complete analysis results with keys:
  - `market_report`: Market analyst's analysis
  - `sentiment_report`: Social media analyst's analysis
  - `news_report`: News analyst's analysis
  - `fundamentals_report`: Fundamentals analyst's analysis
  - `investment_debate_state`: Research team debate and decision
  - `trader_investment_plan`: Trading team's plan
  - `risk_debate_state`: Risk management team debate
  - `final_trade_decision`: Portfolio manager's final decision

- `report_text` (str): Formatted markdown report

**Example:**

```python
final_state, report_text = run_notebook_analysis(
    config=config,
    show_progress=True,
    save_report=True,
    save_path=Path("./my_reports") / config.ticker
)
```

### 5. display_notebook_report(final_state)

Display formatted analysis report in the notebook.

**Parameters:**

- `final_state` (Dict): Results from `run_notebook_analysis()`. Required.

**Example:**

```python
display_notebook_report(final_state)
```

## Common Workflows

### Workflow 1: Single Stock Analysis

Analyze a single stock with all analysts:

```python
from cli.notebook_interface import *

config = NotebookAnalysisConfig(
    ticker="TSLA",
    selected_analysts=[
        AnalystSelection.MARKET,
        AnalystSelection.SOCIAL,
        AnalystSelection.NEWS,
        AnalystSelection.FUNDAMENTALS,
    ],
)

final_state, _ = run_notebook_analysis(config)
display_notebook_report(final_state)
```

### Workflow 2: Batch Analysis

Analyze multiple tickers with consistent settings:

```python
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
results = {}

for ticker in tickers:
    print(f"Analyzing {ticker}...")
    
    config = NotebookAnalysisConfig(
        ticker=ticker,
        selected_analysts=[AnalystSelection.MARKET, AnalystSelection.FUNDAMENTALS],
        research_depth=ResearchDepth.SHALLOW,
    )
    
    final_state, _ = run_notebook_analysis(config, show_progress=False)
    results[ticker] = final_state

print(f"✓ Completed {len(results)} analyses")
```

### Workflow 3: Comparative Analysis

Compare two stocks side-by-side:

```python
stocks = ["AAPL", "MSFT"]
comparisons = {}

for ticker in stocks:
    config = NotebookAnalysisConfig(ticker=ticker)
    final_state, _ = run_notebook_analysis(config)
    comparisons[ticker] = final_state

# Access specific reports
apple_market = comparisons["AAPL"]["market_report"]
microsoft_market = comparisons["MSFT"]["market_report"]

print("=== AAPL Market Analysis ===")
print(apple_market)
print("\n=== MSFT Market Analysis ===")
print(microsoft_market)
```

### Workflow 4: Different Models

Use different LLM providers:

```python
# OpenAI with reasoning
openai_config = NotebookAnalysisConfig(
    ticker="SPY",
    llm_provider="openai",
    shallow_thinker="gpt-4.1",
    deep_thinker="gpt-5",
    openai_reasoning_effort="high",
)

# Google Gemini
google_config = NotebookAnalysisConfig(
    ticker="SPY",
    llm_provider="google",
    backend_url="https://generativelanguage.googleapis.com/v1",
    shallow_thinker="gemini-2.5-flash",
    deep_thinker="gemini-3-pro-preview",
    google_thinking_level="high",
)

# Anthropic Claude
anthropic_config = NotebookAnalysisConfig(
    ticker="SPY",
    llm_provider="anthropic",
    backend_url="https://api.anthropic.com/",
    shallow_thinker="claude-sonnet-4-5",
    deep_thinker="claude-opus-4-5",
)
```

### Workflow 5: Access Individual Reports

Extract specific analysis sections:

```python
config = NotebookAnalysisConfig(ticker="AAPL")
final_state, _ = run_notebook_analysis(config)

# Market analysis only
market = final_state["market_report"]
print(market)

# Research team decision
research = final_state["investment_debate_state"]
print(f"Bull Researcher: {research['bull_history']}")
print(f"Bear Researcher: {research['bear_history']}")
print(f"Manager Decision: {research['judge_decision']}")

# Final decision
print(final_state["final_trade_decision"])
```

## LLM Provider Configuration

### OpenAI

```python
config = NotebookAnalysisConfig(
    ticker="AAPL",
    llm_provider="openai",
    backend_url="https://api.openai.com/v1",
    shallow_thinker="gpt-4.1",
    deep_thinker="gpt-5.2",
    openai_reasoning_effort="high",  # high, medium, low
)
```

### Google Gemini

```python
config = NotebookAnalysisConfig(
    ticker="AAPL",
    llm_provider="google",
    backend_url="https://generativelanguage.googleapis.com/v1",
    shallow_thinker="gemini-2.5-flash",
    deep_thinker="gemini-3-pro-preview",
    google_thinking_level="high",  # high, minimal
)
```

### Anthropic Claude

```python
config = NotebookAnalysisConfig(
    ticker="AAPL",
    llm_provider="anthropic",
    backend_url="https://api.anthropic.com/",
    shallow_thinker="claude-sonnet-4-5",
    deep_thinker="claude-opus-4-5",
)
```

### xAI Grok

```python
config = NotebookAnalysisConfig(
    ticker="AAPL",
    llm_provider="xai",
    backend_url="https://api.x.ai/v1",
    shallow_thinker="grok-4-fast-non-reasoning",
    deep_thinker="grok-4-fast-reasoning",
)
```

### OpenRouter

```python
config = NotebookAnalysisConfig(
    ticker="AAPL",
    llm_provider="openrouter",
    backend_url="https://openrouter.ai/api/v1",
    shallow_thinker="nvidia/nemotron-3-nano-30b-a3b:free",
    deep_thinker="z-ai/glm-4.5-air:free",
)
```

### Local Ollama

```python
config = NotebookAnalysisConfig(
    ticker="AAPL",
    llm_provider="ollama",
    backend_url="http://localhost:11434/v1",
    shallow_thinker="qwen3:latest",
    deep_thinker="glm-4.7-flash:latest",
)
```

## Save and Load Results

### Save Report to Disk

```python
final_state, _ = run_notebook_analysis(
    config,
    save_report=True,
    save_path=Path("./analysis_results") / config.ticker
)
```

This creates:
- `1_analysts/` - Individual analyst reports (market.md, sentiment.md, news.md, fundamentals.md)
- `2_research/` - Research team debate (bull.md, bear.md, manager.md)
- `3_trading/` - Trading plan (trader.md)
- `4_risk/` - Risk analysis (aggressive.md, conservative.md, neutral.md)
- `5_portfolio/` - Portfolio decision (decision.md)
- `complete_report.md` - Consolidated report

### Work with Saved Results

```python
from pathlib import Path
import json

# Results are saved in organized folders
report_dir = Path("./analysis_results/AAPL/2024-01-15")

# Read individual reports
market_report = (report_dir / "1_analysts" / "market.md").read_text()
research_decision = (report_dir / "2_research" / "manager.md").read_text()

# Read complete report
complete = (report_dir / "complete_report.md").read_text()
```

## Tips and Best Practices

1. **Start Shallow for Testing**: Use `ResearchDepth.SHALLOW` when testing configurations
2. **Batch Processing**: Set `show_progress=False` when running many analyses
3. **Environment Variables**: Ensure API keys are in `.env` file
4. **Error Handling**: Wrap analysis in try/except for production use
5. **Save Important Results**: Use `save_report=True` for analyses you want to keep
6. **Different Dates**: Analyze the same ticker on different dates to track changes

## Troubleshooting

**Issue**: "API key not found"
- Solution: Ensure your `.env` file has the correct API key for the LLM provider

**Issue**: "Model not available"
- Solution: Check that the model name is correct for the selected provider

**Issue**: "Notebook cells timeout"
- Solution: Use `ResearchDepth.SHALLOW` or reduce number of analysts

**Issue**: Rate limit errors
- Solution: Add delays between requests in batch processing

## Example Notebook

See `example_notebook_analysis.ipynb` for a complete working example with:
- Basic single stock analysis
- Batch processing multiple tickers
- Comparative analysis
- Different LLM providers
- Accessing individual report sections
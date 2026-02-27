# FRACTAL AI — MODERNIZATION BLUEPRINT

> **Version:** 1.0
> **Created:** 2026-02-26
> **Author:** Robin + Claude
> **Status:** DRAFT — Awaiting Review
> **Purpose:** Master architectural document for rebuilding Fractal AI into a robust, scalable, AI-assisted systematic trading platform

---

## 1. EXECUTIVE SUMMARY

### Why This Blueprint Exists

Fractal AI has grown from an experiment into a live trading system with three validated strategies (FTLR-v2, CISD-v3, S-SCALP-v3), two databases, automated N8N workflows, and a structured research framework. But it was built incrementally, without consistent standards, version control, or testing discipline. The system works — but it's fragile.

This blueprint defines the path from "working but fragile" to "robust, scalable, and professionally engineered." It captures every architectural decision, tool choice, design principle, and migration step needed to rebuild Fractal AI incrementally — without disrupting the live trading system.

### The Vision

A systematic trading platform where:

- Adding a new strategy is a configuration change, not a new project
- Adding a new asset pair requires zero code changes to the core engine
- Every piece of code is version controlled, tested, and documented
- AI agents (Claude Code) can contribute to development with full project context
- Research findings flow automatically into production rules through a validated pipeline
- The entire system can be rebuilt from a single Git repository

### Core Principles

1. **Incremental rebuild** — everything runs as-is while we migrate piece by piece
2. **Strategy as configuration** — trading logic is parameterized, not hardcoded
3. **Asset-agnostic architecture** — pair and timeframe are always parameters, never constants
4. **Test-driven development** — tests exist before code, not after
5. **Domain-driven design** — software structure mirrors the trading domain
6. **Human in the loop** — AI agents assist, humans approve
7. **Compound learning** — every output generates structured knowledge that improves future work
8. **Single source of truth** — one repo, one set of docs, one consistent language

---

## 2. CURRENT STATE ASSESSMENT

### What Exists Today

| Component | Technology | Location | State |
|-----------|-----------|----------|-------|
| Production DB | PostgreSQL (Supabase) | Fractal AI (eooqdkupnrgknstjvkwc) | ~36 MB, 3 active strategies |
| Research DB | PostgreSQL (Supabase) | The Beacon Robin (hdtpvlyofjevvoerculm) | ~364 MB, full 2025 dataset |
| Automation | N8N (self-hosted) | Hetzner VPS (€7.50/mo) | 4 workflows, 5-min cycles |
| Market Data | TwelveData API | Via N8N | Free tier (8 credits/min) |
| Alerting | Discord webhooks | Via N8N | Trade signals + health checks |
| Research Partner | Claude (Anthropic) | Claude.ai project | Conversations + project knowledge |
| Charting | TradingView | Manual | Visual validation |
| Chart Viewer | Lovable (React + Supabase) | Web app | Basic viewing |

### Active Strategies

| Strategy | Version | Validation | Key Metric (2R WR) | Status |
|----------|---------|-----------|---------------------|--------|
| FTLR | v2.0 | IN_SAMPLE (2025) | 59.5% (n=74) | Monitoring, needs OOS |
| CISD | v3.0 | OUT_OF_SAMPLE (2025) | 68.1% (n=144) | Deployed, forward testing |
| S-SCALP | v3.0 | OUT_OF_SAMPLE (2025-2026) | 68.8% (n=27 OOS) | Deployed, forward testing |

### Honest Problems

**No version control.** SQL functions are written directly in Supabase. There's no history, no diff, no rollback. The January 23 swing detection bug took significant debugging because we couldn't compare "before" and "after."

**No testing discipline.** Functions are tested manually once and deployed. There's no regression suite. Changes to one function can silently break others.

**Documentation drift.** FA_STATE.md, strategy playbooks, table schemas, and the actual database frequently disagree. There's no automated sync.

**Inconsistent naming.** "sweep" vs "breach," "C2_CLOSURE" vs "c2_close," function naming varies across production and research databases.

**Hardcoded assumptions.** Many SQL functions assume EURUSD, 1H timeframe, or specific session times. Adding GBPUSD or changing timeframes requires modifying core logic.

**No separation of concerns.** N8N workflows contain business logic (tolerance values, filter thresholds) that should live in configuration. Strategy rules are embedded in SQL functions rather than declarative configuration.

**Fragile deployment.** Deploying a change means pasting SQL into Supabase. There's no staging environment, no automated validation, no rollback procedure.

**Session-dependent context.** Each Claude conversation starts with context reconstruction. There's no persistent, structured project context that an AI agent can read instantly.

**No data validation.** TwelveData data is trusted implicitly. Gaps, duplicates, or bad candles could corrupt analysis without detection.

**No observability.** When something goes wrong, debugging means manually inspecting N8N execution logs and Discord message history.

---

## 3. TARGET STATE ARCHITECTURE

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FRACTAL AI SYSTEM                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  DATA DOMAIN  │  │  STRUCTURE   │  │  STRATEGY DOMAIN  │   │
│  │              │  │  DOMAIN      │  │                   │   │
│  │  Market Data  │→│  Swings      │→│  FTLR Rules       │   │
│  │  Data Valid.  │  │  Levels      │  │  CISD Rules       │   │
│  │  OHLC Store   │  │  Patterns    │  │  SCALP Rules      │   │
│  │              │  │  Structure   │  │  Signal Engine     │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│          │                 │                  │               │
│          ▼                 ▼                  ▼               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              EVENT BUS (Domain Events)                 │   │
│  │  CandleClosed · SwingDetected · LevelCreated         │   │
│  │  PatternFormed · SignalGenerated · TradeOpened        │   │
│  └──────────────────────────────────────────────────────┘   │
│          │                 │                  │               │
│          ▼                 ▼                  ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  EXECUTION   │  │  RESEARCH    │  │  OBSERVABILITY    │   │
│  │  DOMAIN      │  │  DOMAIN      │  │  DOMAIN           │   │
│  │              │  │              │  │                   │   │
│  │  Trade Mgmt  │  │  Hypotheses  │  │  Logging          │   │
│  │  Risk Mgmt   │  │  Backtesting │  │  Metrics          │   │
│  │  Position Sz │  │  Validation  │  │  Health Checks    │   │
│  │  Broker API  │  │  Learning    │  │  Alerting         │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              INFRASTRUCTURE LAYER                     │   │
│  │  PostgreSQL (Supabase) · FastAPI · N8N · Discord     │   │
│  │  Git (GitHub) · Docker · CI/CD (GitHub Actions)      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Domain-Driven Design — Bounded Contexts

The system is organized into six bounded contexts (domains), each with clear responsibilities and interfaces.

#### Domain 1: Market Data

**Responsibility:** Ingest, validate, and store raw market data.

**Entities:** Candle, DataGap, DataSource
**Events emitted:** `CandleClosed`, `DataGapDetected`, `DataRefreshed`
**External dependencies:** TwelveData API (via anti-corruption layer)

Key principle: This domain owns the raw truth of "what happened in the market." No other domain writes to OHLC data. The anti-corruption layer translates TwelveData's format into our internal Candle model — if we switch providers, only this adapter changes.

#### Domain 2: Structure Detection

**Responsibility:** Detect market structure from raw price data.

**Entities:** Swing, KeyLevel, SessionLevel, ClosurePattern, FairValueGap, CISD Event
**Events emitted:** `SwingDetected`, `LevelCreated`, `LevelSwept`, `PatternFormed`, `CISDDetected`
**Consumes:** `CandleClosed` events

Key principle: Structure detection is purely analytical — it observes data and emits structural findings. It has no knowledge of strategies or trade management.

#### Domain 3: Strategy Logic

**Responsibility:** Evaluate whether detected structures constitute a tradeable signal.

**Entities:** Strategy (config), Signal, Filter, Score, RiskTier
**Events emitted:** `SignalGenerated`, `SignalRejected`
**Consumes:** `SwingDetected`, `LevelSwept`, `PatternFormed`, `CISDDetected`

Key principle: Strategies are configuration, not code. A Strategy entity defines which filters to apply, what scoring model to use, which timeframes and pairs to monitor, and what risk parameters to use. The strategy engine interprets this configuration — it doesn't contain FTLR-specific or CISD-specific hardcoded logic.

#### Domain 4: Trade Execution

**Responsibility:** Manage the lifecycle of trades from signal to close.

**Entities:** Trade, Position, Account, RiskBudget
**Events emitted:** `TradeOpened`, `TradeClosed`, `StopHit`, `TargetHit`, `TradeExpired`
**Consumes:** `SignalGenerated`

Key principle: This domain enforces risk management. It validates position sizing, checks portfolio exposure, manages stop losses and take profits, and ensures no single trade or correlated set of trades can exceed defined risk limits. When multiple strategies run on multiple pairs, this domain manages portfolio-level concerns: net exposure per pair, maximum concurrent trades, correlation between open positions, and total portfolio drawdown limits. Future expansion: broker API integration for automated execution.

#### Domain 5: Research

**Responsibility:** Hypothesis-driven investigation, backtesting, and knowledge management.

**Entities:** Hypothesis, Question, Finding, Conclusion, Rule, Validation
**Events emitted:** `FindingRecorded`, `HypothesisResolved`, `RuleCreated`, `ValidationCompleted`
**Consumes:** Historical data from Market Data domain

Key principle: Research operates on historical data snapshots, never on live production data. Research produces Rules that, after validation, can be promoted to Strategy configurations. The research knowledge chain (Hypothesis → Question → Finding → Conclusion → Rule → Strategy) is enforced.

#### Domain 6: Observability

**Responsibility:** Monitor system health, log events, collect metrics, alert on problems.

**Entities:** HealthCheck, Metric, Alert, AuditLog
**Events emitted:** `AlertTriggered`, `HealthCheckFailed`
**Consumes:** Events from all other domains

Key principle: Every significant system action is logged. Metrics are collected on pipeline latency, signal evaluation counts, data freshness, and strategy performance. Health checks run automatically. Alerts are actionable — they tell you what's wrong and suggest how to fix it.

### 3.3 Event-Driven Architecture

The target architecture uses domain events to decouple components. Instead of the current approach where N8N orchestrates a sequential pipeline (fetch data → detect swings → check signals → manage trades), each domain reacts to events independently.

**Current (tightly coupled):**
```
N8N Timer → fetch_candles() → detect_swings() → check_signal() → open_trade()
```

**Target (event-driven):**
```
CandleClosed → Structure Detection listens → emits SwingDetected
                                            → emits PatternFormed
SwingDetected → Strategy Engine listens → evaluates filters → emits SignalGenerated
SignalGenerated → Trade Execution listens → validates risk → emits TradeOpened
TradeOpened → Observability listens → logs + alerts
```

This means adding a new strategy doesn't require changing the data pipeline, the structure detection, or the trade management — it only requires a new strategy configuration that listens to existing events.

**Implementation approach:** For the initial migration, events can be implemented as simple function calls within a Python orchestrator (not full message queues). As the system scales, events can be promoted to a proper event bus (Redis Pub/Sub, or PostgreSQL LISTEN/NOTIFY).

### 3.4 Strategy as Configuration

Every strategy is defined declaratively, not procedurally:

```python
# Example: CISD v3 strategy configuration
{
    "id": "CISD-v3",
    "name": "CISD v3.0 C2-Close",
    "version": "3.0",
    "status": "ACTIVE",
    "pairs": ["EURUSD"],
    "timeframes": {
        "structure": "1H",
        "entry": "5M"
    },
    "trading_window": {
        "start_utc": "04:00",
        "end_utc": "19:00",
        "days": ["MON", "TUE", "WED", "THU", "FRI"]
    },
    "entry": {
        "type": "C2_CLOSE",
        "requires": ["CISD_DETECTED", "SERIES_GTE_2", "C2_ALIGNED", "C3_CONFIRMS"]
    },
    "filters": [
        {"name": "series_minimum", "param": 2, "type": "HARD"},
        {"name": "c2_body_aligned", "type": "HARD"},
        {"name": "c3_first_5m_confirms", "type": "HARD"},
        {"name": "body_risk_range", "min_pips": 1, "max_pips": 6, "type": "HARD"},
        {"name": "no_counter_cisd", "window": "C1_C2", "type": "HARD"}
    ],
    "scoring": {
        "model": "cisd_v3_score",
        "min_score": 40
    },
    "risk_tiers": [
        {"name": "BASE", "score_range": [40, 54], "risk_pct": 0.25},
        {"name": "STANDARD", "score_range": [55, 64], "risk_pct": 0.50},
        {"name": "STRONG", "score_range": [65, 74], "risk_pct": 0.75},
        {"name": "PREMIUM", "score_range": [75, 100], "risk_pct": 1.00}
    ],
    "targets": {
        "primary_r": 3,
        "stop": "C2_BODY_EXTREME"
    },
    "expiry_hours": 48
}
```

Adding FTLR for GBPUSD becomes: copy the FTLR config, change `"pairs": ["GBPUSD"]`, adjust any pair-specific parameters. Zero code changes.

---

## 4. TECHNOLOGY STACK

### 4.1 Primary Language: Python

**Why Python:**
- Dominant language for quantitative finance and data analysis
- Libraries: pandas/polars, numpy, vectorbt, quantstats, scipy
- Excellent testing ecosystem (pytest)
- Claude Code generates high-quality Python
- FastAPI for building APIs
- Strong Supabase/PostgreSQL client libraries (psycopg2, supabase-py)

**Python version:** 3.11+ (for performance improvements and modern type hints)

### 4.2 Development Environment: VS Code + Claude Code

**VS Code** as the central IDE with:
- Claude Code extension (AI-assisted development with full codebase context)
- Python extension (linting, debugging, IntelliSense)
- GitLens (Git history visualization)
- Pylance (type checking)

**Claude Code** provides:
- Agentic coding: give high-level tasks, Claude figures out the steps
- Codebase awareness: reads the entire project structure
- Plan mode: Claude outlines approach before making changes (human in the loop)
- Subagents: parallel task delegation for specialized work
- Hooks: automatically run tests after code changes
- `CLAUDE.md` for persistent project context

### 4.3 Version Control: Git + GitHub

**GitHub** (private repository) for:
- Full version history of all code, SQL, configuration, documentation
- Branching strategy (see section 6.4)
- Pull requests for code review (human validation step)
- GitHub Actions for CI/CD
- Issue tracking for bugs and feature requests

### 4.4 Database: Supabase (PostgreSQL)

**Keep Supabase** as the database layer. What changes:
- SQL functions that contain business logic migrate to Python
- Database retains efficient queries, constraints, and data storage
- Complex logic lives in Python, simple CRUD and aggregations stay in SQL
- Schema migrations tracked in Git (via migration files)

### 4.5 API Layer: FastAPI

**FastAPI** (Python) as the interface between automation and business logic:
- N8N calls FastAPI endpoints instead of raw SQL
- Automatic OpenAPI documentation
- Pydantic models for request/response validation
- Async support for non-blocking operations
- Easy to test with pytest

### 4.6 Automation: N8N (retained)

**N8N stays** as the scheduler and orchestrator:
- Triggers on time schedules (every 5 minutes)
- Calls FastAPI endpoints for business logic
- Handles Discord webhook formatting
- Workflow JSON files version controlled in Git
- Logic moves OUT of N8N nodes and INTO Python/FastAPI

### 4.7 Quantitative Libraries

| Library | Purpose | Priority |
|---------|---------|----------|
| **pandas** | Data manipulation, time series | Essential (day 1) |
| **numpy** | Numerical computations | Essential (day 1) |
| **psycopg2** / **supabase-py** | Database connectivity | Essential (day 1) |
| **pytest** | Testing framework | Essential (day 1) |
| **FastAPI** | API layer | Essential (phase 2) |
| **pydantic** | Data validation and models | Essential (phase 2) |
| **vectorbt** | High-speed backtesting | High (phase 3) |
| **quantstats** | Strategy performance tear sheets | High (phase 3) |
| **polars** | Fast DataFrame alternative for large datasets | Medium (when needed) |
| **scipy** | Statistical testing | Medium (research) |
| **matplotlib / plotly** | Visualization | Medium (research) |

### 4.8 Infrastructure

| Component | Current | Target | Notes |
|-----------|---------|--------|-------|
| Hosting | Hetzner VPS (€7.50/mo) | Same | Sufficient for current scale |
| Containers | Docker (N8N, PostgreSQL, Caddy) | Add Python/FastAPI container | Docker Compose |
| SSL | Caddy | Same | Auto-renewal |

**Docker Compose target state:**

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [db]
    restart: unless-stopped
  n8n:
    image: n8nio/n8n
    ports: ["5678:5678"]
    volumes: [n8n_data:/home/node/.n8n]
    restart: unless-stopped
  db:
    image: postgres:16
    volumes: [pg_data:/var/lib/postgresql/data]
    restart: unless-stopped
  caddy:
    image: caddy:2
    ports: ["80:80", "443:443"]
    restart: unless-stopped
```
| CI/CD | None | GitHub Actions | Free for private repos (2000 min/mo) |
| Secrets | N8N env vars | `.env` file (git-ignored) + GitHub Secrets | Centralized |

### 4.9 Environment Management

Three environments with clear boundaries:

| Environment | Purpose | Database | Deployment |
|-------------|---------|----------|------------|
| **Local (dev)** | Development and testing | Local PostgreSQL (Docker) or Supabase dev branch | `docker-compose up` |
| **Staging** | Pre-production validation | Supabase development branch (free feature) | Manual deploy to VPS |
| **Production** | Live trading | Supabase production (Fractal AI) | Merge to `main` → auto-deploy |

Code flows: local → staging → production. No code reaches production without passing through staging first. Staging uses a separate Supabase branch (free tier feature) so we can test database migrations without risking production data.

### 4.10 Linting and Code Quality

| Tool | Purpose | Integration |
|------|---------|-------------|
| **ruff** | Python linter + formatter (replaces flake8, isort, black) | CI + pre-commit hook |
| **mypy** | Static type checking (stretch goal) | CI |
| **pre-commit** | Git hooks for automated checks before commit | Local dev |

---

## 5. UBIQUITOUS LANGUAGE (GLOSSARY)

A consistent vocabulary used across all code, documentation, database columns, and conversations. This is non-negotiable — every contributor (human or AI) must use these exact terms.

### Market Data Terms

| Term | Definition | Code Convention |
|------|-----------|-----------------|
| **Candle** | A single OHLC price bar for a specific timeframe | `candle`, `Candle` |
| **Pair** | A currency pair (e.g., EURUSD) | `pair: str` — always uppercase, no slash |
| **Timeframe** | The candle period (e.g., 5M, 1H, 4H, D) | `timeframe: str` — uppercase with unit |
| **Session** | A trading session: ASIA, LONDON, NY | `session: str` — uppercase |
| **Pip** | Minimum price increment (0.0001 for majors) | `pips: float` |

### Structure Terms

| Term | Definition | Code Convention |
|------|-----------|-----------------|
| **Swing** | A price reversal point (high or low) | `swing`, `Swing` |
| **Swing High** | A local price maximum | `swing_type: "HIGH"` |
| **Swing Low** | A local price minimum | `swing_type: "LOW"` |
| **C1 / C2 / C3** | The three candles in a swing pattern | `c1_candle`, `c2_candle`, `c3_candle` |
| **C2 Closure** | C2 candle closes beyond C1 extreme | `closure_type: "C2_CLOSURE"` |
| **C3 Closure** | C3 confirms beyond C2 | `closure_type: "C3_CLOSURE"` |
| **Swing Strength** | Classification: STRONG, INTERNAL, WEAK | `swing_strength: str` |
| **Key Level** | A significant price level (session H/L, PDH/PDL, PWH/PWL) | `level`, `KeyLevel` |
| **Level Sweep** | Price wick exceeds level but closes back | `is_swept: bool` |
| **First Touch** | No prior sweep of a level | `is_first_touch: bool` |
| **Swing Point** | A level coinciding with a swing H/L | `is_swing_point: bool` |
| **FVG** | Fair Value Gap — price imbalance between 3 candles | `fvg`, `FairValueGap` |
| **CISD** | Change in State of Delivery — microstructure reversal | `cisd`, `CISDEvent` |
| **Series** | Count of consecutive same-direction 5M candles in a CISD | `series_length: int` |
| **DOL** | Draw on Liquidity — the target level | `dol`, `draw_on_liquidity` |

### Strategy Terms

| Term | Definition | Code Convention |
|------|-----------|-----------------|
| **Signal** | A strategy's determination that conditions are met | `signal`, `Signal` |
| **Filter** | A pass/fail condition in signal evaluation | `filter`, `Filter` |
| **Score** | A 0-100 quality rating for a signal | `score: int` |
| **Risk Tier** | Position sizing tier based on score | `risk_tier: str` (BASE/STANDARD/STRONG/PREMIUM) |
| **R** | Risk unit — the distance from entry to stop loss | `r_value: float` |
| **Target (xR)** | Take profit as multiple of R | `target_r: int` (e.g., 2 for 2R) |
| **Win Rate** | Percentage of trades hitting target | `win_rate: float` — always specify which R target |

### Trade Terms

| Term | Definition | Code Convention |
|------|-----------|-----------------|
| **Trade** | A monitored position from entry to close | `trade`, `Trade` |
| **Entry** | The price and time a trade opens | `entry_price`, `entry_time` |
| **Stop Loss** | The maximum loss price | `stop_loss: float` |
| **Take Profit** | The target price | `take_profit: float` |
| **Outcome** | WIN, LOSS, EXPIRED, CANCELLED | `outcome: str` |
| **P&L** | Profit and loss in account currency | `pnl: float` |
| **Result R** | Outcome expressed in R multiples | `result_r: float` |

### Research Terms

| Term | Definition | Code Convention |
|------|-----------|-----------------|
| **Hypothesis** | A pre-registered prediction to test | `hypothesis`, `Hypothesis`, ID: `H-XXX` |
| **Finding** | Evidence from data analysis | `finding`, `Finding`, ID: `F-XXX` |
| **Conclusion** | Synthesis of multiple findings | `conclusion`, `Conclusion`, ID: `C-XXX` |
| **Rule** | An actionable trading rule derived from conclusions | `rule`, `Rule`, ID: `R-XXX` |
| **IN_SAMPLE** | Found and tested on the same data | `validation_type: "IN_SAMPLE"` |
| **OUT_OF_SAMPLE** | Tested on data not used for discovery | `validation_type: "OUT_OF_SAMPLE"` |
| **WALK_FORWARD** | Tested on sequential unseen periods | `validation_type: "WALK_FORWARD"` |
| **LIVE** | Confirmed in real trading | `validation_type: "LIVE"` |

---

## 6. GOLDEN STANDARD (CODING & DEVELOPMENT CONVENTIONS)

### 6.1 Project Structure

```
fractal-ai/
├── CLAUDE.md                    # AI agent project context (see section 7)
├── claude-progress.txt          # Multi-session progress tracking
├── features.json                # Feature/task tracking for AI agents
├── pyproject.toml               # Python dependencies and project metadata
├── docker-compose.yml           # Container orchestration
├── .env.example                 # Environment variable template
├── .github/
│   └── workflows/
│       ├── test.yml             # Run tests on every push
│       ├── lint.yml             # Code quality checks
│       └── deploy.yml           # Production deployment
│
├── docs/
│   ├── FA_STATE.md              # Current project status
│   ├── FA_TOLERANCES.md         # Constants and thresholds
│   ├── GLOSSARY.md              # Ubiquitous language (from section 5)
│   ├── strategies/
│   │   ├── FTLR_PLAYBOOK.md
│   │   ├── CISD_V3_PLAYBOOK.md
│   │   └── S_SCALP_V3_PLAYBOOK.md
│   └── architecture/
│       ├── BLUEPRINT.md         # This document
│       └── diagrams/            # Mermaid source files
│
├── config/
│   ├── strategies/
│   │   ├── ftlr_v2.json        # FTLR strategy configuration
│   │   ├── cisd_v3.json        # CISD strategy configuration
│   │   └── scalp_v3.json       # S-SCALP strategy configuration
│   ├── tolerances.json          # Pip tolerances, time constants
│   ├── sessions.json            # Trading session definitions
│   └── pairs.json               # Pair-specific parameters
│
├── src/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── market_data/
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Candle, DataGap entities
│   │   │   ├── ingestion.py     # TwelveData adapter (anti-corruption layer)
│   │   │   ├── validation.py    # Gap detection, duplicate checking
│   │   │   └── repository.py    # Database operations for candles
│   │   │
│   │   ├── structure/
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Swing, KeyLevel, Pattern, CISD entities
│   │   │   ├── swing_detection.py
│   │   │   ├── level_detection.py
│   │   │   ├── pattern_recognition.py
│   │   │   ├── cisd_detection.py
│   │   │   └── repository.py
│   │   │
│   │   ├── strategy/
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Strategy, Signal, Filter, Score entities
│   │   │   ├── engine.py        # Generic strategy evaluation engine
│   │   │   ├── filters.py       # Filter implementations
│   │   │   ├── scoring.py       # Scoring model implementations
│   │   │   └── repository.py
│   │   │
│   │   ├── execution/
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Trade, Position, Account entities
│   │   │   ├── trade_manager.py # Trade lifecycle management
│   │   │   ├── risk_manager.py  # Position sizing, exposure limits
│   │   │   ├── portfolio.py     # Portfolio-level risk: correlation, net exposure, max drawdown
│   │   │   └── repository.py
│   │   │
│   │   ├── research/
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Hypothesis, Finding, Conclusion, Rule
│   │   │   ├── backtester.py    # Backtesting engine
│   │   │   ├── validator.py     # OOS validation, walk-forward
│   │   │   ├── knowledge_chain.py
│   │   │   └── repository.py
│   │   │
│   │   └── observability/
│   │       ├── __init__.py
│   │       ├── models.py        # HealthCheck, Metric, Alert
│   │       ├── health.py        # Health check implementations
│   │       ├── metrics.py       # Metric collection
│   │       ├── alerting.py      # Discord alert formatting
│   │       └── logger.py        # Structured logging
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── strategy.py      # /api/strategy/evaluate
│   │   │   ├── health.py        # /api/health
│   │   │   ├── trades.py        # /api/trades
│   │   │   └── data.py          # /api/data/sync
│   │   └── schemas.py           # Pydantic request/response models
│   │
│   ├── events/
│   │   ├── __init__.py
│   │   ├── bus.py               # Simple event bus implementation
│   │   ├── types.py             # Event type definitions
│   │   └── handlers.py          # Event handler registry
│   │
│   └── infrastructure/
│       ├── __init__.py
│       ├── database.py          # Database connection management
│       ├── twelve_data.py       # TwelveData API client
│       ├── discord.py           # Discord webhook client
│       └── config.py            # Configuration loading
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── unit/
│   │   ├── test_swing_detection.py
│   │   ├── test_level_detection.py
│   │   ├── test_pattern_recognition.py
│   │   ├── test_cisd_detection.py
│   │   ├── test_strategy_engine.py
│   │   ├── test_filters.py
│   │   ├── test_scoring.py
│   │   ├── test_trade_manager.py
│   │   ├── test_risk_manager.py
│   │   └── test_data_validation.py
│   ├── integration/
│   │   ├── test_pipeline.py     # End-to-end pipeline tests
│   │   ├── test_api.py          # API endpoint tests
│   │   └── test_database.py     # Database operation tests
│   └── fixtures/
│       ├── candles.json         # Known candle datasets for testing
│       ├── swings.json          # Expected swing detection results
│       └── signals.json         # Expected signal evaluation results
│
├── migrations/
│   ├── 001_initial_schema.sql
│   ├── 002_add_strategy_config.sql
│   └── README.md                # Migration conventions
│
├── n8n/
│   ├── wf1_data_pipeline.json
│   ├── wf2_strategy_engine.json
│   ├── wf3_health_check.json
│   └── README.md                # N8N deployment instructions
│
└── scripts/
    ├── setup.sh                 # Initial environment setup
    ├── deploy.sh                # Deployment script
    ├── backtest.py              # CLI backtesting tool
    └── validate.py              # Monthly re-validation script
```

### 6.2 Python Coding Conventions

**Style:** PEP 8 with the following specifics:

- Maximum line length: 100 characters
- Type hints required on all function signatures
- Docstrings required on all public functions (Google style)
- No magic numbers — all constants in config files or named constants

**Naming:**

| Element | Convention | Example |
|---------|-----------|---------|
| Files | snake_case | `swing_detection.py` |
| Classes | PascalCase | `SwingDetector` |
| Functions | snake_case | `detect_swings()` |
| Variables | snake_case | `swing_high` |
| Constants | UPPER_SNAKE_CASE | `MAX_SERIES_LOOKBACK` |
| Config keys | snake_case | `min_score` |
| Database tables | snake_case | `detected_swings` |
| Database columns | snake_case | `swing_type` |
| Enum values | UPPER_SNAKE_CASE | `C2_CLOSURE` |

**Function structure:**

```python
def detect_swings(
    candles: list[Candle],
    pair: str,
    timeframe: str,
    min_swing_pips: float | None = None,
) -> list[Swing]:
    """Detect C1-C2-C3 swing patterns in a series of candles.

    Scans the candle series for swing highs and lows using the
    three-candle pattern: C1 sets the initial extreme, C2 exceeds it,
    and C3 confirms the reversal.

    Args:
        candles: Ordered list of OHLC candles (oldest first).
        pair: Currency pair (e.g., "EURUSD").
        timeframe: Candle timeframe (e.g., "1H").
        min_swing_pips: Minimum swing size filter. Defaults to
            pair/timeframe-specific value from config.

    Returns:
        List of detected Swing objects, ordered by time.

    Raises:
        ValueError: If fewer than 3 candles provided.
    """
```

### 6.3 Testing Conventions (Test-Driven Development)

**Philosophy:** Write the test FIRST, then write the code to make it pass.

**Test structure:**

```python
class TestSwingDetection:
    """Tests for swing detection logic."""

    def test_detects_basic_swing_high(self, sample_candles_swing_high):
        """A clear C1-C2-C3 swing high should be detected."""
        swings = detect_swings(sample_candles_swing_high, "EURUSD", "1H")
        assert len(swings) == 1
        assert swings[0].swing_type == "HIGH"
        assert swings[0].swing_price == sample_candles_swing_high[1].high

    def test_ignores_swing_below_minimum_pips(self, tiny_swing_candles):
        """Swings smaller than min_swing_pips should be filtered out."""
        swings = detect_swings(tiny_swing_candles, "EURUSD", "1H", min_swing_pips=10.0)
        assert len(swings) == 0

    def test_handles_empty_candle_list(self):
        """Empty input should raise ValueError."""
        with pytest.raises(ValueError):
            detect_swings([], "EURUSD", "1H")
```

**Test fixtures** use known datasets stored in `tests/fixtures/`. These are real market data samples with manually verified expected outputs — the same validation approach we used in Phase 0, now automated.

**Coverage target:** 90% for domain logic, 80% for API and infrastructure.

### 6.4 Git Branching Strategy

```
main                    ← Production-stable code. Deploys to live system.
  └── develop           ← Integration branch. All features merge here first.
       ├── feature/*    ← New features (e.g., feature/cisd-filter-update)
       ├── research/*   ← Research experiments (e.g., research/trend-filter-ftlr)
       ├── fix/*        ← Bug fixes (e.g., fix/swing-detection-jan23)
       └── migration/*  ← SQL-to-Python migration work
```

**Rules:**
- `main` is always deployable. Never commit directly to main.
- All changes go through pull requests with at least a test suite pass.
- Feature branches are short-lived (max 1 week).
- Research branches are exempt from PR requirements (experimentation zone) but cannot merge to develop without tests.

### 6.5 SQL Conventions (for database-level operations that remain in SQL)

- All SQL files tracked in `migrations/` directory
- Each migration is numbered sequentially: `001_`, `002_`, etc.
- Migrations are idempotent (safe to re-run)
- Functions that remain in SQL follow the domain prefix: `market_data_*`, `structure_*`, `strategy_*`, `trade_*`

---

## 7. CONTEXT ENGINEERING

### 7.1 CLAUDE.md — The AI Agent's Bible

The `CLAUDE.md` file at the project root is the single most important file for AI-assisted development. Every time Claude Code starts a session, it reads this file first. It must contain everything an AI agent needs to understand the project and contribute effectively.

**Contents of CLAUDE.md:**

```markdown
# Fractal AI — Systematic Forex Trading Platform

## Overview
Fractal AI is a systematic forex trading system that detects market structure
patterns (swings, levels, CISDs) and evaluates them against configured strategy
rules to generate trading signals. Currently monitors EURUSD with three active
strategies: FTLR-v2, CISD-v3, and S-SCALP-v3.

## Tech Stack
- Python 3.11+, FastAPI, pytest
- PostgreSQL (Supabase) for data storage
- N8N for workflow automation
- Discord for alerting
- Docker for containerization

## Architecture
Domain-Driven Design with 6 bounded contexts:
Market Data → Structure Detection → Strategy Logic → Trade Execution
Plus: Research and Observability as cross-cutting domains.
See docs/architecture/BLUEPRINT.md for full details.

## Project Structure
[abbreviated tree — key directories and their purposes]

## Commands
python -m pytest                    # Run all tests
python -m pytest tests/unit/        # Run unit tests only
python -m src.api.main              # Start FastAPI server
python scripts/backtest.py          # Run backtesting
python scripts/validate.py          # Monthly re-validation

## Code Patterns
- All functions require type hints and Google-style docstrings
- Domain entities use Pydantic models
- Strategy logic is configuration-driven (see config/strategies/)
- Tests use fixtures from tests/fixtures/ with real market data
- No magic numbers — all constants in config/ or named constants

## Key Conventions
- Pair is always uppercase, no slash: "EURUSD" not "EUR/USD"
- Timeframe is uppercase with unit: "1H" not "1h" or "60"
- Swing types: "HIGH" or "LOW"
- Closure types: "C2_CLOSURE" or "C3_CLOSURE"
- Validation types: "IN_SAMPLE", "OUT_OF_SAMPLE", "WALK_FORWARD", "LIVE"
- See docs/GLOSSARY.md for complete terminology

## Current State
See docs/FA_STATE.md for live project status.
See claude-progress.txt for recent session history.

## Testing
- Write tests BEFORE implementation (TDD)
- Test fixtures contain real market data with verified expected outputs
- Coverage target: 90% domain logic, 80% infrastructure
- Tests must pass before any merge to develop or main

## What NOT to Do
- Never hardcode pair or timeframe in domain logic
- Never put business logic in N8N workflow nodes
- Never deploy SQL directly to Supabase — use migration files
- Never commit secrets or .env files
- Never merge to main without passing tests
```

### 7.2 claude-progress.txt — Session Continuity

Inspired by Anthropic's research on long-running agents. This file is read at the start of every session and updated at the end.

```
# Claude Progress Log
# Format: [DATE] [SESSION_TYPE] Summary | Next Steps

[2026-02-26] [MIGRATION] Ported swing_detection.py from SQL to Python.
  - 12 tests written, all passing
  - Handles C2_CLOSURE and C3_CLOSURE patterns
  - Known gap: intermediate swing detection not yet ported
  | NEXT: Port level_detection.py, add integration test with real data

[2026-02-25] [RESEARCH] Tested trend filter impact on FTLR.
  - H-012 registered: "Trend alignment improves FTLR WR by 15%+"
  - F-210: Trend-aligned = 72.3% WR (n=31), counter = 48.1% (n=43)
  - F-211 (adversarial): Effect concentrated in STRONG trends only
  | NEXT: Register conclusion, create rule, run OOS validation
```

### 7.3 features.json — Structured Task Tracking

```json
{
  "migration_tasks": [
    {
      "id": "MIG-001",
      "description": "Port swing detection from SQL to Python",
      "domain": "structure",
      "status": "passing",
      "tests": 12,
      "completed_date": "2026-02-26"
    },
    {
      "id": "MIG-002",
      "description": "Port level detection from SQL to Python",
      "domain": "structure",
      "status": "failing",
      "tests": 0,
      "completed_date": null
    }
  ]
}
```

---

## 8. MULTI-AGENT FRAMEWORK

### 8.1 Concept

Inspired by the multi-agent framework approach presented by Icapps (Antwerp-based software company) at their AI event, where multiple AI agents mimic professional profiles (planning, business analysis, architecture, development, QA, testing, security) to handle a feature request from ticket to deployment. Adapted for Fractal AI's context: every significant change flows through a pipeline of specialized "agent steps" with human validation between them. These are not separate AI instances — they are structured prompts and workflows that Claude Code executes, with Robin approving at each gate.

**Key Icapps principles adopted:**
- Human in the loop between every agent step
- Test-driven development methodology
- Clean documentation architecture for AI context
- Context engineering for each agent step (right context, minimal tokens)
- Compound learning from every agent output
- Golden standard for quality assurance

### 8.2 Agent Pipeline: New Strategy Implementation

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   RESEARCH   │     │   BUSINESS   │     │  ARCHITECT   │
│   ANALYST    │────▶│   ANALYST    │────▶│              │
│              │     │              │     │              │
│ Input:       │     │ Input:       │     │ Input:       │
│ Raw idea     │     │ Hypothesis   │     │ Validated    │
│              │     │              │     │ rules        │
│ Output:      │     │ Output:      │     │              │
│ Registered   │     │ Strategy     │     │ Output:      │
│ hypothesis + │     │ config +     │     │ Technical    │
│ adversarial  │     │ acceptance   │     │ design +     │
│ questions    │     │ criteria     │     │ schema       │
│              │     │              │     │ changes      │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                     │
   [HUMAN OK]          [HUMAN OK]            [HUMAN OK]
       │                    │                     │
       ▼                    ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  DEVELOPER   │     │     QA       │     │   SECURITY   │
│              │────▶│   TESTER     │────▶│   / RISK     │
│              │     │              │     │              │
│ Input:       │     │ Input:       │     │ Input:       │
│ Technical    │     │ Implementation│    │ Tested code  │
│ design       │     │ + tests      │     │              │
│              │     │              │     │ Output:      │
│ Output:      │     │ Output:      │     │ Risk         │
│ Working code │     │ Test results │     │ assessment + │
│ + unit tests │     │ + edge cases │     │ worst-case   │
│              │     │ + regression │     │ scenarios    │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                     │
   [HUMAN OK]          [HUMAN OK]            [HUMAN OK]
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │   DEPLOY     │
                                          │              │
                                          │ Merge to     │
                                          │ main, deploy │
                                          │ to production│
                                          └──────────────┘
```

### 8.3 Agent Pipeline: Research Hypothesis

```
IDEA → [Research Analyst] → Hypothesis + Questions + Adversarial Qs
                                    ↓ [HUMAN OK]
     [Data Architect] → Required queries + data availability check
                                    ↓ [HUMAN OK]
     [Quantitative Analyst] → Execute queries, record findings
                                    ↓ [HUMAN OK]
     [Devil's Advocate] → Challenge findings, test edge cases
                                    ↓ [HUMAN OK]
     [Synthesis Agent] → Conclusions with confidence + validation type
                                    ↓ [HUMAN OK]
     [Rule Formulator] → Actionable rule + strategy config update
```

### 8.4 Agent Pipeline: Bug Fix

```
BUG REPORT → [Architect] → Root cause analysis + impact assessment
                                    ↓ [HUMAN OK]
           [Developer] → Fix + regression test (TDD: test first, then fix)
                                    ↓ [HUMAN OK]
           [QA] → Run full test suite + verify fix + check related code
                                    ↓ [HUMAN OK]
           [Deploy] → Merge + deploy
```

### 8.5 Implementation with Claude Code

In practice, these "agents" are implemented as structured prompts or Claude Code custom commands. For example, a `/research-analyst` command in Claude Code could be configured to:

1. Read the current hypotheses from the database
2. Help formulate a new hypothesis with prediction and invalidation criteria
3. Generate adversarial questions
4. Log everything to the research tables
5. Update claude-progress.txt

**Claude Code features that support this:**

- **Custom commands:** Define `/research`, `/develop`, `/qa`, `/deploy` commands that load the right context and instructions for each agent role
- **Hooks:** Automatically run tests after any code change (`post-edit` hook), run linting before commits (`pre-commit` hook). This enforces quality without manual discipline.
- **Subagents:** Delegate specialized tasks in parallel — e.g., one subagent writes the implementation while another writes the tests, or one researches while another documents
- **Plan mode:** Claude outlines its approach before executing, giving Robin a checkpoint to approve or redirect

This doesn't require a multi-agent framework like CrewAI or LangGraph. It's Claude Code with structured workflows and human checkpoints. The key innovation is the discipline of distinct steps with distinct outputs, not the technology.

---

## 9. COMPOUND LEARNING LOOP

### 9.1 How Learning Flows

Every output in the system generates structured learnings that feed back into future work:

```
TRADE COMPLETES
    ↓
TRADE AUTOPSY (automated)
    ├── Market context at entry (session, trend, volatility)
    ├── Which filters passed/failed
    ├── Microstructure quality assessment
    ├── Entry timing vs. ideal
    ├── Outcome vs. expected
    └── Tagged anomalies (if any)
    ↓
LEARNING DATABASE
    ↓
MONTHLY PATTERN ANALYSIS (automated)
    ├── "FTLR performs X% worse during high-vol weeks"
    ├── "CISD premium tier maintains 85% WR (stable)"
    ├── "Session X produces more false signals than Session Y"
    └── Triggers re-validation if deviation > 15%
    ↓
STRATEGY CONFIG UPDATES (human-approved)
    ├── Adjust risk tiers
    ├── Add/modify filters
    ├── Update trading windows
    └── Pause strategy in adverse conditions
    ↓
GOLDEN STANDARD UPDATES
    ├── "Pattern X doesn't work — don't research further"
    ├── "Approach Y produced best results for this type of analysis"
    └── Updated CLAUDE.md with new patterns/anti-patterns
```

### 9.2 Trade Autopsy Structure

Every closed trade automatically generates:

```python
{
    "trade_id": "T-042",
    "strategy": "CISD-v3",
    "pair": "EURUSD",
    "outcome": "WIN",
    "result_r": 3.0,
    "context": {
        "session": "LONDON",
        "trend": "BULLISH",
        "trend_strength": "STRONG",
        "volatility_regime": "NORMAL",
        "day_of_week": "TUE"
    },
    "signal_quality": {
        "score": 78,
        "tier": "PREMIUM",
        "filters_passed": ["series_gte_2", "c2_aligned", "c3_confirms", "body_risk_ok"],
        "c3_displacement_pips": 4.2
    },
    "execution": {
        "entry_delay_seconds": 0,
        "actual_vs_expected_entry": 0.0,
        "time_to_target_minutes": 47
    },
    "learnings": []  # Populated by analysis
}
```

### 9.3 Monthly Re-Validation (Automated)

The `scripts/validate.py` script runs on the first weekend of each month:

1. Pull all ACTIVE rules and KEY_INSIGHT conclusions
2. Re-run stored SQL/Python against latest data
3. Compare current values to original discovery values
4. Flag deviations > 15%
5. Generate validation report
6. Send Discord summary
7. Update `research_validations` table

---

## 10. DATA MANAGEMENT

### 10.1 Data Validation Layer

Every candle received from TwelveData passes through validation before entering the database:

**Checks:**
- Timestamp is sequential (no gaps within session hours)
- OHLC values are reasonable (not zero, not 10x normal range)
- No exact duplicates
- Volume is present (if provided)
- Candle falls within expected session hours

**On failure:** Log the issue, alert on Discord, but do NOT block the pipeline. Missing/bad candles are flagged for manual review. The system should degrade gracefully, not halt entirely.

### 10.2 Data Retention Policy

| Data Type | Full Resolution | Aggregated | Archive |
|-----------|----------------|------------|---------|
| 5M candles | Last 3 months | Hourly beyond 3 months | Delete beyond 12 months |
| 1H candles | Last 12 months | Daily beyond 12 months | Keep all |
| 4H/D/W candles | Keep all | N/A | N/A |
| Trade data | Keep all | N/A | N/A |
| Signal evaluations | Last 6 months | Monthly stats beyond | Keep stats |
| Research data | Keep all | N/A | N/A |

This policy keeps us well within the 500MB Supabase free tier while maintaining full resolution for active analysis.

### 10.3 Anti-Corruption Layer (External Data)

TwelveData's API format is translated at the boundary:

```python
class TwelveDataAdapter:
    """Translates TwelveData API responses into Fractal AI Candle models.

    If we switch to a different data provider (e.g., OANDA, Polygon),
    we only change this adapter. No other code is affected.
    """

    def to_candle(self, raw_response: dict) -> Candle:
        return Candle(
            pair=self._normalize_pair(raw_response["symbol"]),
            timeframe=self._normalize_timeframe(raw_response["interval"]),
            timestamp=self._parse_timestamp(raw_response["datetime"]),
            open=float(raw_response["open"]),
            high=float(raw_response["high"]),
            low=float(raw_response["low"]),
            close=float(raw_response["close"]),
            volume=float(raw_response.get("volume", 0)),
        )
```

---

## 11. OBSERVABILITY

### 11.1 Structured Logging

Replace ad-hoc print statements and Discord messages with structured logging:

```python
import structlog

logger = structlog.get_logger()

# Every log entry includes context
logger.info(
    "signal_evaluated",
    strategy="CISD-v3",
    pair="EURUSD",
    outcome="TAKEN",
    score=78,
    tier="PREMIUM",
    filters_passed=5,
)
```

Logs are written to file (rotated daily) and can be forwarded to any log aggregation service if needed later.

### 11.2 Health Checks

The existing `system_health_check()` function is a good foundation. In the target state, health checks are defined per domain:

| Check | Domain | Frequency | Alert On |
|-------|--------|-----------|----------|
| Data freshness | Market Data | Every 5 min | Gap > 15 min during session |
| Candle completeness | Market Data | Hourly | Missing candles in last hour |
| Swing detection running | Structure | Every 5 min | No new swings in 4 hours |
| Strategy evaluation running | Strategy | Every 5 min | No evaluations in 1 hour |
| Open trade monitoring | Execution | Every 5 min | Trade not checked in 15 min |
| Database size | Infrastructure | Daily | > 400 MB (approaching limit) |
| API response time | Infrastructure | Every 5 min | > 5 seconds |

### 11.3 Daily Performance Summary

Automated Discord message every day at 21:00 UTC:

```
📊 Fractal AI Daily Summary — Feb 26, 2026

STRATEGIES
  FTLR-v2:  0 signals, 0 trades, $0.00
  CISD-v3:  2 signals (1 TAKEN, 1 FILTERED), 0 closes
  S-SCALP:  3 signals (2 TAKEN, 1 FILTERED), 1 WIN (+3R)

SYSTEM HEALTH: ✅ All checks passing
  Data freshness: 2 min ago
  Pipeline latency: 1.3s avg
  DB size: 38 MB / 500 MB

UPCOMING
  Monthly re-validation: Mar 1 (3 days)
```

---

## 12. DISASTER RECOVERY

### 12.1 The "Rebuild from Git" Test

The system is designed so that the entire trading platform can be reconstructed from the Git repository alone. This means:

- All code (Python, SQL migrations) is in Git
- All configuration (strategy configs, tolerances, session definitions) is in Git
- All N8N workflow definitions (JSON exports) are in Git
- All documentation is in Git
- Database schema can be reconstructed from migration files
- The only thing NOT in Git is the actual market data (which can be re-fetched from TwelveData)

### 12.2 Backup Strategy

| What | How | Frequency |
|------|-----|-----------|
| Git repository | GitHub (remote) | Every push |
| Supabase production DB | Supabase automated backups | Daily |
| Supabase research DB | Supabase automated backups | Daily |
| N8N workflows | JSON export in Git | After every change |
| Environment variables | `.env.example` template in Git | After every change |

### 12.3 Rollback Procedure

If a deployment breaks something:
1. `git revert <commit>` to undo the change
2. Re-deploy the reverted version
3. If database migration was involved, run the corresponding down-migration
4. Verify via health checks

---

## 13. BUILD VS. BUY DECISIONS

For each component, an explicit decision on whether to build custom or use existing tools:

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Swing detection | **BUILD** | Our ICT-specific C1-C2-C3 pattern is unique; no library supports it |
| Level detection | **BUILD** | Session-level logic is specific to our methodology |
| CISD detection | **BUILD** | Unique microstructure pattern; no existing implementation |
| Pattern recognition | **BUILD** | Core competitive edge |
| Strategy engine | **BUILD** | Configuration-driven engine specific to our domain |
| Backtesting | **HYBRID** | Build our own runner, use vectorbt for speed on parameter sweeps |
| Performance analytics | **BUY** | Use quantstats for tear sheets and standard metrics |
| Statistical testing | **BUY** | Use scipy for hypothesis testing, confidence intervals |
| Data manipulation | **BUY** | Use pandas (or polars for speed) |
| API framework | **BUY** | FastAPI — mature, well-documented, async |
| Testing | **BUY** | pytest — industry standard |
| Database | **BUY** | Supabase/PostgreSQL — already working, no reason to change |
| Automation | **BUY** | N8N — already working, good at scheduling |
| Logging | **BUY** | structlog — structured logging for Python |
| Event bus | **BUILD** (simple) | Start with in-process events; upgrade to Redis/PG LISTEN if needed |

---

## 14. MIGRATION PLAN

### 14.1 Philosophy

**Incremental, not big-bang.** The live system keeps running on SQL + N8N. New Python modules are built alongside, tested thoroughly, and swapped in one at a time. At no point does the live trading system go offline.

### 14.2 Migration Phases

#### Phase M0: Foundation (Est. 2-3 sessions)

**Goal:** Set up the development environment and project skeleton.

**Deliverables:**
- [ ] GitHub private repository created
- [ ] Project structure created (as defined in section 6.1)
- [ ] `CLAUDE.md` written and committed
- [ ] `pyproject.toml` with dependencies
- [ ] Docker Compose with Python container
- [ ] pytest configured with basic test
- [ ] GitHub Actions workflow for running tests
- [ ] `.env.example` with all required variables
- [ ] `GLOSSARY.md` committed
- [ ] This blueprint committed to `docs/architecture/`

**Human checkpoints:** Robin reviews and approves the repo structure before any code is written.

#### Phase M1: First Reference Module — Swing Detection (Est. 3-4 sessions)

**Goal:** Port swing detection from SQL to Python as the reference implementation. This module sets the pattern that all other modules will follow.

**Why swing detection first:**
- Well-understood logic (validated in Phase 0)
- Has a known bug to fix (January 23 miss)
- Existing test cases from manual validation
- Clear input (candles) and output (swings) — easy to verify

**Deliverables:**
- [ ] `src/domain/structure/models.py` — Swing and Candle Pydantic models
- [ ] `src/domain/structure/swing_detection.py` — Core detection logic
- [ ] `tests/unit/test_swing_detection.py` — Comprehensive tests (TDD)
- [ ] `tests/fixtures/candles.json` — Real market data test fixtures
- [ ] `tests/fixtures/swings.json` — Expected outputs (from Phase 0 validation)
- [ ] Fix: sequential pattern detection logic (January 23 bug)
- [ ] Documentation: docstrings on all functions

**Process:**
1. Write tests first based on known validation samples
2. Implement swing detection to make tests pass
3. Compare output against current SQL function on same data
4. 100% match required before considering complete

**Human checkpoints:** Robin validates test cases before implementation. Robin reviews the completed module. Robin approves merge to develop.

#### Phase M2: Configuration System + Strategy Models (Est. 2-3 sessions)

**Goal:** Build the configuration-driven strategy system and domain models.

**Deliverables:**
- [ ] `config/strategies/*.json` — All three strategy configs
- [ ] `config/tolerances.json` — Pip tolerances, time constants
- [ ] `config/sessions.json` — Trading session definitions
- [ ] `config/pairs.json` — Pair-specific parameters
- [ ] `src/domain/strategy/models.py` — Strategy, Signal, Filter Pydantic models
- [ ] `src/infrastructure/config.py` — Config loading and validation
- [ ] Tests for config loading and validation

**Human checkpoints:** Robin reviews strategy configs match current trading rules exactly.

#### Phase M3: Structure Detection Suite (Est. 4-5 sessions)

**Goal:** Port all structure detection (levels, patterns, CISD) to Python.

**Deliverables:**
- [ ] Level detection (session levels, PDH/PDL, PWH/PWL)
- [ ] Closure pattern recognition (C2/C3)
- [ ] CISD detection with series counting
- [ ] Sweep detection
- [ ] First touch detection
- [ ] All with comprehensive tests
- [ ] Integration test: full structure detection pipeline on real data

**Human checkpoints:** Each module reviewed individually. Integration test results validated against current SQL output.

#### Phase M4: Strategy Engine (Est. 3-4 sessions)

**Goal:** Build the generic strategy evaluation engine.

**Deliverables:**
- [ ] `src/domain/strategy/engine.py` — Config-driven evaluation
- [ ] `src/domain/strategy/filters.py` — All filter implementations
- [ ] `src/domain/strategy/scoring.py` — Scoring models (CISD v3, FTLR)
- [ ] Tests: each strategy config produces same signals as current SQL
- [ ] Backtest comparison: run all three strategies through new engine, compare to known results

**Human checkpoints:** Backtest results must match existing results within tolerance (±2% WR, ±5R total). Any deviation investigated.

#### Phase M5: API Layer + N8N Integration (Est. 2-3 sessions)

**Goal:** Build FastAPI endpoints and point N8N to them.

**Deliverables:**
- [ ] FastAPI app with endpoints for strategy evaluation, health check, data sync
- [ ] Pydantic request/response models
- [ ] API tests
- [ ] N8N workflows updated to call FastAPI instead of raw SQL
- [ ] Parallel running: new API + old SQL, compare outputs

**Human checkpoints:** Parallel testing period (minimum 1 week) where both old and new systems run. Robin compares outputs daily.

#### Phase M6: Trade Management + Execution (Est. 2-3 sessions)

**Goal:** Port trade lifecycle management to Python.

**Deliverables:**
- [ ] Trade opening, monitoring, closing logic
- [ ] Position sizing and risk management
- [ ] 48-hour expiry logic
- [ ] Counter-CISD detection
- [ ] Discord alert formatting
- [ ] All with tests

#### Phase M7: Observability + Health (Est. 1-2 sessions)

**Goal:** Implement structured logging, metrics, and enhanced health checks.

**Deliverables:**
- [ ] Structured logging throughout the codebase
- [ ] Health check suite (per domain)
- [ ] Daily performance summary
- [ ] Metric collection

#### Phase M8: Research Tools (Est. 3-4 sessions)

**Goal:** Build Python-based research and backtesting tools.

**Deliverables:**
- [ ] Backtesting engine (vectorbt integration)
- [ ] Performance analytics (quantstats tear sheets)
- [ ] Monthly re-validation script
- [ ] Research knowledge chain management
- [ ] Trade autopsy generation

#### Phase M9: Cutover + Cleanup (Est. 1-2 sessions)

**Goal:** Retire old SQL-based logic, clean up.

**Deliverables:**
- [ ] Old SQL functions deprecated (not deleted — kept as reference)
- [ ] N8N workflows fully migrated to FastAPI calls
- [ ] All documentation updated
- [ ] "Rebuild from Git" test performed

### 14.3 Timeline Estimate

| Phase | Sessions | Calendar Estimate | Dependency |
|-------|----------|-------------------|------------|
| M0: Foundation | 2-3 | Week 1 | None |
| M1: Swing Detection | 3-4 | Week 2-3 | M0 |
| M2: Configuration | 2-3 | Week 3-4 | M0 |
| M3: Structure Suite | 4-5 | Week 4-6 | M1 |
| M4: Strategy Engine | 3-4 | Week 6-8 | M2, M3 |
| M5: API + N8N | 2-3 | Week 8-9 | M4 |
| M6: Trade Management | 2-3 | Week 9-10 | M4 |
| M7: Observability | 1-2 | Week 10-11 | M5 |
| M8: Research Tools | 3-4 | Week 11-13 | M4 |
| M9: Cutover | 1-2 | Week 13-14 | All |

**Total estimate: 25-33 sessions over ~14 weeks**

This can run in parallel with ongoing trading operations and research. M1 and M2 can run in parallel. M3 depends on M1. M5 and M6 can run in parallel after M4.

---

## 15. CI/CD PIPELINE

### 15.1 GitHub Actions — On Every Push

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: python -m pytest tests/unit/ -v --tb=short
      - run: python -m pytest tests/integration/ -v --tb=short
```

### 15.2 Automated Regression Testing

Every push triggers a regression suite that validates core system behavior hasn't changed:

**Regression test categories:**

- **Swing detection regression:** A fixed set of 50+ known candle sequences with expected swing outputs. If any expected swing is missing or a phantom swing appears, the build fails.
- **Signal evaluation regression:** Known market scenarios with expected signal outcomes (TAKEN/REJECTED/FILTERED) for each strategy. Any change in signal output requires explicit acknowledgment.
- **Scoring regression:** Known inputs with expected scores. Score changes are flagged for review.
- **Filter regression:** Each filter tested against known pass/fail cases.

These regression fixtures are "golden files" — they change only when we intentionally modify strategy logic, and those changes require a PR description explaining why.

### 15.3 Pre-Merge Requirements

Before any PR can merge to `develop`:
- All unit tests pass
- All integration tests pass
- No linting errors (ruff)
- Type checking passes (mypy) — stretch goal
- At least the PR description explains what changed and why

Before merging `develop` to `main`:
- All of the above
- Manual review by Robin
- For strategy changes: backtest comparison showing no regression

---

## 16. COST ANALYSIS

### Current Monthly Cost

| Item | Cost |
|------|------|
| Hetzner VPS | €7.50 |
| Supabase (2x free tier) | €0 |
| TwelveData (free tier) | €0 |
| Claude Pro subscription | ~€20 |
| Discord | €0 |
| **Total** | **~€27.50/month** |

### Projected Additional Costs

| Item | Cost | When |
|------|------|------|
| GitHub (private repo, free tier) | €0 | Phase M0 |
| Claude Max (for Claude Code heavy use) | ~€100/month | Optional, during heavy migration |
| Supabase Pro (if exceeding 500MB) | ~€25/month | When scaling to multiple pairs |
| Domain name (if adding web dashboard) | ~€10/year | Future |

The migration itself adds minimal ongoing cost. The primary investment is Robin's time.

---

## 17. RISK REGISTER

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Migration breaks live trading | Medium | High | Parallel running during M5. Old system stays active until new is proven. |
| Scope creep on migration | High | Medium | Phase gates with clear deliverables. No phase starts until previous is complete. |
| Python implementation differs from SQL | Medium | High | Exhaustive comparison tests. Output must match within tolerance. |
| Context limits with Claude Code on large codebase | Medium | Low | Proper CLAUDE.md + modular design keeps relevant context small. |
| Robin loses motivation during long migration | Medium | High | Each phase delivers standalone value. Paper trading continues throughout. |
| Supabase free tier limits reached during migration | Low | Medium | Data retention policy. Monitor size weekly. |
| TwelveData API changes or goes paid | Low | Medium | Anti-corruption layer means only adapter changes. |

---

## 18. SUCCESS CRITERIA

The migration is considered successful when:

1. **All three strategies produce identical signals** through the Python engine vs. the current SQL engine (verified over a 2-week parallel run)
2. **Test coverage exceeds 85%** on domain logic
3. **The "rebuild from Git" test passes** — fresh clone, run setup, all tests pass, system starts
4. **Adding a new pair takes < 1 hour** — just configuration, no code changes
5. **Every function has a docstring and type hints** — enforced by CI
6. **The January 23 swing detection bug is fixed and has a regression test**
7. **Monthly re-validation runs automatically** and produces a report
8. **Robin can describe the system architecture** to someone else using the diagrams and documentation in this blueprint

---

## 19. OPEN QUESTIONS

Items that need decisions before or during migration:

1. **GitHub account:** Personal or organization? Free tier sufficient?
2. **Claude Code subscription level:** Pro ($20) or Max ($100) for heavy development?
3. **Docker on Hetzner:** Is the VPS powerful enough to run Python + FastAPI alongside N8N?
4. **Broker API selection:** When we move to live trading, which broker? This affects the execution domain design.
5. **Web dashboard:** Do we want one eventually? If yes, React + Supabase (Lovable pattern) or Python-based (Dash/Streamlit)?
6. **Multi-agent framework tool:** Stick with Claude Code custom commands, or evaluate CrewAI/LangGraph for more complex orchestration?
7. **Research database consolidation timing:** Migrate research DB to same repo, or keep separate?

---

## 20. NEXT STEPS

1. **Robin reviews this blueprint** — add, remove, or modify anything
2. **Finalize open questions** (section 19)
3. **Create Mermaid diagrams** for system architecture, domain model, and migration flow
4. **Start Phase M0** — set up GitHub repo and project skeleton
5. **Add this blueprint to Claude project knowledge** as the architectural north star

---

## CHANGELOG

| Date | Version | Change |
|------|---------|--------|
| 2026-02-26 | 1.0 | Initial blueprint created from brainstorming sessions |

---

*Document: FA_MODERNIZATION_BLUEPRINT.md*
*Project: Fractal AI*
*"Build it right, scale it wide."*

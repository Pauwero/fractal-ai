# Fractal AI — Systematic Forex Trading Platform

## Overview

Fractal AI is a systematic forex trading system that detects market structure
patterns (swings, levels, CISDs) and evaluates them against configured strategy
rules to generate trading signals. Currently monitors EURUSD and GBPUSD with three active
strategies: FTLR-v2, CISD-v3, and S-SCALP-v3.

## Tech Stack

- **Language:** Python 3.11+
- **API:** FastAPI
- **Testing:** pytest
- **Database:** PostgreSQL (Supabase)
- **Automation:** N8N (self-hosted on Hetzner VPS)
- **Alerting:** Discord webhooks
- **Containers:** Docker + Docker Compose
- **CI/CD:** GitHub Actions
- **Linting:** ruff
- **Type checking:** mypy (stretch goal)

## Architecture

Domain-Driven Design with 6 bounded contexts:

```
Market Data → Structure Detection → Strategy Logic → Trade Execution
                                                          ↑
                    Research ←──────────────────────────────┘
                    Observability (cross-cutting)
```

See `docs/architecture/BLUEPRINT.md` for full details and Mermaid diagrams.

## Project Structure

```
fractal-ai/
├── CLAUDE.md                 # This file — AI agent context
├── claude-progress.txt       # Multi-session progress tracking
├── features.json             # Feature/task tracking
├── pyproject.toml            # Dependencies and metadata
├── docker-compose.yml        # Container orchestration
├── .env.example              # Environment variable template
├── config/                   # All configuration (strategies, tolerances, sessions, pairs)
│   └── strategies/           # One JSON per strategy
├── src/                      # Source code
│   ├── domain/               # Business logic (6 bounded contexts)
│   │   ├── market_data/      # Candle ingestion, validation, storage
│   │   ├── structure/        # Swing, level, pattern, CISD detection
│   │   ├── strategy/         # Config-driven signal evaluation engine
│   │   ├── execution/        # Trade lifecycle, risk management
│   │   ├── research/         # Hypothesis testing, backtesting
│   │   └── observability/    # Logging, metrics, health checks, alerting
│   ├── api/                  # FastAPI endpoints
│   ├── events/               # Domain event bus
│   └── infrastructure/       # DB connections, external API clients, config loading
├── tests/                    # pytest test suite
│   ├── unit/                 # Fast, isolated tests
│   ├── integration/          # Tests requiring DB or external services
│   └── fixtures/             # Real market data with verified expected outputs
├── migrations/               # Numbered SQL migration files
├── n8n/                      # N8N workflow JSON exports
├── scripts/                  # CLI tools (backtest, validate, deploy)
└── docs/                     # Documentation
    ├── GLOSSARY.md           # Ubiquitous language — the single vocabulary
    ├── FA_STATE.md           # Current project status
    ├── strategies/           # Strategy playbooks
    └── architecture/         # Blueprint + Mermaid diagrams
```

## Commands

```bash
# Testing
python -m pytest                        # Run all tests
python -m pytest tests/unit/ -v         # Run unit tests only
python -m pytest tests/integration/ -v  # Run integration tests
python -m pytest --cov=src              # Run with coverage

# Development
python -m src.api.main                  # Start FastAPI server
ruff check src/ tests/                  # Lint
ruff format src/ tests/                 # Format

# Scripts
python scripts/backtest.py              # Run backtesting
python scripts/validate.py              # Monthly re-validation
```

## Code Patterns

### Required on all functions
- Type hints on all parameters and return values
- Google-style docstrings on all public functions
- No magic numbers — use config files or named constants

### Domain entities
- Use Pydantic models (`src/domain/*/models.py`)
- Immutable where possible (frozen=True)

### Strategy logic
- Configuration-driven (see `config/strategies/`)
- The engine interprets config; no strategy-specific hardcoded logic in engine.py

### Testing
- Write tests BEFORE implementation (TDD)
- Fixtures use real market data (`tests/fixtures/`)
- Coverage target: 90% domain logic, 80% infrastructure

## Key Conventions

| Convention | Correct | Wrong |
|-----------|---------|-------|
| Pair format | `"EURUSD"` | `"EUR/USD"`, `"eurusd"` |
| Timeframe format | `"1H"` | `"1h"`, `"60"`, `"60m"` |
| Swing types | `"HIGH"`, `"LOW"` | `"high"`, `"swing_high"` |
| Closure types | `"C2_CLOSURE"`, `"C3_CLOSURE"` | `"c2_close"`, `"C2"` |
| Validation types | `"IN_SAMPLE"`, `"OUT_OF_SAMPLE"`, `"WALK_FORWARD"`, `"LIVE"` | |
| Session names | `"ASIA"`, `"LONDON"`, `"NY"` | `"asian"`, `"london"` |
| Risk tiers | `"BASE"`, `"STANDARD"`, `"STRONG"`, `"PREMIUM"` | |

See `docs/GLOSSARY.md` for the complete ubiquitous language.

## Current State

See `docs/FA_STATE.md` for live project status.
See `claude-progress.txt` for recent session history.

## Active Strategies

| Strategy | Version | Key Metric (2R WR) | Validation | Status |
|----------|---------|---------------------|-----------|--------|
| FTLR | v2.0 | 59.5% (n=74) | IN_SAMPLE (2025) | Monitoring |
| CISD | v3.0 | 68.1% (n=144) | OUT_OF_SAMPLE (2025) | Forward testing |
| S-SCALP | v3.0 | 68.8% (n=27 OOS) | OUT_OF_SAMPLE (2025-2026) | Forward testing |

## Database Architecture

| Database | Purpose | Supabase Project |
|----------|---------|------------------|
| Fractal AI | Production/Live trading | `eooqdkupnrgknstjvkwc` |
| The Beacon Robin | Research/Historical analysis | `hdtpvlyofjevvoerculm` |

## What NOT to Do

- Never hardcode pair or timeframe in domain logic — always parameters
- Never put business logic in N8N workflow nodes
- Never deploy SQL directly to Supabase — use migration files
- Never commit secrets or .env files
- Never merge to main without passing tests
- Never call a finding "validated" if tested on discovery data — that's IN_SAMPLE
- Never trust a win rate without stating sample size and validation type

## Research Pipeline

The `.claude/agents/` directory contains 6 research pipeline agents.
Start with: `/research "your hypothesis or question"`
Continue with: `/continue`
The SubagentStop hook guides you through each step.

### Pipeline Flow
```
[1] Research Analyst → [2] Devil's Advocate → GATE 1
→ [3] Quant Analyst → [4] Statistical Auditor → GATE 2
→ [5] Synthesizer (Opus) → [6] Rule Formulator → GATE 3
```

### Database Access
Supabase MCP is configured for two databases:
- **The Beacon Robin** (research): `hdtpvlyofjevvoerculm` — use for ALL analysis
- **Fractal AI** (production): `eooqdkupnrgknstjvkwc` — DO NOT modify during research

### Research Conventions
- Hypotheses: H-XXX, Questions: Q-XXX, Findings: F-XXX
- Conclusions: C-XXX, Rules: R-XXX, Strategies: S-NAME-vX
- Pipeline state tracked in `.claude/pipeline/queue.json`
- Artifacts in `.claude/pipeline/runs/RUN-XXX/`
- Agent memory in `.claude/agent-memory/<agent-name>/MEMORY.md`

### Research Rules
1. Never modify production database during research
2. Every finding must record validation_type honestly
3. Record ALL findings including neutral/contradicting ones
4. Human gates must be respected (steps 2→3 and 4→5)
5. Pre-register hypotheses BEFORE any data analysis (confirmatory sessions)
6. North Star metrics evaluated for every actionable conclusion

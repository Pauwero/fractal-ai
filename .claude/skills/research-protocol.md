# Research Protocol — Fractal AI

## The North Star
Find strategies with the largest potential **net R per year**.
- Minimum: 100 trades/year (statistical relevance + psychological sustainability)
- Minimum: 60% win rate (psychological sustainability for manual execution)
- All findings must be honest about validation type

## Research Knowledge Chain
```
HYPOTHESIS → QUESTIONS → FINDINGS → CONCLUSIONS → RULES → STRATEGY
                                                        ↑
                                    VALIDATIONS ────────┘
```

## ID Conventions
| Table | Format | Example |
|-------|--------|---------|
| Hypotheses | H-001 | H-012: "Trend alignment improves FTLR WR" |
| Questions | Q-001 | Q-128: "What is WR with trend filter?" |
| Findings | F-001 | F-210: "Trend-aligned WR 72.1% (n=43)" |
| Conclusions | C-001 | C-016: "Trend filter helps WR but hurts frequency" |
| Rules | R-001 | R-029: "FTLR Trend Alignment Scoring Factor" |
| Strategies | S-NAME-vX | S-FTLR-v2, S-CISD-v3, S-SCALP-v3 |

To get next ID: `SELECT id FROM research_[table] ORDER BY id DESC LIMIT 1;`

## Validation Type Definitions (BE HONEST)
| Type | Definition | Trust Level |
|------|-----------|-------------|
| IN_SAMPLE | Found AND tested on same data | ⚠️ Suggestive only |
| OUT_OF_SAMPLE | Tested on data NOT used to discover it | ✅ Stronger |
| WALK_FORWARD | Tested on sequential unseen periods | ✅✅ Strong |
| LIVE | Confirmed in real trading | ✅✅✅ Proven |

**Current reality:** Almost all FTLR findings are IN_SAMPLE (2025 data).
CISD v3 has some OUT_OF_SAMPLE (2025 discovery, early 2026 validation).
S-SCALP v3 has 7 weeks OOS on 2026 data.

## Session Types
- **EXPLORATORY:** Open-ended investigation. No pre-registration needed.
  Findings flagged as lower evidence weight.
- **CONFIRMATORY:** Tests a specific prediction. REQUIRES pre-registered
  hypothesis with predicted_outcome + invalidation criteria BEFORE any SQL.

## Critical Anti-Overfitting Rules
From Lopez de Prado (2018) and Bailey et al. (2014):
1. Do not backtest until research design is complete
2. Track ALL variations tested (prevents p-hacking)
3. Record neutral/contradicting findings (prevents confirmation bias)
4. With 5 years of daily data, no more than ~45 strategy variations
   should be tested before overfitting risk becomes severe
5. A strategy that works IN_SAMPLE but not OUT_OF_SAMPLE is not a strategy
6. The better you become at backtesting, the MORE likely false discoveries
7. Always ask: "Could random data explain this result?"

## Finding Recording Requirements
Every finding MUST include:
- `validation_type` (honestly assessed)
- `sample_size` (flag if n < 30)
- `sql_used` (exact, reproducible query)
- `data_start` and `data_end` (explicit date range)
- `direction` (SUPPORTING / CONTRADICTING / NEUTRAL)

## North Star Evaluation Template
For every actionable conclusion, evaluate:
- **Trades per year:** Does the filter/rule maintain ≥100 trades/year?
- **Win rate:** Does the WR remain ≥60%?
- **Net R projection:** What is the estimated net R impact per year?
- **Max consecutive losses:** Is the losing streak psychologically sustainable?
- **Binding constraint:** Which North Star metric is the bottleneck?

## Current Strategies Under Research
| Strategy | Trades | WR @2R | Net R | Validation | Status |
|----------|--------|--------|-------|------------|--------|
| FTLR v2.0 | 74 | 59.5% | +326R | IN_SAMPLE 2025 | Research |
| CISD v3.0 | 144 | 68.1% | +168R @3R | OUT_OF_SAMPLE | Production |
| S-SCALP v3.0 | 287 IS / 27 OOS | 65.9%/70.4% | +329.5R weighted | IN_SAMPLE + 7wk OOS | Validated |

## Monthly Re-Validation (First Weekend Each Month)
1. Pull all ACTIVE rules and KEY_INSIGHT conclusions
2. Re-run stored SQL against latest data
3. Compare current vs original values
4. Flag deviations > 15%
5. Log to research_validations table

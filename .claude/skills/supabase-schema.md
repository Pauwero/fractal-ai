# Supabase Schema Reference — Fractal AI

## Database Architecture
| Database | Project Ref | Purpose |
|----------|-------------|---------|
| The Beacon Robin | hdtpvlyofjevvoerculm | Research/Historical (364 MB) |
| Fractal AI | eooqdkupnrgknstjvkwc | Production/Live (36 MB) — DO NOT MODIFY |

**All research queries go to The Beacon Robin.**

## Key Research Tables

### research_swings (~36K rows)
Detected swing highs and lows across pairs and timeframes.
Key columns: id, pair, timeframe, swing_time, swing_price, swing_type (HIGH/LOW),
c2_closure_confirmed, c3_closure_confirmed, c1_time, c2_time, c3_time,
body_pips, wick_pips, swing_strength, reversal_pattern

### research_key_levels_detailed (~8.6K rows)
Session highs/lows, daily/weekly levels.
Key columns: id, pair, level_type, level_price, level_time, session_name,
formation_timeframe, touch_count, sweep_count

### research_price_interactions (~3.7K rows)
How price interacts with key levels (touches, sweeps, breaches).
Key columns: id, level_id, interaction_type (TOUCH/SWEEP/BREACH),
interaction_time, interaction_price, wick_beyond_pips

### research_cisd_events (~5.3K rows)
Change in State of Delivery events.
Key columns: id, pair, timeframe, cisd_time, direction, series_number,
c3_displacement_pips, body_risk_pips, is_aligned_with_c2

### research_fvg_events (~7.7K rows)
Fair Value Gaps detected.
Key columns: id, pair, timeframe, fvg_time, direction, gap_size_pips

### ohlc_candles (~229K rows)
Raw OHLC data across multiple timeframes.
Key columns: pair, timeframe, candle_time, open, high, low, close, volume
Timeframes: 5M, 15M, 1H, 4H, D, W
Date range: 2025-01-01 to present

### research_trades (~284 rows)
Research-validated trade setups.
Key columns: id, strategy_id, pair, direction, entry_time, entry_price,
sl_price, tp1_price, tp2_price, result_1r, result_2r, result_3r,
signal_score, trade_quality_tier

### Research Knowledge Chain Tables
- research_hypotheses: id, title, predicted_outcome, invalidation, strategy_id, status
- research_questions: id, hypothesis_id, question, intent (CONFIRMATORY/ADVERSARIAL/EXPLORATORY), status
- research_findings: id, question_id, hypothesis_id, title, description, direction, sample_size, metric_name, metric_value, metric_unit, validation_type, data_start, data_end, sql_used
- research_conclusions: id, title, confidence, significance, is_validated, supporting_finding_ids, contradicting_finding_ids
- research_rules: id, name, strategy_id, rule_type, condition_sql, impact_description, validation_type, status
- research_strategies: id, name, description, version, status
- research_validations: id, target_type, target_id, validation_date, original_value, current_value, deviation_pct, still_valid

## Useful SQL Patterns

### Get next available ID for any research table
```sql
SELECT COALESCE(
  MAX(CAST(SUBSTRING(id FROM '[0-9]+') AS INTEGER)) + 1,
  1
) as next_num
FROM research_hypotheses;
```

### Check existing hypotheses (avoid duplicates)
```sql
SELECT id, title, status, predicted_outcome
FROM research_hypotheses
WHERE status IN ('REGISTERED','INVESTIGATING','SUPPORTED','REFUTED')
ORDER BY id DESC LIMIT 20;
```

### Quick data availability check
```sql
SELECT pair, timeframe,
  MIN(candle_time) as earliest,
  MAX(candle_time) as latest,
  COUNT(*) as candle_count
FROM ohlc_candles
GROUP BY pair, timeframe
ORDER BY pair, timeframe;
```

### FTLR base query pattern (commonly used)
```sql
WITH ftlr_setups AS (
  SELECT t.*,
    s.swing_strength,
    s.c2_closure_confirmed,
    pi.interaction_type
  FROM research_trades t
  JOIN research_swings s ON t.swing_id = s.id
  LEFT JOIN research_price_interactions pi ON t.interaction_id = pi.id
  WHERE t.strategy_id = 'S-FTLR-v2'
)
SELECT ... FROM ftlr_setups;
```

## Performance Notes
- JOINs on ohlc_candles can be slow (229K rows) — use WHERE clauses on pair + timeframe first
- research_swings has indexes on (pair, timeframe, swing_time)
- Always include date range filters to limit scan scope

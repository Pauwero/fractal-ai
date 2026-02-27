# Database Migrations

## Conventions

- Files are numbered sequentially: `001_`, `002_`, etc.
- Each migration is idempotent (safe to re-run)
- Functions that remain in SQL follow domain prefixes:
  - `market_data_*` — candle ingestion, data validation
  - `structure_*` — swing, level, pattern detection
  - `strategy_*` — signal evaluation
  - `trade_*` — trade management
- Include both `UP` and `DOWN` sections where possible

## Running Migrations

Migrations are applied to Supabase via the SQL editor or automated scripts.
Never apply a migration to production without testing on a development branch first.

## File Format

```sql
-- Migration: 001_initial_schema
-- Date: YYYY-MM-DD
-- Description: Brief description of what this migration does

-- UP
CREATE TABLE IF NOT EXISTS ...;

-- DOWN
DROP TABLE IF EXISTS ...;
```

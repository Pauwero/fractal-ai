# N8N Workflows

## Overview

N8N handles scheduling and orchestration. Business logic lives in Python/FastAPI.
N8N calls FastAPI endpoints — it does NOT contain trading logic in workflow nodes.

## Folder Structure

```
n8n/
├── 1. Data Collection/     # Market data ingestion workflows
├── 2. Alert Processing/    # TradingView alert handling
├── 3. Monitoring/          # Trade lifecycle monitoring
├── 4. System Management/   # Health checks and error handling
└── 5. Strategies/          # Strategy signal evaluation
```

## Active Workflows

### 1. Data Collection

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| WF1 - OHLC Collector | `1. Data Collection/WF1 - OHLC Collector (7).json` | Every 5min Mon-Fri (`*/5 * * * 1-5`) | Fetch candle data from TwelveData; decides which timeframes to process based on market hours |
| WF2 - Daily Initializer | `1. Data Collection/WF2 - Daily Initializer (3).json` | Daily 17:05 UTC Mon-Fri (`5 17 * * 1-5`, after NY close) | Calculate daily bias, DOL & confluence from PDH/PDL/PWH/PWL/PMH/PML; upsert key levels and daily context to DB; send Discord summary |
| WF3 v2 - Session Tracker | `1. Data Collection/WF3 v2 - Session Tracker (14).json` | Asia Close 08:05, London Close 13:05, NY Close 22:05 UTC Mon-Fri | Record session OHLCs, detect sweeps, backfill missing 5M candles from TwelveData if needed |

### 2. Alert Processing

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| WF4 v1.4 - Alert Processor | `2. Alert Processing/WF4_v1.4 - Alert Processor (8).json` | Webhook (TradingView) + Manual | Receive TradingView alerts; enrich with OHLC, daily context, key levels, DXY, and recent alerts from DB; send Discord alert |
| WF5 v1.2 - DXY Correlation Tracker | `2. Alert Processing/WF5_v1.2 - DXY Correlation Tracker (7).json` | Two webhooks: DXY Alert + Confirmation | Track DXY structural alerts, correlate with pair alerts, update correlation records, send Discord notification |

### 3. Monitoring

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| Trade Monitor | `3. Monitoring/Trade Monitor (1).json` | Every 5min Mon-Fri (`*/5 * * * 1-5`) | Poll open trades, detect closures, send Discord close alert, log trade closure to DB, send account summary |

### 4. System Management

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| [CORE] Health Check | `4. System Management/[CORE] Health Check (1).json` | Every 2h Mon-Fri (`3 4,6,8,10,12,14,16,18,20 * * 1-5`) | System health monitoring across all pairs; EOD performance digest; Claude AI generates action items when flags detected |
| Error Handler | `4. System Management/Error Handler (2).json` | N8N Error Trigger (fired by other workflow failures) | Catch errors from any workflow, log to DB, send Discord alert |

### 5. Strategies

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| [CORE] Strategy Engine | `5. Strategies/[CORE] Strategy Engine (6).json` | Every 5min Mon-Fri 04:00–20:00 UTC (`3/5 4-20 * * 1-5`) | Evaluate strategy signals via FastAPI; send Discord alerts for forming signals, opened trades, closures, and counter signals; log all alerts to DB |

## Deployment

1. Export workflow JSON from N8N UI
2. Save to the appropriate subfolder in this directory
3. Commit to Git
4. To deploy: import JSON into N8N on Hetzner VPS

## Environment

- Self-hosted on Hetzner VPS (€7.50/month)
- Docker container alongside Caddy (SSL)
- Unlimited executions (no cloud tier limits)

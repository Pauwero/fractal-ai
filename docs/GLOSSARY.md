# Fractal AI — Glossary (Ubiquitous Language)

> **Purpose:** A consistent vocabulary used across all code, documentation, database columns, and conversations.
> This is non-negotiable — every contributor (human or AI) must use these exact terms.

---

## Market Data Terms

| Term | Definition | Code Convention |
|------|-----------|-----------------|
| **Candle** | A single OHLC price bar for a specific timeframe | `candle`, `Candle` |
| **Pair** | A currency pair (e.g., EURUSD) | `pair: str` — always uppercase, no slash |
| **Timeframe** | The candle period (e.g., 5M, 1H, 4H, D) | `timeframe: str` — uppercase with unit |
| **Session** | A trading session: ASIA, LONDON, NY | `session: str` — uppercase |
| **Pip** | Minimum price increment (0.0001 for majors) | `pips: float` |

## Structure Terms

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

## Strategy Terms

| Term | Definition | Code Convention |
|------|-----------|-----------------|
| **Signal** | A strategy's determination that conditions are met | `signal`, `Signal` |
| **Filter** | A pass/fail condition in signal evaluation | `filter`, `Filter` |
| **Score** | A 0-100 quality rating for a signal | `score: int` |
| **Risk Tier** | Position sizing tier based on score | `risk_tier: str` (BASE/STANDARD/STRONG/PREMIUM) |
| **R** | Risk unit — the distance from entry to stop loss | `r_value: float` |
| **Target (xR)** | Take profit as multiple of R | `target_r: int` (e.g., 2 for 2R) |
| **Win Rate** | Percentage of trades hitting target | `win_rate: float` — always specify which R target |

## Trade Terms

| Term | Definition | Code Convention |
|------|-----------|-----------------|
| **Trade** | A monitored position from entry to close | `trade`, `Trade` |
| **Entry** | The price and time a trade opens | `entry_price`, `entry_time` |
| **Stop Loss** | The maximum loss price | `stop_loss: float` |
| **Take Profit** | The target price | `take_profit: float` |
| **Outcome** | WIN, LOSS, EXPIRED, CANCELLED | `outcome: str` |
| **P&L** | Profit and loss in account currency | `pnl: float` |
| **Result R** | Outcome expressed in R multiples | `result_r: float` |

## Research Terms

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

*Document: docs/GLOSSARY.md*
*Project: Fractal AI*

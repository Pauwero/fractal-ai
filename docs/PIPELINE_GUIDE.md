# Fractal AI — Research Pipeline Guide

## Quick Start

### Start a new research investigation
```
/research "Does trend alignment (1H market structure direction) improve FTLR v2.0 win rate at 2R target?"
```

### Continue after reviewing a gate
```
/continue
```

## How the Pipeline Works

The research pipeline runs 6 specialist agents in sequence, with human review gates at key decision points.

### Pipeline Steps

| Step | Agent | What It Does | Next |
|------|-------|-------------|------|
| 1 | **Research Analyst** | Classifies intent (EXPLORATORY/CONFIRMATORY), registers hypothesis with predictions + invalidation criteria | Auto-chains to Step 2 |
| 2 | **Devil's Advocate** | Generates adversarial questions to break the hypothesis, designs all SQL queries | **GATE 1** |
| 3 | **Quant Analyst** | Executes approved queries, records all findings (supporting + contradicting + neutral) | Auto-chains to Step 4 |
| 4 | **Statistical Auditor** | Validates statistical rigor, runs adversarial queries, checks outliers/CIs/temporal stability | **GATE 2** |
| 5 | **Synthesizer** (Opus) | Weighs all evidence, produces conclusions with North Star assessment, cross-pollinates across strategies | Auto-chains to Step 6 if actionable |
| 6 | **Rule Formulator** | Converts actionable conclusions into implementable trading rules with exact SQL | **GATE 3** |

### Human Gates

**Gate 1** (after Step 2): Review hypothesis framing + query plan before any data is queried.
- Check: Is the hypothesis well-framed? Are adversarial questions thorough? Are queries correct?
- Review file: `.claude/pipeline/runs/RUN-XXX/02-challenge-and-queries.json`

**Gate 2** (after Step 4): Review ALL evidence before conclusions are drawn.
- Check: Are findings honest? Did adversarial challenges reveal problems? Are sample sizes adequate?
- Review files: `.claude/pipeline/runs/RUN-XXX/03-findings.json` + `04-statistical-audit.json`

**Gate 3** (after Step 6): Review proposed trading rules before they enter the knowledge base.
- Check: Are rules implementable? Is OOS validation planned? Any conflicts with existing rules?
- Review file: `.claude/pipeline/runs/RUN-XXX/06-rules.json`

### Auto-Chain Rules
- Steps 1 → 2: Research Analyst auto-chains to Devil's Advocate (no gate between them)
- Steps 3 → 4: Quant Analyst auto-chains to Statistical Auditor
- Steps 5 → 6: Synthesizer auto-chains to Rule Formulator IF conclusions are actionable
- All other transitions require your explicit `/continue`

## Reviewing Artifacts

Each pipeline run creates a directory at `.claude/pipeline/runs/RUN-XXX/` containing:

```
RUN-001/
├── 01-research-brief.json          ← Hypothesis framing
├── 02-challenge-and-queries.json   ← Questions + SQL query plan
├── 03-findings.json                ← All query results as formal findings
├── 04-statistical-audit.json       ← Statistical validation + adversarial results
├── 05-synthesis.json               ← Conclusions + North Star assessment
└── 06-rules.json                   ← Proposed trading rules (if actionable)
```

The pipeline state is tracked in `.claude/pipeline/queue.json`. This file shows the current status of each step (PENDING, READY, IN_PROGRESS, COMPLETE, PENDING_HUMAN_REVIEW, SKIPPED).

## Agent Memory

Each agent accumulates domain-specific wisdom across pipeline runs in `.claude/agent-memory/<agent-name>/MEMORY.md`. This is injected into the agent's context automatically.

Memory locations:
- `.claude/agent-memory/research-analyst/MEMORY.md`
- `.claude/agent-memory/devils-advocate/MEMORY.md`
- `.claude/agent-memory/quant-analyst/MEMORY.md`
- `.claude/agent-memory/statistical-auditor/MEMORY.md`
- `.claude/agent-memory/synthesizer/MEMORY.md`
- `.claude/agent-memory/rule-formulator/MEMORY.md`

Agents update their own memory after each run. Over time, they learn:
- Common pitfalls for specific strategy types
- Effective adversarial questions
- Query optimization patterns
- Statistical patterns at various sample sizes
- Cross-strategy insights

## Database Access

All research queries run against **The Beacon Robin** (project ref: `hdtpvlyofjevvoerculm`).
The **Fractal AI** production database (`eooqdkupnrgknstjvkwc`) is NEVER modified during research.

## Troubleshooting

### Pipeline seems stuck
Check `.claude/pipeline/queue.json` to see the current state. Look for a step with status `PENDING_HUMAN_REVIEW` — that means a gate is waiting for your review.

### Hook not firing
Verify `.claude/settings.json` has both `SubagentStop` and `Stop` hooks configured pointing to `.claude/hooks/on-pipeline-step.sh`.

### Agent can't find artifacts
Ensure the run directory exists at `.claude/pipeline/runs/RUN-XXX/` and previous agents wrote their output files.

### Query fails
The quant-analyst logs query errors as NEUTRAL findings. Check the findings artifact for error details. Common issues: wrong column names (verify schema), missing date range filters, or timeout on large JOINs.

### Want to restart a pipeline
Delete or rename `.claude/pipeline/queue.json` and start fresh with `/research "..."`.

### Want to skip to a specific step
Manually edit `.claude/pipeline/queue.json` — set the desired step to `READY` and all previous steps to `COMPLETE`.

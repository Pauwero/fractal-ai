Continue the research pipeline from where it left off.

## Steps:
1. Read pipeline/queue.json
2. Find the next step with status READY or PENDING_HUMAN_REVIEW that has been approved
3. If the next step status is PENDING_HUMAN_REVIEW, ask if Robin has reviewed and wants
   to proceed. If confirmed, update status to READY and continue.
4. Invoke the appropriate subagent for that step
5. If steps can auto-chain (no gate between them), continue to the next step
   automatically after the current one completes

## Auto-chain rules:
- After step 3 (quant-analyst) → auto-chain to step 4 (statistical-auditor)
- After step 5 (synthesizer) → auto-chain to step 6 (rule-formulator) IF actionable
- All other transitions require explicit /continue from Robin

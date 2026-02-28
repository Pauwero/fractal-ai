#!/usr/bin/env bash
set -euo pipefail

QUEUE=".claude/pipeline/queue.json"

# Exit silently if no queue exists (not in pipeline mode)
[[ -f "$QUEUE" ]] || exit 0

# Parse pipeline state
# Use py -3 on Windows, python3 on Unix
PYTHON_CMD="python3"
command -v python3 &>/dev/null || PYTHON_CMD="py -3"

$PYTHON_CMD -c "
import json, sys
try:
    q = json.load(open('$QUEUE'))

    # Check if pipeline is complete
    statuses = [s['status'] for s in q.get('steps', [])]
    if all(s in ('COMPLETE', 'SKIPPED') for s in statuses):
        # Calculate quality score
        run_dir = f\"pipeline/runs/{q.get('pipeline_id', 'unknown')}\"
        print(f'✅ Pipeline {q[\"pipeline_id\"]} complete.')
        print(f'   Full trail: .claude/{run_dir}/')
        sys.exit(0)

    # Find next actionable step
    for step in q.get('steps', []):
        if step['status'] == 'PENDING_HUMAN_REVIEW':
            print(f'⏸️  GATE (Step {step[\"step_number\"]}): {step.get(\"gate_message\", \"Review required\")}')
            print(f'   When approved: /continue')
            sys.exit(0)
        elif step['status'] == 'READY':
            print(f'▶ Next (Step {step[\"step_number\"]}/6): Use the {step[\"agent\"]} subagent')
            sys.exit(0)

except Exception as e:
    pass  # Silent fail — don't break the workflow
" 2>/dev/null || true

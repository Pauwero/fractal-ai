Start a new research pipeline for: $ARGUMENTS

## Steps:
1. Create a new run directory: pipeline/runs/RUN-XXX/
   (get next run number by counting existing directories)
2. Initialize pipeline/queue.json with the new pipeline_id and all steps set to PENDING,
   except step 1 set to READY
3. Use the research-analyst subagent to classify and register the hypothesis:
   "$ARGUMENTS"
4. After the research-analyst completes, immediately use the devils-advocate subagent
   to generate adversarial questions and design queries
5. Stop at Gate 1 — present the summary and wait for Robin to /continue

# Stage generation rules

## Initialization

Read the current XDPai task/requirement context using the XDPai skill. Populate init.json with the actual requirement identity and description. Do not ask the SOP prompt to carry the full requirement text.

## Understanding

Read the requirement context actively.

Generate only understanding.json:
- business/user goal;
- included and excluded scope;
- affected frontend/backend modules;
- assumptions;
- review items that materially affect later planning.

Identify repositories from actual context/tools. Unknown repository → empty string, not a guess.

If understanding is edited later, downstream stage JSON is not rewritten here; mark downstream stages stale through init when possible.

## Breakdown

Read:
- init.json;
- understanding.json;
- requirement context when necessary.

Generate only breakdown.json.

Use understanding.modules[].id as module_id. Break work into executable tasks. Dependencies express true blocking order, not mere relation.

Do not generate effort, confidence, assignee, or dates.

## Estimation

Read:
- breakdown.json;
- understanding.json if assumptions/review answers affect complexity.

Generate only estimation.json.

For each breakdown task, create exactly one estimation. Use concrete sub-effort components whose sum equals effort_days. Lower confidence when unresolved information can materially affect effort.

Do not change task definitions.

## Scheduling

Read:
- breakdown.json;
- estimation.json;
- actual team/capacity/calendar context available through XDPai or related skills.

Generate only scheduling.json.

Create exactly one schedule item per task. Respect dependencies and parallelism. Do not invent real assignees. Compute critical path from dependency/schedule impact.

Do not change task definitions or effort estimates.

## Human edits

A stage node must preserve upstream human edits exactly as read.

If the current stage JSON already exists and contains human edits, change only fields necessary to satisfy the current new input. Never rebuild unrelated rows just for stylistic consistency.

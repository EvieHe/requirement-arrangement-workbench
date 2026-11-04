---
name: requirement-arrangement-planner
description: Generate and update structured requirement evaluation data for the requirement-arrangement workbench. Use when an agent must turn a software requirement into the workbench's four-stage planning state: requirement understanding, task breakdown, effort estimation, and scheduling; generate human review questions; or revise the planning JSON after human edits while preserving page compatibility.
---

# Requirement Arrangement Planner

Generate a single planning-state JSON that the requirement-arrangement workbench can render and edit.

## Required workflow

Run the stages in order:

1. **understanding** — understand goal, scope, out-of-scope, affected frontend/backend modules, assumptions, and review questions.
2. **breakdown** — create executable frontend/backend/other tasks and dependencies.
3. **estimation** — assign person-day estimates, confidence, and concrete estimate basis to every task.
4. **scheduling** — assign owner, start/end dates, and critical path while respecting dependencies.

Each stage reads the latest state produced by previous stages. Human edits are authoritative inputs to later stages; do not silently overwrite them.

## Before generating

Read:
- `references/output-contract.md` for the exact field contract and invariants.
- `references/stage-generation.md` for how to derive each stage from requirement context and human edits.
- `references/planning-result.template.json` for the exact output shape.

If modifying an existing planning state, preserve stable IDs whenever the same module/task/review item still exists.

## Output rules

Return **only valid JSON** when the caller asks for machine-consumable planning data.

Use exactly these top-level keys:

`schema_version`, `requirement`, `evaluation`, `tasks`, `revision`.

The current schema version is `3.2`.

### Understanding

Generate:
- goal
- scope
- out_of_scope
- modules
- assumptions
- review_items

For `modules`, always distinguish `frontend` and `backend`. Each module must include:
- stable `id`
- `side`
- `name`
- `repository`
- one-sentence `change_summary`

Do not invent repository names if they are unknown. Use an empty string and create a review item requesting the repository/module mapping when needed.

Review items support:
- `choice`: options plus optional custom answer
- `text`: free-form human answer

Only ask questions that can materially change scope, tasks, effort, or scheduling.

### Breakdown

Generate tasks in the shared top-level `tasks` array.

Each task must have:
- stable ID
- title
- category: `frontend`, `backend`, or `other`
- description
- dependencies

Task IDs should normally use `FE-XX`, `BE-XX`, and `QA-XX`/other clear prefixes.

Include implementation, integration, and validation work needed for a deployable result. Do not create fake work merely to make the plan look complete.

### Estimation

For every task set:
- `effort_days` > 0
- `confidence`: `high`, `medium`, or `low`
- `estimate_basis`: concrete sub-effort or complexity reasons

The sum of task effort must equal `evaluation.stages.estimation.output.total_effort_days`.

Confidence buckets in the estimation output must exactly match task confidence.

Never express false precision. If important unknowns remain, lower confidence and surface them in review items rather than fabricating certainty.

### Scheduling

For every task set:
- `assignee`
- `start_date`
- `end_date`

Use ISO dates `YYYY-MM-DD`.

A task may not start before any dependency finishes. If capacity/assignee information is not provided, use role-level placeholder names such as `前端待分配` rather than inventing real people.

Set:
- start_date
- delivery_date
- estimated_working_days
- critical_path

Critical-path IDs must reference existing tasks.

## Human edits and regeneration

When a user edits modules, tasks, estimates, owners, dates, or review answers:

1. Treat the edited value as authoritative.
2. Update affected downstream stage outputs.
3. Recompute totals and confidence buckets.
4. Recheck dependencies and schedule.
5. Append a concise change record under `revision.changes`.
6. Increment `revision.version`.

Do not erase unrelated human edits.

## Validation

Before returning or saving JSON, run:

```bash
python3 scripts/validate_planning_result.py <planning-result.json>
```

Fix every validation error before completion. Warnings may remain only when they represent intentional unresolved human-review items.

For detailed invariants and field definitions, read `references/output-contract.md`.
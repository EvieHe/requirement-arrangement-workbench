---
name: requirement-arrangement-planner
description: Generate and validate stage-specific JSON for the requirement-arrangement workbench. Use when an agent must produce one of the four requirement-planning stages—requirement understanding, task breakdown, effort estimation, or scheduling—or initialize the shared requirement metadata. Each stage has its own JSON and references upstream data by requirement_id, module_id, and task_id.
---

# Requirement Arrangement Planner

The workbench uses **five independent JSON documents**:

1. `init.json` — requirement metadata and stage status.
2. `understanding.json` — requirement understanding tab.
3. `breakdown.json` — task breakdown tab.
4. `estimation.json` — effort estimation tab.
5. `scheduling.json` — scheduling tab.

Do not generate one giant planning JSON.

## Before generating

Read:
- `references/output-contract.md` for exact schemas and cross-file invariants.
- `references/stage-generation.md` for how to derive each stage.
- `references/task-ownership.md` for module/service ownership and assignable task boundaries.
- the corresponding template in `references/templates/`.

## Stage ownership

Each AI node writes **only its own stage JSON**.

- understanding node → `understanding.json`
- breakdown node → `breakdown.json`
- estimation node → `estimation.json`
- scheduling node → `scheduling.json`

`init.json` is initialized once and may be updated only for requirement metadata or stage status.

Never overwrite upstream JSON from a downstream stage.

## Task granularity

A breakdown task is the smallest **assignable ownership/delivery unit**, not a list of implementation steps.

Default rule:
- one affected service or independently owned business module → one task;
- multiple changes inside the same service/module stay in that task;
- use `work_items[]` (when useful) and `description` to preserve internal change details;
- split one module into multiple tasks only when there is a real ownership or delivery boundary, such as different owners, different repositories, or independently deliverable work;
- merge small related changes when they share the same module/service and owner;
- cross-module integration/QA may remain a separate task with `module_id = null`.

Do not create separate tasks merely because there are multiple APIs, pages, UI states, CRUD actions, or implementation steps inside the same module.

When a module boundary is unresolved by a required review item, avoid inventing a permanent standalone task. Mark the uncertainty clearly in the task description/work_items or keep the task provisional until the boundary is known.

This rule is intentionally aligned with downstream task-assignment behavior: breakdown should already be close to the units that can be assigned to owners.

## Cross-stage references

Use stable IDs:

- `understanding.modules[].id` → `breakdown.tasks[].module_id`
- `breakdown.tasks[].id` → `estimation.estimations[].task_id`
- `breakdown.tasks[].id` → `scheduling.schedule[].task_id`
- `breakdown.tasks[].id` → task dependencies and scheduling critical path

Do not duplicate full module/task objects downstream.

## Human edits

Human edits are authoritative.

If an upstream stage changes, downstream documents may become stale. Do not silently mutate downstream stage JSON from the current node. Instead:
1. write the current stage JSON;
2. mark downstream stages `stale` in `init.stage_status` when the runtime supports updating init;
3. let the corresponding downstream SOP nodes regenerate their own JSON.

## Output

When the caller asks for machine-consumable stage data, return only the JSON for the current stage.

Current schema version: `4.0`.

## Validation

Validate before writing a workflow variable.

Examples:

```bash
python3 scripts/validate_stage.py init init.json
python3 scripts/validate_stage.py understanding understanding.json --init init.json
python3 scripts/validate_stage.py breakdown breakdown.json --init init.json --understanding understanding.json
python3 scripts/validate_stage.py estimation estimation.json --init init.json --breakdown breakdown.json
python3 scripts/validate_stage.py scheduling scheduling.json --init init.json --breakdown breakdown.json --estimation estimation.json
```

Fix all errors before writing the stage result to XDPai.
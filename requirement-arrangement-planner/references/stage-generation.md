# Stage generation rules

Use this reference when producing or regenerating stage data.

## 1. Understanding

### Inputs

Use all available requirement context:
- requirement title and description
- acceptance criteria
- linked product/spec text
- known frontend/backend repositories or modules
- existing system constraints
- human answers from previous review items

### Derive goal

Write one sentence answering: **what outcome should be true for the user/business after this requirement ships?**

Do not put implementation details in the goal.

### Derive scope / out_of_scope

Scope should be capability-level, not task-level.

Good:
- 报名表单与提交
- 报名状态查询

Bad:
- 写一个 SubmitRegistration RPC
- 新增一个 React component

Only put something in out_of_scope when:
- the requirement explicitly excludes it, or
- a boundary is necessary to avoid a materially different implementation and the boundary is supported by context.

### Derive modules

Identify codebases that will actually change.

For each module:
1. classify frontend/backend;
2. use the real module name if known;
3. use a repository from context if known;
4. summarize the primary change in one sentence.

Do not infer a repository path from a module name. Unknown repository → empty string plus a review item if repository identity is needed for later work.

Prefer multiple precise modules over one vague “frontend” or “backend” module.

### Derive assumptions

Assumptions are temporary AI decisions made because the requirement is incomplete.

Only retain assumptions that can affect:
- scope;
- task breakdown;
- effort;
- dependencies;
- schedule.

### Derive review items

Create a review item when different answers would cause a meaningful planning change.

Use `choice` when a small set of expected answers exists.

Use `text` when:
- the answer space is open-ended;
- the user should describe a rule, constraint, or exceptional case.

For every question:
- state the current AI assumption;
- state the impact;
- do not ask information that can be derived from supplied context.

## 2. Breakdown

### Inputs

Read:
- understanding output;
- resolved review answers;
- affected modules;
- existing task edits that humans made.

### Task decomposition method

For each affected module, determine the minimal set of executable work items needed to deliver the requirement.

Typical categories:
- frontend UI/state/integration;
- backend API/domain/data changes;
- cross-module integration;
- validation or acceptance work.

A task should generally:
- have one primary delivery responsibility;
- be independently understandable;
- be small enough to estimate;
- be large enough to be managed as one work item.

Avoid:
- one task for the entire requirement;
- micro-tasks such as “add field”, “write one function” unless they are independently important;
- duplicating the same work under frontend and backend.

### Dependencies

Add a dependency only when task B cannot reasonably start before task A is complete.

Do not use dependencies merely to express that two tasks are related.

Keep the graph acyclic.

### Human edits

If a human adds, deletes, renames, recategorizes, or changes dependencies:
- preserve that edit;
- update `breakdown.output.task_ids`;
- mark downstream estimation and scheduling for recomputation.

## 3. Estimation

### Inputs

Read:
- final task list;
- task descriptions;
- affected modules;
- assumptions/review answers;
- known integration/testing burden.

### Estimate person-days

Estimate the **human engineering effort**, not calendar duration.

For every task, decompose the estimate into concrete components.

Examples:
- 页面结构 0.5d
- 状态与交互 0.5d
- 接口接入 0.5d
- 幂等与异常处理 0.5d
- 单测与自测 0.5d

Do not use:
- “复杂度较高”
- “参考经验”
- “常规开发”

unless accompanied by a concrete reason.

### Confidence

Use:
- `high`: scope and implementation path are clear; little material uncertainty.
- `medium`: some uncertainty or integration risk could change effort moderately.
- `low`: unresolved scope/architecture/dependency could materially change effort.

A required unresolved review item affecting a task normally prevents `high` confidence for that task.

### Reconcile

After estimating:
1. sum every task's `effort_days`;
2. write the sum to `total_effort_days`;
3. regenerate all three confidence buckets;
4. ensure every task belongs to exactly one bucket.

### Human edits

When a human changes effort/confidence/basis:
- preserve the edit;
- recompute totals/buckets;
- only revisit scheduling if the changed effort affects dates/capacity.

## 4. Scheduling

### Inputs

Read:
- tasks and dependencies;
- effort;
- assignee/team availability if supplied;
- requested target start/delivery date;
- work calendar if supplied.

### Assignee

If actual people are supplied, assign only compatible people.

If actual people are not supplied, use placeholders:
- 前端待分配
- 后端待分配
- 测试待分配
- 待分配

Never invent a real person.

### Dates

Schedule independent tasks in parallel when resources permit.

Respect dependencies:
- dependent task starts after dependency completion;
- when planning by whole dates, default to the next workday after dependency completion.

If only effort is known but capacity is not, make the minimum reasonable schedule and keep assumptions explicit.

### Critical path

Critical path should represent the dependency chain whose delay would move the delivery date.

Do not simply choose the longest task IDs or every task.

### Output summary

Set:
- earliest task start → `start_date`
- latest task end → `delivery_date`
- workdays in schedule window → `estimated_working_days`
- critical chain → `critical_path`

## 5. Regenerating after human edits

Use downstream invalidation:

| Human edit | Recompute |
|---|---|
| goal/scope/module/review answer | breakdown → estimation → scheduling |
| task add/delete/category/dependency | estimation → scheduling |
| effort/confidence/estimate basis | estimation summary; scheduling if needed |
| assignee/start/end | scheduling summary only |

Never replace an unrelated human edit during regeneration.

When the system cannot distinguish AI-authored and human-authored fields, prefer preserving existing values and changing only fields logically required by the new input.

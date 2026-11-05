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

Only put a real affected service/business module in `modules[]` when its implementation boundary is sufficiently known to serve as a planning responsibility boundary. A capability whose implementation layer is still unresolved (for example “this may belong to acts / data / battle”) is not yet a module. Keep it in `review_items` and/or assumptions until the boundary is resolved. Do not create placeholder modules such as “xxx 实现层待确认”.

Separate confirmed business rules from uncertainty in reasoning: requirement facts must not be treated as assumptions merely because the AI restates them. Use `assumptions[]` only for facts that are not explicitly confirmed by the requirement/context.

If understanding is edited later, downstream stage JSON is not rewritten here; mark downstream stages stale through init when possible.

## Breakdown

Read:
- init.json;
- understanding.json;
- requirement context when necessary.

Generate only breakdown.json.

Use understanding.modules[].id as module_id.

Break work by **responsibility boundary**, not by feature step:

1. Start from `understanding.modules[]`.
2. By default, create one task for one affected service / independently owned business module.
3. Put multiple changes inside that module into the same task. Use a complete `description` and, when useful, `work_items[]` to enumerate the internal changes.
4. Split a module into more than one task only when there is a real boundary: different owner, different repository, independently deliverable work, or another explicit assignment boundary.
5. Small related changes in the same module/service should be merged.
6. Cross-module integration/QA can be a separate task with `module_id = null`.
7. If a required review item leaves the implementation module unresolved, do not prematurely materialize a confident standalone module/task. Preserve the uncertainty and allow the task to remain provisional or merge after the review answer.

A task should be close to what can later be assigned to one owner. APIs, pages, UI states, handlers, and implementation steps inside the same module are normally `work_items`, not separate tasks.

Dependencies express **blocking relationships between task/module deliverables**, not internal coding sequence inside one module.

Read `references/task-ownership.md` and use its module/service/repository/owner rules to validate whether multiple changes belong to the same assignable responsibility boundary.

Before finalizing breakdown, perform a consolidation pass:
- group tasks by module/service and likely ownership;
- merge tasks that differ only by feature action inside the same responsibility boundary;
- verify every task represents an independently assignable unit;
- verify no requirement detail was lost when merging.

Do not generate effort, confidence, assignee, or dates.

## Estimation

Read:
- breakdown.json;
- understanding.json if assumptions/review answers affect complexity.

Generate only estimation.json.

For each breakdown task, create exactly one estimation. Use concrete sub-effort components whose sum equals effort_days. If the task has `work_items`, use them as the natural source for estimate_basis where appropriate. Do not turn work_items back into separate task estimations. Lower confidence when unresolved information can materially affect effort.

Do not change task definitions.

## Scheduling

Read:
- breakdown.json;
- estimation.json;
- actual team/capacity/calendar context available through XDPai or related skills.

Generate only scheduling.json.

Create exactly one schedule item per confirmed breakdown task. Respect dependencies and parallelism. Read `references/task-ownership.md`.

Prefer actual owner/team/capacity/calendar context. Do not invent people or artificial resource slots such as “后端待分配-A/B”.

If the actual owner is unknown, use an explicit unresolved assignee such as `待确认负责人` (or a known team/role if that is the highest-confidence fact). When real capacity is unavailable, generate only a dependency-based tentative schedule: independent tasks may run in parallel, and the result must not imply a resource-constrained plan that the system cannot justify.

If a task itself is provisional because its responsibility boundary is unresolved, do not assign false-precision dates as if it were a confirmed delivery unit; preserve the uncertainty in the scheduling result/report according to what the current schema/runtime supports.

Compute critical path from actual dependency/schedule impact, not from an invented resource serialization.

Do not change task definitions or effort estimates.

## Human edits

A stage node must preserve upstream human edits exactly as read.

If the current stage JSON already exists and contains human edits, change only fields necessary to satisfy the current new input. Never rebuild unrelated rows just for stylistic consistency.
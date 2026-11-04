# Output contract

This file defines the canonical data contract consumed by the requirement-arrangement workbench.

## Top-level shape

```text
schema_version
requirement
evaluation
  current_stage
  stages
    understanding
    breakdown
    estimation
    scheduling
tasks
revision
```

The UI uses the four stage objects as navigation and uses the shared `tasks` array across breakdown, estimation, and scheduling. Do not duplicate independent task records inside individual stage outputs.

## 1. requirement

| Field | Type | Rule |
|---|---|---|
| id | string | Stable requirement ID |
| title | string | Non-empty |
| description | string | Original or normalized requirement description |
| priority | string | Prefer `high`, `medium`, `low`; preserve source vocabulary if necessary |

## 2. evaluation

### current_stage

One of:
- `understanding`
- `breakdown`
- `estimation`
- `scheduling`

It indicates which stage the UI should open by default. It does not mean previous stages may be discarded.

### stage status

Each stage has `status`:
- `pending`
- `in_progress`
- `completed`

A later stage should not be `completed` while a required predecessor has no usable output.

## 3. understanding stage

### output.goal

One concise sentence describing the user/business outcome.

### output.scope

Concrete capabilities included in this requirement. Do not put implementation tasks here.

### output.out_of_scope

Explicit exclusions or boundaries. Use an empty array when no exclusion is known; do not invent exclusions.

### output.modules

Array of affected code modules.

Each item:

```json
{
  "id": "M1",
  "side": "frontend",
  "name": "activity-web",
  "repository": "git/ieg/activity-web",
  "change_summary": "新增活动详情页、报名入口和报名状态展示。"
}
```

Rules:
- `side` is exactly `frontend` or `backend`.
- `name` is the module/service/application name.
- `repository` is a repository identifier or URL/path supplied by context. If unknown, use `""`.
- `change_summary` is one sentence describing the primary change in that module.
- IDs are unique and stable across regeneration.
- A database table is not itself a module unless the product explicitly models it as one. Prefer the owning backend module/service.

### output.assumptions

Only assumptions that materially affect interpretation, task decomposition, effort, or schedule.

### review_items

Human inputs required or useful before later stages become reliable.

#### Choice item

```json
{
  "id": "Q1",
  "type": "choice",
  "question": "活动是否限制总报名人数？",
  "required": true,
  "ai_assumption": "不限制",
  "value": null,
  "custom_value": "",
  "options": ["不限制", "有限制"],
  "impact": "影响 BE-01 并发控制与一致性设计"
}
```

Rules:
- `options` contains AI-generated standard choices only. The workbench provides the separate “自定义” UI option.
- If the human chooses a standard option, put it in `value`.
- If the human chooses custom, set `value` to `"自定义"` and put the answer in `custom_value`.
- Required choice items are unresolved when `value` is null/empty, or when `value == "自定义"` and `custom_value` is empty.

#### Text item

```json
{
  "id": "Q3",
  "type": "text",
  "question": "还有哪些关键业务规则需要补充？",
  "required": false,
  "ai_assumption": "暂无",
  "value": "",
  "impact": "补充内容会参与后续任务拆解和估算"
}
```

## 4. breakdown stage

`output.task_ids` is the ordered list of IDs shown in the task-breakdown stage.

Rules:
- Every ID must exist exactly once in top-level `tasks`.
- Every top-level task must appear in `task_ids`.
- No duplicate IDs.
- Dependencies reference task IDs only.
- Dependency graph must be acyclic.
- Avoid task granularity that is either too broad to estimate or too tiny to manage.

The UI allows adding, editing, and deleting tasks. After a human changes tasks, regenerate downstream estimation and scheduling data without reverting the edit.

## 5. shared task object

```json
{
  "id": "BE-01",
  "title": "报名核心接口",
  "category": "backend",
  "description": "报名提交、参数校验、幂等和异常处理",
  "effort_days": 2,
  "confidence": "medium",
  "assignee": "后端 A",
  "start_date": "2026-11-05",
  "end_date": "2026-11-06",
  "dependencies": [],
  "estimate_basis": [
    "领域逻辑 1d",
    "幂等与异常 0.5d",
    "单测与自测 0.5d"
  ]
}
```

Rules:
- `category`: `frontend` | `backend` | `other`.
- `effort_days`: positive number, normally in 0.5-day increments unless context supports finer precision.
- `confidence`: `high` | `medium` | `low`.
- `assignee`: human-editable display value. Never fabricate a real employee.
- `start_date <= end_date`.
- `estimate_basis` must explain the estimate specifically. Avoid vague text such as “based on complexity”.

## 6. estimation stage

Output:

```json
{
  "total_effort_days": 8,
  "medium_confidence_tasks": ["FE-02", "BE-01", "QA-01"],
  "high_confidence_tasks": ["FE-01", "BE-02", "BE-03"],
  "low_confidence_tasks": []
}
```

Rules:
- Total equals the sum of all `tasks[].effort_days`.
- Confidence buckets are exhaustive and mutually exclusive.
- IDs in each bucket must match the corresponding task's `confidence`.
- If a page version omits an empty bucket visually, keep the field in JSON for a stable contract.

## 7. scheduling stage

Output:

```json
{
  "start_date": "2026-11-05",
  "delivery_date": "2026-11-11",
  "estimated_working_days": 5,
  "critical_path": ["BE-01", "FE-02", "QA-01"]
}
```

Rules:
- Dates use `YYYY-MM-DD`.
- `start_date` is the earliest task start.
- `delivery_date` is the latest task end.
- `estimated_working_days` counts workdays in the schedule window unless an explicit team calendar is supplied.
- Every critical-path ID exists in tasks.
- A task must not start before a dependency is finished. With day-granularity scheduling, if a dependency ends on date D, the dependent task should start on the next valid workday unless the environment explicitly allows same-day handoff.
- Detect impossible schedules rather than hiding them.

## 8. revision

```json
{
  "version": 3,
  "last_modified_by": "human",
  "changes": [
    "BE-01 effort_days changed from 2 to 2.5"
  ]
}
```

Rules:
- `version` is a positive integer.
- `last_modified_by`: `ai` or `human`.
- Append concise changes when updating existing state.
- Do not manufacture detailed audit history that the system did not capture.

## Regeneration dependencies

Changes should cascade only downstream:

- Understanding/module/review answer change → reconsider breakdown, estimation, scheduling.
- Task add/delete/dependency change → recompute estimation and scheduling.
- Effort/confidence change → recompute estimation totals/buckets and scheduling if dates depend on effort.
- Owner/date change → recompute scheduling only.
- Unrelated human edits must remain unchanged.

## Page compatibility checklist

Before output:
1. Exactly four stages exist: understanding, breakdown, estimation, scheduling.
2. Understanding modules have frontend/backend side, name, repository, change_summary.
3. Breakdown task IDs and top-level tasks are one-to-one.
4. Every task has editable estimation fields.
5. Every task has editable scheduling fields.
6. Totals and confidence buckets reconcile.
7. Dependencies exist and are acyclic.
8. Dates and critical path are valid.
9. Review items use only `choice` or `text`.
10. Run the validator.

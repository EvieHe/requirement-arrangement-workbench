# Output contract — schema 4.0

The workbench consumes five independent JSON documents.

## Relationships

```text
init.requirement.id
  ├─ understanding.requirement_id
  ├─ breakdown.requirement_id
  ├─ estimation.requirement_id
  └─ scheduling.requirement_id

understanding.modules[].id
  └─ breakdown.tasks[].module_id

breakdown.tasks[].id
  ├─ breakdown.tasks[].dependencies[]
  ├─ estimation.estimations[].task_id
  ├─ scheduling.schedule[].task_id
  └─ scheduling.summary.critical_path[]
```

## init.json

Purpose: shared requirement identity and stage freshness.

Required fields:
- `schema_version = "4.0"`
- `requirement.id/title/description/priority`
- `stage_status.understanding/breakdown/estimation/scheduling`
- `revision`

Stage status enum: `pending | ready | completed | stale`.

## understanding.json

Purpose: render the 需求理解 tab.

Required:
- `schema_version`
- `requirement_id`
- `goal`
- `scope[]`
- `out_of_scope[]`
- `modules[]`
- `assumptions[]`
- `review_items[]`
- `revision`

Module:
```json
{
  "id": "M1",
  "side": "frontend",
  "name": "activity-web",
  "repository": "git/ieg/activity-web",
  "change_summary": "新增活动详情页、报名入口和状态展示。"
}
```

Rules:
- side is `frontend | backend`.
- repository may be empty only when unknown; do not invent it.
- change_summary is one concise sentence.
- module IDs are unique.

Review item types:

Choice:
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
  "impact": "影响报名接口并发控制与一致性设计"
}
```

Text:
```json
{
  "id": "Q2",
  "type": "text",
  "question": "还有哪些关键业务规则需要补充？",
  "required": false,
  "ai_assumption": "暂无",
  "value": "",
  "impact": "可能影响后续任务拆解与估算"
}
```

The UI itself adds “自定义”; do not include it in choice options.

## breakdown.json

Purpose: render the 任务拆解 tab.

Task:
```json
{
  "id": "BE-01",
  "module_id": "M3",
  "title": "报名核心接口",
  "category": "backend",
  "description": "完成报名模块后端能力改造，覆盖提交、校验、幂等和异常处理。",
  "work_items": [
    "报名提交与参数校验",
    "幂等与重复提交处理",
    "异常处理与必要自测"
  ],
  "dependencies": []
}
```

Rules:
- category is `frontend | backend | other`.
- module_id must reference understanding.modules[].id. For cross-module integration/QA tasks, module_id may be null.
- a task represents an **assignable module/service responsibility boundary**, not an individual feature action.
- default: one affected service or independently owned business module maps to one task.
- multiple APIs/pages/actions inside the same module belong in one task; preserve them in `description` and optional `work_items[]`.
- `work_items`, when present, is a non-empty list of concise strings describing internal changes. It does not create extra scheduling/estimation units.
- split one module into multiple tasks only for a real ownership/delivery boundary (for example different owners, repositories, or independently deliverable work).
- small related changes in the same module/service should be merged.
- dependencies reference task IDs and express blocking dependencies between task/module deliverables, not internal implementation order.
- IDs unique; graph acyclic.
- breakdown owns task definition only. Do not put effort or schedule fields here.

## estimation.json

Purpose: render the 工作量评估 tab.

```json
{
  "summary": {
    "total_effort_days": 8,
    "confidence_counts": {"high": 3, "medium": 3, "low": 0}
  },
  "estimations": [
    {
      "task_id": "BE-01",
      "effort_days": 2,
      "confidence": "medium",
      "estimate_basis": [
        {"item": "领域逻辑", "effort_days": 1},
        {"item": "幂等与异常", "effort_days": 0.5},
        {"item": "单测与自测", "effort_days": 0.5}
      ],
      "uncertainties": ["名额限制尚未确认"]
    }
  ]
}
```

Rules:
- exactly one estimation for every breakdown task.
- effort_days > 0.
- confidence is `high | medium | low`.
- sum estimate_basis effort equals task effort.
- sum estimations effort equals summary.total_effort_days.
- confidence_counts exactly reconcile.

## scheduling.json

Purpose: render the 排期生成 tab.

```json
{
  "summary": {
    "start_date": "2026-11-05",
    "delivery_date": "2026-11-11",
    "estimated_working_days": 5,
    "critical_path": ["BE-01", "FE-02", "QA-01"]
  },
  "schedule": [
    {
      "task_id": "BE-01",
      "assignee": "后端 A",
      "start_date": "2026-11-05",
      "end_date": "2026-11-06"
    }
  ]
}
```

Rules:
- exactly one schedule item for every breakdown task.
- assignee must come from known team context; if unknown use role-level “待分配”, never invent a person.
- dates are YYYY-MM-DD and start <= end.
- dependencies must be respected.
- summary start/delivery equal earliest/latest task dates.
- critical_path contains existing task IDs.

## revision object

All five JSON documents use:

```json
{
  "version": 1,
  "last_modified_by": "ai",
  "changes": []
}
```

last_modified_by: `ai | human`.

## Freshness

Recommended init.stage_status transitions:
- initial: understanding=ready, others=pending
- after understanding: understanding=completed, breakdown=ready
- if understanding changes: breakdown/estimation/scheduling=stale
- after breakdown: breakdown=completed, estimation=ready
- if breakdown changes: estimation/scheduling=stale
- after estimation: estimation=completed, scheduling=ready
- after scheduling: scheduling=completed
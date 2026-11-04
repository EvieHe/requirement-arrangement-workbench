#!/usr/bin/env python3
"""Validate requirement-arrangement planning JSON (schema 3.2).

Usage:
    python3 scripts/validate_planning_result.py path/to/planning-result.json
"""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import date, timedelta
from pathlib import Path

STAGES = ("understanding", "breakdown", "estimation", "scheduling")
STAGE_STATUS = {"pending", "in_progress", "completed"}
TASK_CATEGORIES = {"frontend", "backend", "other"}
CONFIDENCE = {"high", "medium", "low"}
REVIEW_TYPES = {"choice", "text"}
MODULE_SIDES = {"frontend", "backend"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def require_dict(v: Validation, obj, path: str):
    if not isinstance(obj, dict):
        v.error(f"{path} must be an object")
        return {}
    return obj


def require_list(v: Validation, obj, path: str):
    if not isinstance(obj, list):
        v.error(f"{path} must be an array")
        return []
    return obj


def nonempty_string(v: Validation, obj, path: str, allow_empty: bool = False) -> str:
    if not isinstance(obj, str):
        v.error(f"{path} must be a string")
        return ""
    if not allow_empty and not obj.strip():
        v.error(f"{path} must be non-empty")
    return obj


def parse_date(v: Validation, value, path: str):
    if not isinstance(value, str) or not DATE_RE.match(value):
        v.error(f"{path} must be YYYY-MM-DD")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        v.error(f"{path} is not a valid calendar date")
        return None


def weekday_count(start: date, end: date) -> int:
    if end < start:
        return 0
    n = 0
    d = start
    while d <= end:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def check_unique(v: Validation, values: list[str], path: str) -> None:
    seen = set()
    for item in values:
        if item in seen:
            v.error(f"{path} contains duplicate value {item!r}")
        seen.add(item)


def detect_cycle(tasks_by_id: dict[str, dict]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str):
        mark = state.get(node, 0)
        if mark == 1:
            if node in stack:
                i = stack.index(node)
                return stack[i:] + [node]
            return [node, node]
        if mark == 2:
            return None
        state[node] = 1
        stack.append(node)
        for dep in tasks_by_id[node].get("dependencies", []):
            if dep in tasks_by_id:
                cycle = visit(dep)
                if cycle:
                    return cycle
        stack.pop()
        state[node] = 2
        return None

    for task_id in tasks_by_id:
        cycle = visit(task_id)
        if cycle:
            return cycle
    return None


def validate(data: dict) -> Validation:
    v = Validation()

    expected_top = {"schema_version", "requirement", "evaluation", "tasks", "revision"}
    missing = expected_top - set(data)
    if missing:
        v.error(f"missing top-level keys: {sorted(missing)}")

    if data.get("schema_version") != "3.2":
        v.error("schema_version must be '3.2'")

    requirement = require_dict(v, data.get("requirement"), "requirement")
    for field in ("id", "title", "description", "priority"):
        nonempty_string(v, requirement.get(field), f"requirement.{field}")

    evaluation = require_dict(v, data.get("evaluation"), "evaluation")
    current_stage = evaluation.get("current_stage")
    if current_stage not in STAGES:
        v.error(f"evaluation.current_stage must be one of {STAGES}")

    stages = require_dict(v, evaluation.get("stages"), "evaluation.stages")
    if set(stages.keys()) != set(STAGES):
        v.error(
            "evaluation.stages must contain exactly understanding, breakdown, estimation, scheduling"
        )

    # Understanding
    understanding = require_dict(v, stages.get("understanding"), "evaluation.stages.understanding")
    if understanding.get("status") not in STAGE_STATUS:
        v.error("understanding.status is invalid")
    uout = require_dict(v, understanding.get("output"), "understanding.output")
    nonempty_string(v, uout.get("goal"), "understanding.output.goal")
    for field in ("scope", "out_of_scope", "assumptions"):
        arr = require_list(v, uout.get(field), f"understanding.output.{field}")
        for i, x in enumerate(arr):
            nonempty_string(v, x, f"understanding.output.{field}[{i}]")

    modules = require_list(v, uout.get("modules"), "understanding.output.modules")
    module_ids: list[str] = []
    for i, raw in enumerate(modules):
        m = require_dict(v, raw, f"understanding.output.modules[{i}]")
        mid = nonempty_string(v, m.get("id"), f"modules[{i}].id")
        module_ids.append(mid)
        if m.get("side") not in MODULE_SIDES:
            v.error(f"modules[{i}].side must be frontend or backend")
        nonempty_string(v, m.get("name"), f"modules[{i}].name")
        nonempty_string(v, m.get("repository"), f"modules[{i}].repository", allow_empty=True)
        nonempty_string(v, m.get("change_summary"), f"modules[{i}].change_summary")
    check_unique(v, module_ids, "module ids")

    review_items = require_list(v, understanding.get("review_items"), "understanding.review_items")
    review_ids: list[str] = []
    for i, raw in enumerate(review_items):
        item = require_dict(v, raw, f"understanding.review_items[{i}]")
        rid = nonempty_string(v, item.get("id"), f"review_items[{i}].id")
        review_ids.append(rid)
        typ = item.get("type")
        if typ not in REVIEW_TYPES:
            v.error(f"review_items[{i}].type must be choice or text")
        nonempty_string(v, item.get("question"), f"review_items[{i}].question")
        if not isinstance(item.get("required"), bool):
            v.error(f"review_items[{i}].required must be boolean")
        nonempty_string(v, item.get("ai_assumption"), f"review_items[{i}].ai_assumption", allow_empty=True)
        nonempty_string(v, item.get("impact"), f"review_items[{i}].impact")
        value = item.get("value")
        if value is not None and not isinstance(value, str):
            v.error(f"review_items[{i}].value must be string or null")
        if typ == "choice":
            options = require_list(v, item.get("options"), f"review_items[{i}].options")
            if len(options) < 2:
                v.error(f"review_items[{i}].options must contain at least two choices")
            for j, option in enumerate(options):
                nonempty_string(v, option, f"review_items[{i}].options[{j}]")
            if "自定义" in options:
                v.error(
                    f"review_items[{i}].options must not contain '自定义'; the UI adds it automatically"
                )
            if not isinstance(item.get("custom_value", ""), str):
                v.error(f"review_items[{i}].custom_value must be string")
            if value not in (None, "", "自定义") and value not in options:
                v.error(f"review_items[{i}].value must match an option or '自定义'")
            if value == "自定义" and not item.get("custom_value", "").strip():
                v.warn(f"review_items[{i}] selected 自定义 but custom_value is empty")
        elif typ == "text" and "options" in item:
            v.error(f"review_items[{i}] text item must not contain options")
    check_unique(v, review_ids, "review item ids")

    # Tasks
    tasks = require_list(v, data.get("tasks"), "tasks")
    task_ids: list[str] = []
    tasks_by_id: dict[str, dict] = {}
    task_dates: dict[str, tuple[date | None, date | None]] = {}
    total_effort = 0.0
    confidence_ids = {c: [] for c in CONFIDENCE}

    for i, raw in enumerate(tasks):
        t = require_dict(v, raw, f"tasks[{i}]")
        tid = nonempty_string(v, t.get("id"), f"tasks[{i}].id")
        task_ids.append(tid)
        if tid in tasks_by_id:
            v.error(f"duplicate task id {tid!r}")
        tasks_by_id[tid] = t
        nonempty_string(v, t.get("title"), f"tasks[{i}].title")
        if t.get("category") not in TASK_CATEGORIES:
            v.error(f"tasks[{i}].category must be frontend/backend/other")
        nonempty_string(v, t.get("description"), f"tasks[{i}].description")
        effort = t.get("effort_days")
        if not isinstance(effort, (int, float)) or isinstance(effort, bool) or effort <= 0:
            v.error(f"tasks[{i}].effort_days must be a positive number")
        else:
            total_effort += float(effort)
        conf = t.get("confidence")
        if conf not in CONFIDENCE:
            v.error(f"tasks[{i}].confidence must be high/medium/low")
        else:
            confidence_ids[conf].append(tid)
        nonempty_string(v, t.get("assignee"), f"tasks[{i}].assignee")
        start = parse_date(v, t.get("start_date"), f"tasks[{i}].start_date")
        end = parse_date(v, t.get("end_date"), f"tasks[{i}].end_date")
        task_dates[tid] = (start, end)
        if start and end and start > end:
            v.error(f"task {tid} start_date is after end_date")
        deps = require_list(v, t.get("dependencies"), f"tasks[{i}].dependencies")
        for j, dep in enumerate(deps):
            nonempty_string(v, dep, f"tasks[{i}].dependencies[{j}]")
            if dep == tid:
                v.error(f"task {tid} cannot depend on itself")
        basis = require_list(v, t.get("estimate_basis"), f"tasks[{i}].estimate_basis")
        if not basis:
            v.error(f"task {tid} estimate_basis must not be empty")
        for j, b in enumerate(basis):
            nonempty_string(v, b, f"tasks[{i}].estimate_basis[{j}]")

    # Dependency refs and cycles
    for tid, t in tasks_by_id.items():
        for dep in t.get("dependencies", []):
            if dep not in tasks_by_id:
                v.error(f"task {tid} dependency {dep!r} does not exist")
    cycle = detect_cycle(tasks_by_id) if tasks_by_id else None
    if cycle:
        v.error("dependency graph contains a cycle: " + " -> ".join(cycle))

    # Breakdown
    breakdown = require_dict(v, stages.get("breakdown"), "evaluation.stages.breakdown")
    if breakdown.get("status") not in STAGE_STATUS:
        v.error("breakdown.status is invalid")
    bout = require_dict(v, breakdown.get("output"), "breakdown.output")
    breakdown_ids = require_list(v, bout.get("task_ids"), "breakdown.output.task_ids")
    check_unique(v, breakdown_ids, "breakdown task_ids")
    if set(breakdown_ids) != set(task_ids):
        v.error("breakdown.output.task_ids must match top-level task IDs exactly")
    require_list(v, breakdown.get("review_items"), "breakdown.review_items")

    # Estimation
    estimation = require_dict(v, stages.get("estimation"), "evaluation.stages.estimation")
    if estimation.get("status") not in STAGE_STATUS:
        v.error("estimation.status is invalid")
    eout = require_dict(v, estimation.get("output"), "estimation.output")
    declared_total = eout.get("total_effort_days")
    if not isinstance(declared_total, (int, float)) or isinstance(declared_total, bool):
        v.error("estimation.output.total_effort_days must be numeric")
    elif not math.isclose(float(declared_total), total_effort, rel_tol=0, abs_tol=1e-9):
        v.error(
            f"estimation total {declared_total} != sum(tasks.effort_days) {total_effort:g}"
        )

    bucket_fields = {
        "high": "high_confidence_tasks",
        "medium": "medium_confidence_tasks",
        "low": "low_confidence_tasks",
    }
    bucket_union: list[str] = []
    for conf, field in bucket_fields.items():
        ids = require_list(v, eout.get(field), f"estimation.output.{field}")
        check_unique(v, ids, field)
        bucket_union.extend(ids)
        if set(ids) != set(confidence_ids[conf]):
            v.error(f"{field} does not match tasks with confidence={conf}")
    if len(bucket_union) != len(set(bucket_union)):
        v.error("confidence buckets overlap")

    require_list(v, estimation.get("review_items"), "estimation.review_items")

    # Scheduling
    scheduling = require_dict(v, stages.get("scheduling"), "evaluation.stages.scheduling")
    if scheduling.get("status") not in STAGE_STATUS:
        v.error("scheduling.status is invalid")
    sout = require_dict(v, scheduling.get("output"), "scheduling.output")
    sched_start = parse_date(v, sout.get("start_date"), "scheduling.output.start_date")
    sched_end = parse_date(v, sout.get("delivery_date"), "scheduling.output.delivery_date")
    working_days = sout.get("estimated_working_days")
    if not isinstance(working_days, int) or isinstance(working_days, bool) or working_days <= 0:
        v.error("scheduling.output.estimated_working_days must be a positive integer")
    critical = require_list(v, sout.get("critical_path"), "scheduling.output.critical_path")
    for tid in critical:
        if tid not in tasks_by_id:
            v.error(f"critical_path references unknown task {tid!r}")
    check_unique(v, critical, "critical_path")
    require_list(v, scheduling.get("review_items"), "scheduling.review_items")

    valid_starts = [x[0] for x in task_dates.values() if x[0]]
    valid_ends = [x[1] for x in task_dates.values() if x[1]]
    if valid_starts and sched_start and sched_start != min(valid_starts):
        v.error("scheduling.output.start_date must equal earliest task start_date")
    if valid_ends and sched_end and sched_end != max(valid_ends):
        v.error("scheduling.output.delivery_date must equal latest task end_date")
    if sched_start and sched_end and isinstance(working_days, int):
        expected = weekday_count(sched_start, sched_end)
        if working_days != expected:
            v.warn(
                f"estimated_working_days={working_days}, weekday count in date window={expected}; "
                "acceptable only when a custom work calendar is intended"
            )

    # Dependency date ordering (strict next-day handoff for date-granularity plan)
    for tid, t in tasks_by_id.items():
        tstart, _ = task_dates.get(tid, (None, None))
        if not tstart:
            continue
        for dep in t.get("dependencies", []):
            _, dep_end = task_dates.get(dep, (None, None))
            if dep_end and tstart <= dep_end:
                v.error(
                    f"task {tid} starts {tstart} before dependency {dep} has fully completed ({dep_end})"
                )

    # Revision
    revision = require_dict(v, data.get("revision"), "revision")
    version = revision.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        v.error("revision.version must be a positive integer")
    if revision.get("last_modified_by") not in {"ai", "human"}:
        v.error("revision.last_modified_by must be ai or human")
    changes = require_list(v, revision.get("changes"), "revision.changes")
    for i, x in enumerate(changes):
        nonempty_string(v, x, f"revision.changes[{i}]")

    return v


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_planning_result.py <planning-result.json>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print("ERROR: top-level JSON must be an object", file=sys.stderr)
        return 1

    result = validate(data)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if result.errors:
        print(f"FAILED: {len(result.errors)} error(s), {len(result.warnings)} warning(s)", file=sys.stderr)
        return 1

    print(f"OK: planning JSON is valid ({len(result.warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

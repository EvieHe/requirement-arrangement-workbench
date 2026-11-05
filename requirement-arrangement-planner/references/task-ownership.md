# Task ownership and responsibility-boundary reference

This reference defines how requirement-arrangement-planner should use module/service ownership information when forming assignable tasks and schedules.

It is a planning reference, not a separate workflow stage and not a new output JSON.

## Purpose

The planner should not treat “feature point” as the default task boundary.

A task should be close to a unit that can be assigned to a real owner/team and independently delivered.

Use the following signals together:

- affected service / business module;
- repository;
- known owner / responsible team;
- whether the work can be delivered independently;
- whether two changes share the same code ownership and release boundary.

## Default boundary

Default:

```text
one service / independently owned business module
≈
one assignable task
```

Multiple APIs, pages, handlers, states, CRUD actions, or implementation steps inside the same responsibility boundary should normally remain one task and be expressed as `work_items[]`.

Do not split tasks just to preserve detail.

## When to split one module

Split one module into multiple tasks only when there is a real assignment or delivery boundary, for example:

- different responsible owners/teams;
- different repositories or independently released packages;
- independently deliverable submodules with separate ownership;
- explicit organizational responsibility boundaries.

## When to merge

Prefer merging when changes:

- belong to the same service/module;
- share the same repository;
- are normally owned by the same person/team;
- are part of the same delivery;
- only differ by feature action or endpoint/page.

## Owner information

Owner information is reference context for planning.

If XDPai or the current environment can provide a known owner/team for a module or repository, use it when deciding task boundaries and scheduling.

Never invent a person's name.

If only a team or role is known, preserve that level of certainty.

If no owner is known, use an explicit unresolved state such as:

```text
待确认负责人
```

instead of creating artificial resource identities such as:

```text
后端待分配-A
后端待分配-B
```

unless those resource slots come from an actual capacity model supplied by the user/system.

## Unresolved module ownership

If the implementation layer itself is not confirmed, do not prematurely turn the hypothetical module into a fully committed task with confident effort and schedule.

Example:

```text
“有效对局计数”可能落在 acts / data / battle
```

Until the responsibility boundary is confirmed:

- keep the uncertainty visible;
- prefer attaching it to the most likely existing module as an uncertainty/work item when appropriate; or
- keep it provisional and avoid treating it as a confirmed independent delivery unit.

The planner may use a required review item to resolve this boundary.

## Dependencies

Dependencies should express blocking relationships between independently assignable module/service deliverables.

Do not encode the internal coding order of work_items as task dependencies.

## Scheduling

Scheduling should consume actual ownership/capacity information when available.

If owners are different, independent module tasks may run in parallel.

Do not serialize unrelated backend services merely because they are all backend tasks.

If owner/capacity information is unavailable, present the schedule as tentative and avoid implying false precision.

## Relationship to stage outputs

This reference does not add a new workflow variable.

It guides:

- understanding: identifying real affected modules/services and unresolved ownership;
- breakdown: choosing the task boundary;
- estimation: estimating the whole assignable task, with work_items as basis;
- scheduling: using known owners/teams/capacity and preserving uncertainty where unknown.

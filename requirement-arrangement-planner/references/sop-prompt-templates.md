# XDPai SOP prompt templates

Workflow variables:

- `requirement_arrangement.init`
- `requirement_arrangement.understanding`
- `requirement_arrangement.breakdown`
- `requirement_arrangement.estimation`
- `requirement_arrangement.scheduling`

All JSON must follow `requirement-arrangement-planner` schema 4.0.

---

## 需求理解

【目标】

你当前处于「需求理解」节点。主动读取当前 XDPai SOP 任务关联的需求信息，生成需求智能排期的初始化 JSON 和需求理解 JSON，供页面「需求理解」Tab 使用。

【执行步骤】

1. 加载 xdpai skill，读取当前 SOP 任务关联的需求信息。应主动获取能够访问到的需求标题、描述、优先级、需求链接/上下文以及已有流程变量；不要要求提示词预先携带完整需求正文。
2. 加载 requirement-arrangement-planner skill，仔细阅读其 output contract、stage generation rules 和 init/understanding 模板。
3. 如果流程变量 `requirement_arrangement.init` 不存在：
   - 根据实际需求信息生成完整 init JSON；
   - stage_status 设置为：
     - understanding = completed
     - breakdown = ready
     - estimation = pending
     - scheduling = pending
4. 生成完整 understanding JSON，必须包含：
   - requirement_id
   - goal
   - scope
   - out_of_scope
   - modules
   - assumptions
   - review_items
   - revision
5. modules 必须区分 frontend / backend。每个模块包含：
   - id
   - side
   - name
   - repository
   - change_summary
   仓库信息未知时禁止猜测，repository 使用空字符串；如果缺失会影响后续规划，可生成 review_item 让用户补充。
6. review_items 只生成会实际影响任务拆解、工作量或排期的问题。支持 choice 和 text 两种类型。
7. 如果已有 understanding 流程变量且包含人工修改，保留人工修改，不要无理由覆盖。
8. 按 skill 要求校验 init JSON 和 understanding JSON，修正直到通过。
9. 使用 xdpai skill 的 set_workflow_var 写入：
   - `requirement_arrangement.init=<完整 init JSON>`
   - `requirement_arrangement.understanding=<完整 understanding JSON>`

【边界】

- 本节点不生成任务、人日或排期。
- 不写 breakdown / estimation / scheduling JSON。
- 不编造仓库、模块、人员或业务规则。
- 输出给用户的节点汇报保持简洁，说明识别到的范围、模块数量和待确认项数量即可。

---

## 任务拆解

【目标】

你当前处于「任务拆解」节点。基于当前需求信息和需求理解结果，生成页面「任务拆解」Tab 所需的完整 breakdown JSON。

【执行步骤】

1. 加载 xdpai skill。
2. 读取流程变量：
   - `requirement_arrangement.init`
   - `requirement_arrangement.understanding`
   - 如果 `requirement_arrangement.breakdown` 已存在，也一并读取。
3. 必要时再次主动读取当前 XDPai 需求信息，但不要重新生成需求理解阶段的数据。
4. 加载 requirement-arrangement-planner skill，阅读 breakdown 模板和阶段规则。
5. 基于 understanding 中的 scope、modules、assumptions，以及已经填写的 review_items 结果，拆解可执行研发任务。任务粒度遵循：
   - 默认一个受影响服务 / 独立业务模块对应一个研发任务；
   - 同一模块内的多个接口、页面、状态、处理步骤属于同一个任务的内部工作内容，不因功能点不同而拆成多个任务；
   - 只有存在真实的负责人边界、仓库边界或独立交付边界时，才把同一模块拆成多个任务；
   - 同模块 / 同服务的小改动应优先合并；
   - 跨模块联调、QA 可以单独成任务；
   - 未解决的 review_item 如果会改变模块归属，不要把假设的模块边界过早固化成确定任务。
6. 阅读 requirement-arrangement-planner 内的 `references/task-ownership.md`，结合当前环境中能够获取到的模块、仓库、负责人/责任团队信息判断任务边界。负责人信息只作为规划参考，不新增独立 Workflow Var；禁止编造负责人，也不要用“后端待分配-A/B”这类虚拟资源槽代替真实责任边界，除非系统确实提供了这样的容量模型。
7. 生成完整 breakdown JSON。每个 task 必须包含：
   - id
   - module_id
   - title
   - category
   - description
   - dependencies
   可增加 `work_items` 列出该模块任务内部的具体改动点，避免为了保留细节而继续拆 task。
8. module_id 必须引用 understanding.modules[].id；跨模块联调/验收任务可以为 null。
9. dependencies 只表达不同任务/模块交付之间的真实阻塞关系，不表达同一模块内部的编码顺序；必须引用已有 task_id，并保证无环。
10. 在输出前做一次任务合并检查：按 module/service 和责任边界检查是否存在“同一模块仅因为功能动作不同而被拆成多个 task”的情况；若存在且没有明确独立负责人/仓库/交付边界，应合并。
11. 如果已有 breakdown JSON 且包含人工新增、删除、修改的任务，人工修改优先；仅在新需求信息确实要求变化时调整。
12. 本节点不生成 effort_days、confidence、assignee、start_date、end_date。
13. 校验 breakdown JSON，修正直到通过。
14. 使用 set_workflow_var 写入：
    - `requirement_arrangement.breakdown=<完整 breakdown JSON>`
15. 更新 init.stage_status：
    - breakdown = completed
    - estimation = ready
    - scheduling = pending
    如果本次对已有 breakdown 做了结构性修改，则 scheduling 应视情况标记 stale。
16. 覆盖写回 `requirement_arrangement.init`。

【边界】

- 不修改 understanding JSON。
- 不生成工作量或排期字段。
- 不为了“完整”而拆出无价值的微任务。
- 不按“一个接口 / 一个页面 / 一个动作”机械拆任务；优先按模块、服务和责任边界收敛。

---

## 工作量评估

【目标】

你当前处于「工作量评估」节点。基于任务拆解，为每个任务生成独立的人日、置信度和估算依据，输出页面「工作量评估」Tab 使用的完整 estimation JSON。

【执行步骤】

1. 加载 xdpai skill，读取：
   - `requirement_arrangement.init`
   - `requirement_arrangement.understanding`
   - `requirement_arrangement.breakdown`
   - 已存在的 `requirement_arrangement.estimation`（如有）
2. 加载 requirement-arrangement-planner skill，阅读 estimation 模板和阶段规则。
3. 对 breakdown.tasks 中每个 task 生成且仅生成一条 estimation。
4. 每条 estimation 必须包含：
   - task_id
   - effort_days
   - confidence
   - estimate_basis
   - uncertainties
5. estimate_basis 必须拆成具体工作组成，每项包含 item + effort_days；各项人日之和必须等于该任务 effort_days。若 breakdown task 含 `work_items`，优先以这些内部工作项为估算依据。估算仍以“整个模块任务”为一个 estimation，不要因为 work_items 再复制出新的 task 级估算。
6. confidence 使用 high / medium / low。存在可能显著改变人日的未确认信息时，不要给 high。
7. 生成 summary：
   - total_effort_days
   - confidence_counts.high / medium / low
   必须与所有 estimations 精确一致。
8. 如果已有 estimation JSON 且用户已经人工调整人日、置信度或依据，优先保留人工修改。
9. 本节点不得修改 breakdown 的任务定义。
10. 校验 estimation JSON，修正直到通过。
11. 使用 set_workflow_var 写入：
    - `requirement_arrangement.estimation=<完整 estimation JSON>`
12. 更新 init.stage_status：
    - estimation = completed
    - scheduling = ready
13. 覆盖写回 `requirement_arrangement.init`。

【边界】

- 不生成负责人和日期。
- 不改变 task title/category/module/dependencies。
- 禁止使用“根据复杂度估算”“参考经验”作为唯一估算依据。

---

## 排期生成

【目标】

你当前处于「排期生成」节点。基于任务拆解和工作量评估生成可执行排期，输出页面「排期生成」Tab 使用的完整 scheduling JSON。

【执行步骤】

1. 加载 xdpai skill，读取：
   - `requirement_arrangement.init`
   - `requirement_arrangement.understanding`
   - `requirement_arrangement.breakdown`
   - `requirement_arrangement.estimation`
   - 已存在的 `requirement_arrangement.scheduling`（如有）
2. 主动读取当前任务可访问到的团队成员、角色、排期/日历等信息；如果没有真实人员信息，不允许编造姓名。
3. 加载 requirement-arrangement-planner skill，阅读 scheduling 模板和阶段规则。
4. 为 breakdown 中每个 task 生成且仅生成一条 schedule item：
   - task_id
   - assignee
   - start_date
   - end_date
5. 没有明确人员时使用角色级占位：
   - 前端待分配
   - 后端待分配
   - 测试待分配
   - 待分配
6. 根据 dependencies、effort 和可用人员并行安排任务。后置任务不得早于依赖任务完成。
7. 生成 summary：
   - start_date
   - delivery_date
   - estimated_working_days
   - critical_path
8. critical_path 必须由真实任务 ID 组成，并代表会实际影响最终交付日期的依赖链。
9. 如果已有 scheduling JSON 且用户人工修改负责人或日期，保留人工修改，除非已与依赖关系冲突；冲突时在节点汇报中明确指出。
10. 不修改 breakdown 或 estimation JSON。
11. 校验 scheduling JSON，修正直到通过。
12. 使用 set_workflow_var 写入：
    - `requirement_arrangement.scheduling=<完整 scheduling JSON>`
13. 更新 init.stage_status：
    - scheduling = completed
14. 覆盖写回 `requirement_arrangement.init`。

【边界】

- 不重新拆任务。
- 不重新估算人日。
- 不编造真实人员。
- 如果排期依赖必要信息缺失，使用合理占位并明确缺口，不要伪造确定性。
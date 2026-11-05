# XDPai SOP prompt templates

Workflow variables:

- `requirement_arrangement.init`
- `requirement_arrangement.understanding`
- `requirement_arrangement.breakdown`
- `requirement_arrangement.estimation`
- `requirement_arrangement.scheduling`

All stage data follows `requirement-arrangement-planner` schema 4.0.

The SOP prompts intentionally stay thin. Detailed planning rules live in the skill and its references.

---

## 需求理解

你当前处于「需求理解」节点。

1. 加载 `xdpai` skill，主动读取当前 SOP Task 关联的真实需求信息与已有流程变量。
2. 加载最新 `requirement-arrangement-planner` skill，按其中 Understanding / init 的规则和数据契约执行。
3. 生成并校验：
   - `requirement_arrangement.init`
   - `requirement_arrangement.understanding`
4. 只把已经能够映射到真实服务/业务模块的对象放入 `modules[]`。实现层仍未确定的能力边界保留为 review item / uncertainty，不要创建“实现层待确认”之类的占位 module。
5. 已经由需求明确确认的业务规则不要当作 assumption；assumptions 只记录真实未确认假设。
6. 使用 XDPai workflow var 能力写回完整 JSON。

本节点不生成 breakdown / estimation / scheduling。

---

## 任务拆解

你当前处于「任务拆解」节点。

1. 加载 `xdpai` skill，读取 init、understanding 和已有 breakdown（如有）。
2. 加载最新 `requirement-arrangement-planner` skill，重点遵循：
   - `references/stage-generation.md`
   - `references/task-ownership.md`
   - breakdown output contract
3. 基于真实 module/service/repository/owner 或责任团队信息形成可分配 Task；不要按接口、页面、状态或功能动作机械拆任务。
4. 同一责任边界内的具体改动使用 `work_items[]` 保留。
5. implementation boundary 尚未确定的能力不要伪装成正式独立 Task。
6. dependencies 只表示不同可分配任务之间的真实阻塞关系。
7. 校验后写回完整 `requirement_arrangement.breakdown`，并按 skill 规则更新 init.stage_status。

本节点不生成人日、负责人或日期。

---

## 工作量评估

你当前处于「工作量评估」节点。

1. 加载 `xdpai` skill，读取 init、understanding、breakdown 和已有 estimation（如有）。
2. 加载最新 `requirement-arrangement-planner` skill，按 Estimation 规则执行。
3. 对每个 confirmed breakdown task 生成且仅生成一条 estimation。
4. 优先以 task 的 `work_items[]` 作为 estimate_basis 的细分依据，但不要把 work_items 再拆回多个 Task。
5. 对模块归属、外部依赖、承接团队等未确认信息正确降低 confidence，并写入 uncertainties。
6. 校验后写回完整 `requirement_arrangement.estimation`，并更新 init.stage_status。

本节点不修改 breakdown，不生成负责人和日期。

---

## 排期生成

你当前处于「排期生成」节点。

1. 加载 `xdpai` skill，读取 init、understanding、breakdown、estimation 和已有 scheduling（如有）。
2. 加载最新 `requirement-arrangement-planner` skill，重点遵循 `references/task-ownership.md` 和 Scheduling 规则。
3. 主动使用当前环境能够获取到的真实 owner / team / capacity / calendar 信息。
4. 禁止编造人员或“后端待分配-A/B”一类虚拟资源槽，除非系统真实提供了该容量模型。
5. owner 未知时明确使用“待确认负责人”或当前能确认到的 team/role。
6. 没有真实 capacity 时只生成 dependency-based tentative schedule：独立任务可以并行，不要因为同属 backend/frontend 就人为串行。
7. critical_path 只基于真实依赖和可证明的排期影响计算。
8. 校验后写回完整 `requirement_arrangement.scheduling`，并更新 init.stage_status。

本节点不重新拆任务或重估人日。

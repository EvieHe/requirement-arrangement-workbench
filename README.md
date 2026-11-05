# requirement-arrangement-workbench

需求智能评估与排期相关 Skill 仓库。

## requirement-arrangement-planner

用于需求理解、任务拆解、工作量评估和排期生成，并维护对应的阶段 JSON 数据契约。

### 一键安装到当前目录

在你希望安装 Skill 的目录下执行：

```bash
mkdir -p requirement-arrangement-planner && curl -fsSL https://github.com/EvieHe/requirement-arrangement-workbench/archive/refs/heads/main.tar.gz | tar -xz -C requirement-arrangement-planner --strip-components=2 requirement-arrangement-workbench-main/requirement-arrangement-planner
```

安装后目录：

```text
./requirement-arrangement-planner/
├── SKILL.md
├── references/
├── scripts/
├── examples/
└── evals/
```

如果当前目录已经存在同名目录，建议先确认其中是否有本地修改，避免文件被覆盖。

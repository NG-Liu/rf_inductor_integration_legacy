# LVBOBALUN Workspace Context

这个目录是当前对话的外层工作区，用来保存跨对话可恢复的上下文、FDL/EMX/Cadence 辅助脚本和阶段性记录。

新对话开始时先读取：

- `PROJECT_CONTEXT.md`
- `fdl_first_batch/params.csv`
- `vm_probe/fdl_stack.proc`
- `vm_probe/fdl_stack_to_emx_proc.py`
- `vm_probe/single_inductor_12s_3p5t_test.il`

注意：`repo_lvbobalun/` 是独立 Git 仓库，外层仓库不直接追踪它，避免嵌套仓库状态混乱。需要管理代码变更时进入 `repo_lvbobalun/` 内单独执行 Git 操作。

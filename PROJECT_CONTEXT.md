# Project Context

更新时间：2026-06-28

## 目标

当前工作围绕 `BEWATERo/LVBOBALUN` 的单电感生成、UltraEM/FDL 仿真、Cadence/EMX 复现和后续 L/Q 代理模型建立。

核心电感结构：

- 单电感，只保留三层金属加空气桥结构。
- 12 边形螺旋电感为当前主方向。
- 当前正确桥规则：左桥在 `m5`，右桥为 `m5/v4/m4`，两个桥不完全相同，避免伸出桥与其他螺旋金属短接。
- `P1/P2` pin 应放在 `m5`。
- 频率扫描目标：`3.0, 3.5, 4.0, 4.5 GHz`，`3.75 GHz` 用 `3.5/4.0 GHz` 复数插值得到。

## 代理模型计划

单电感 L/Q 模型只覆盖 `1-6 nH`。

输入几何特征：

- `r0`
- `W`
- `S`
- `N`
- 派生特征：`pitch = W + S`
- 派生特征：`outer_radius = r0 + N * pitch`
- 派生特征：`fill_ratio`

提取流程：

- 由 `.s2p` 转 `Z` 参数。
- 使用差模 `Zdiff = Z11 - Z12`。
- 对 `Zdiff(3.5 GHz)` 和 `Zdiff(4.0 GHz)` 做复数线性插值，得到 `Zdiff(3.75 GHz)`。
- `L@3.75 = imag(Zdiff) / (2*pi*f)`。
- `Q@3.75 = abs(imag(Zdiff) / real(Zdiff))`。
- `Q@3.0` 和 `Q@4.5` 作为辅助检查。

## 本地目录结构

- `repo_lvbobalun/`：`BEWATERo/LVBOBALUN` 的独立 Git 仓库。外层仓库忽略此目录。
- `fdl_first_batch/`：第一批简化命名的单电感 FDL/Python 文件和参数表。
- `vm_probe/`：VM、Cadence、EMX 调试脚本和工艺映射文件。
- `PROJECT_CONTEXT.md`：给后续对话读取的主上下文文件。

## 当前 repo_lvbobalun 状态

内层仓库 `repo_lvbobalun/` 当前有未提交变更，包含：

- 修改：`START_HERE.md`
- 修改：`code/filter_parameterization/modules/L1L3_optimization/_gen_single_inductor.py`
- 修改：`code/filter_parameterization/modules/L1L3_optimization/fdl_versions/single_inductor_geometry.py`
- 修改：`docs/parameterization.md`
- 修改：`docs/ultraem_batch_sim.md`
- 新增：多个 `single_inductor_*12gon*.py`
- 新增：`single_inductor_lq_model.py`
- 新增：`runs/`
- 新增：`tools/`

处理原则：进入 `repo_lvbobalun/` 内单独提交，不从外层仓库直接提交它。

## VM / SSH

VM 已可通过 SSH 连接。当前辅助脚本：

- `vm_probe/ssh_vm.py`

当前脚本内记录了本地 VM 连接信息。不要把密码复制到公开文档或远程仓库。

已知 VM 信息：

- VM 用户：`IC`
- 最近可用 IP：`192.168.37.128`
- EMX 安装目录：`/home/IC/EDA/INTEGRAND60`
- EMX 命令：`/home/IC/EDA/INTEGRAND60/bin/emx`
- `emx --version` 已返回 `EMX version 6.0`

## Cadence / EMX 配置

EMX Virtuoso interface 已配置：

- Interface 目录：`/home/IC/EDA/INTEGRAND60/virtuoso_ui/emxinterface`
- `.cdsinit`：`/home/IC/EDA/.cdsinit`
- `emxconfig.il`：
  - `EMX_interface_path="/home/IC/EDA/INTEGRAND60/virtuoso_ui/emxinterface"`
  - `EMX_path="/home/IC/EDA/INTEGRAND60/bin"`
  - `EMX_process_name="fdl_stack.proc"`

FDL 匹配 EMX process 文件：

- Host：`vm_probe/fdl_stack.proc`
- VM：`/home/IC/EDA/INTEGRAND60/virtuoso_ui/emxinterface/processes/fdl_stack.proc`

工艺映射要点：

- `M4 = L64T0`
- `M5 = L65T0`
- `V4 = L73T0`
- M4/M5 厚度：`3 um`
- M4/M5 RPSQ：`0.0062`
- V4：`0.026 Ohms/via`
- substrate：`725 um`，`er=11.9`，`4000 ohm-cm`

## 已生成 Cadence 版图

Cadence layout 已生成并能打开：

- Library：`codex_fdl_bridge`
- Cell：`single_inductor_12s_3p5t_test`
- View：`layout`
- 生成脚本：`vm_probe/single_inductor_12s_3p5t_test.il`
- 打开脚本：`vm_probe/geopen_single_inductor.il`

GDS 导出已成功：

- VM run dir：`/home/IC/EDA/emx_runs/single_inductor_12s_3p5t_test`
- GDS：`single_inductor_12s_3p5t_test.gds`
- strmout：`0` errors / `0` warnings

## 下一步 EMX 仿真

下一步应在 VM 内对已导出的 GDS 跑 EMX。

候选参数：

- GDS：`/home/IC/EDA/emx_runs/single_inductor_12s_3p5t_test/single_inductor_12s_3p5t_test.gds`
- Structure：`single_inductor_12s_3p5t_test`
- Process：`/home/IC/EDA/INTEGRAND60/virtuoso_ui/emxinterface/processes/fdl_stack.proc`
- 频点：`3e9 3.5e9 4e9 4.5e9`
- Port：优先尝试 `-p Pdiff=P1:P2`
- 输出：Touchstone `.s2p`

如果 `P1:P2` 端口语法失败，先用 `emx --help` 或最小测试确认 EMX6.0 对 differential / label port 的实际参数格式。

## Git 管理约定

外层仓库用于保存当前对话工作区上下文和可复现辅助文件。

默认追踪：

- `README.md`
- `PROJECT_CONTEXT.md`
- `.gitignore`
- `fdl_first_batch/**/*.py`
- `fdl_first_batch/**/*.csv`
- `vm_probe/*.py`
- `vm_probe/*.il`
- `vm_probe/*.proc`

默认忽略：

- 截图：`*.png`
- 临时提取文本：`tmp_*.txt`、`ultraem_*.txt`
- 仿真输出：`*.s2p`、`*.gds`、`*.raw`、`*.psf`
- 内层仓库：`repo_lvbobalun/`


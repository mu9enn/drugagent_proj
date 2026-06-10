# Developer Guide

适合读者：准备修改代码、入口、contract、测试或文档的开发者/Codex  
依赖文档：[主线架构](architecture.md)、[Contract Guide](contracts/contract-guide.md)  
相关入口：[入口目录](entrypoints.md)  
相关 contract：`docs/contracts/catalog.json`  
最后更新意图：提供可执行的变更前检查清单，保护现有主线行为

## 三块职责

- `molclaw-kg/`：工具卡、图边、provenance、KG sampling。
- `mol-pipeline/`：任务执行、raw session、评测、质量门、ReAct producer。
- `slime/drug_agent/`：数据验证/转换和离线训练插件；Slime core 仍按 Slime 语义运行。

Producer-owned contract 应在 owner 子项目中修改；不要先搬进新的 monorepo shared package。

## 变更检查表

| 要改什么 | 修改前必须做 | 同步内容 |
| --- | --- | --- |
| postprocess | 读 postprocess README/schema/tests；确认 accepted/rejected 行为 | golden samples、schema report、contract docs |
| ToolRL reward | 读 converter、normalization、reward tests、offline policy | reward tests、风险说明；不得误接 executor |
| GAD data | 读 `gad/data.py`、README、Stage2/3 reader | state boundary、doc-only 风险、测试 |
| entrypoint | 确认运行目录与真实副作用 | `docs/entrypoints.md` 和对应 runbook |
| contract | 查 producer/consumer/validator | `catalog.json`、定义、validator、golden sample |
| legacy 删除 | 先 `git grep` 所有引用 | `docs/legacy-removals.md` 的原因和恢复方式 |

## 新脚本与副作用

新增脚本必须在入口目录标注 status，并从以下标签中选择真实副作用：
`read-only`、`local-write`、`remote`、`ray-gpu`。会真实调用 MCP 的脚本必须明确是
online debug/evaluation，要求显式 opt-in，不能成为 formal training 依赖。

## Golden Sample

Golden sample 应覆盖关键结构、字段、顺序、状态边界和失败原因；不比较时间戳、绝对路径
等非确定字段。doc-only contract 的样本用于保护 reader 行为，不应被描述成完整 schema。

## 检查边界

- `make check` = 静态检查 + contract tests + active tests。
- `make test-contracts` = 根 contract/golden tests。
- `make test-active` = 三个子项目当前 active 测试集合。
- 这些目标不得启动训练、Ray、GPU、Claude、MCP、模型加载或远程请求。

## 不可混入文档任务的变更

训练参数/行为、清洗规则、reward、采样、质量门、真实 MCP executor、模型路径、
worker 环境路径、默认值、统一业务 CLI、shared core 抽象都必须作为独立代码任务评审。

下一步应该读：[Contract Guide](contracts/contract-guide.md)  
如果要修改相关代码，请先读：[深度主流程](mainline-flow-deep-dive.md)

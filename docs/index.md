# DrugAgent Documentation Index

适合读者：owner、新成员、数据/训练工程师、排障人员  
依赖文档：[主线架构](architecture.md)、[入口目录](entrypoints.md)  
相关入口：所有入口的状态与副作用以 `docs/entrypoints.md` 为准  
相关 contract：唯一索引是 `docs/contracts/catalog.json`  
最后更新意图：提供短、稳定的文档入口，避免误跑有副作用的脚本

## 从这里开始

| 目标 | 首先阅读 | 然后阅读 |
| --- | --- | --- |
| owner 检查当前主线 | [主线架构](architecture.md) | [深度主流程](mainline-flow-deep-dive.md)、[已知问题](known-issues.md) |
| 新成员理解项目 | [阅读地图](reading-map.md) | [术语表](glossary.md)、[数据生命周期](data-lifecycle.md) |
| 生成和后处理数据 | [数据生成 runbook](runbooks/data-generation-and-postprocess.md) | [数据生命周期](data-lifecycle.md) |
| 训练 SFT / ToolRL / GAD / OPD | [训练方法](training-methodology.md) | [训练 runbook](runbooks/training-sft-toolrl-gad.md) |
| 调试 MCP / online evaluation | [在线调试 runbook](runbooks/debug-and-online-evaluation.md) | [离线训练边界](../slime/drug_agent/OFFLINE_TRAINING_POLICY.md) |
| 改 contract / postprocess / reward | [Contract Guide](contracts/contract-guide.md) | [开发者指南](developer-guide.md) |
| 排查环境和运行故障 | [环境与资源](runbooks/environment-and-resources.md) | [Troubleshooting](runbooks/troubleshooting.md) |

## 不要从导航页猜入口

入口的 `status` 与 `read-only`、`local-write`、`remote`、`ray-gpu` 副作用只在
[入口目录](entrypoints.md) 维护。运行前必须查该表。

本仓库文档不保证 worker-local checkpoint、`$VERL_DATA` 内容、真实 MCP
服务、provider 配额、GPU/Ray/SGLang 可用性。静态仓库检查也不会验证这些外部状态。

## 事实源

- 架构与职责边界：[主线架构](architecture.md)
- 入口与副作用：[入口目录](entrypoints.md)
- Contract 索引：`docs/contracts/catalog.json`
- 当前问题：[已知问题](known-issues.md)
- 历史删除与恢复：[Legacy Removals](legacy-removals.md)
- 主线整理时的结果：[Mainline Cleanup Report](mainline-cleanup-report.md)

下一步应该读：[阅读地图](reading-map.md)  
如果要修改相关代码，请先读：[开发者指南](developer-guide.md)

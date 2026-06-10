# Debug And Online Evaluation Runbook

适合读者：需要真实 MCP 健康检查、trajectory replay 或单任务推理调试的工程师  
依赖文档：[离线训练边界](../../slime/drug_agent/OFFLINE_TRAINING_POLICY.md)  
相关入口：[入口目录](../entrypoints.md) 的 Online Evaluation And Debug 表  
相关 contract：`complete_session`、`react_sft`；debug 不定义新的训练 contract  
最后更新意图：隔离真实工具调试与 formal training，避免入口误用

## 允许真实 MCP 的入口

| 入口 | 用途 | 主要副作用 |
| --- | --- | --- |
| `debug_mcp_tools.py` | MCP connectivity/tool smoke | remote MCP |
| `debug_replay_trajectory.py` | replay 历史 tool calls | local-write、remote MCP |
| `debug_one_task.py` | 单模型任务真实工具测试 | local-write、remote MCP、可能 GPU/SGLang |

这些入口要求显式 `DRUG_AGENT_ALLOW_TOOL_ENV=1`，且进程不能处于 offline training。
启用前确认目标 MCP、凭据、测试数据和写入目录；不要在 formal training runtime env 中设置。

## 推荐调试顺序

1. 先读入口脚本并查 `entrypoints.md` 的副作用。
2. 用 MCP tool smoke 验证 connectivity 和工具列表。
3. 需要复现历史 action 时再 replay trajectory。
4. 最后进行 one-task model debug；它可能启动/加载 SGLang/GPU。
5. 保存调试产物，但不要把其入口或在线 observation 接回 formal training。

## 为什么不属于 Formal Training

Formal training 的 state 和 observation 已固定，student action 只被评分或用于 loss。
Online debug 会执行 action 并获取新 observation，因此其数据分布、副作用和失败模式不同。
仓库当前没有 production online-evaluation launcher。

下一步应该读：[Troubleshooting](troubleshooting.md)  
如果要修改相关代码，请先读：[开发者指南](../developer-guide.md)

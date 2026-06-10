# Glossary

适合读者：新成员、reviewer、需要统一术语的文档作者  
依赖文档：[主线架构](architecture.md)  
相关入口：[入口目录](entrypoints.md)  
相关 contract：[Contract Catalog](contracts/README.md)  
最后更新意图：减少对当前项目术语的重复解释

| 术语 | 当前项目含义 |
| --- | --- |
| ReAct trajectory | reasoning/action/observation/final answer 组成的历史交互轨迹 |
| assistant turn | 一次 assistant message；可包含 thought、tool call 或 final answer |
| observation | 历史 tool result，formal training 中是不可变上下文 |
| tool_call | assistant 产生的结构化工具调用文本/action |
| final_answer | ReAct 序列的最终回答 |
| MolClaw tool | 目标 MolClaw MCP 工具；postprocess 会过滤非目标工具 |
| MCP | 工具服务协议；只有明确 online debug/evaluation 可真实调用 |
| raw session | 执行器原始事件记录，尚未成为训练样本 |
| `complete_session.jsonl` | claude_agent 写出的 raw stream-json session |
| `trajectory_exporter` | 从 raw session 重建步骤、指标和接受状态 |
| `scan_molclaw_usage` | 汇总 accepted session、MolClaw usage 和任务指标 |
| `post_process_sft` | 将候选 session 确定性转为 ReAct SFT/RL prompt |
| ReAct-SFT | 以完整 ReAct messages 为单位的监督训练视图 |
| ToolRL step | 某 assistant tool-call decision 前的 fixed state 与 reference action |
| GAD decision state | 某 tool-call/final-answer decision 前的 fixed state |
| negative candidate | current student 对同一 GAD state 生成的候选响应 |
| offline training | 生成 action 只用于 loss/reward，不执行并获取新 observation |
| online debug | 显式 opt-in、可能调用真实 MCP 的调试 |
| entrypoint side effect | 入口的 read-only/local-write/remote/ray-gpu 行为标签 |
| contract | producer 与 consumer 共享的数据形状/语义约定 |
| catalog | `docs/contracts/catalog.json`，contract 的唯一索引 |
| producer / consumer | 写出 / 读取某 contract 的模块或阶段 |
| validator | 可执行的结构或协议检查；不等同于所有语义正确 |
| quarantine | 未满足硬清洗/验证条件、与 accepted 输出隔离的数据 |
| sidecar | 与主数据并列保存的审计、provenance、报告或解释数据 |
| artifact handle | 替代本地绝对路径的稳定占位符 |
| TP / DP | tensor / data parallel size |
| RBS / GBS | rollout / global batch size |

下一步应该读：[FAQ](faq.md)  
如果要修改相关代码，请先读：[开发者指南](developer-guide.md)

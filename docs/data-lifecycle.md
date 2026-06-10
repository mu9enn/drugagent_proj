# Data Lifecycle

适合读者：修改数据生产、清洗、contract 或训练消费逻辑的工程师  
依赖文档：[深度主流程](mainline-flow-deep-dive.md)  
相关入口：[数据生成 runbook](runbooks/data-generation-and-postprocess.md)  
相关 contract：[Contract Catalog](contracts/README.md)  
最后更新意图：说明每种数据形态的 owner、最小形状、验证和破坏性变更

```text
KG artifacts -> task spec -> raw complete_session.jsonl
-> trajectory candidates -> accepted/rejected/quarantine
-> ReAct SFT -> ToolRL steps / GAD decisions
-> training logs and checkpoints
```

| 数据形态 | 典型路径/名称 | 最小字段或 contract | Producer -> Consumer | Validator |
| --- | --- | --- | --- | --- |
| KG internal artifacts | `molclaw-kg` run outputs | ToolCard/edge/provenance models | KG stages -> KG stages | code models |
| Grounded graph sample | `sample_success_v2.jsonl` | `trajectory_v2_graph` | KG Stage3 -> KG adapter | KG adapter builder |
| KG task spec | adapter output | `kg_task_spec_v0.2` | KG adapter -> task execution | doc-only |
| Raw session | `complete_session.jsonl` | stream events | claude_agent -> exporter/postprocess | doc-only |
| Trajectory exports | `trajectories/*.jsonl` | steps, metrics, acceptance | exporter -> scan | doc-only |
| Candidate decisions | accepted/rejected/stage2 rejection/quarantine | reason + source identity | quality gates -> postprocess/operator | implementation checks |
| ReAct SFT | `sft_outputs/mcp_sft_all/`, `mcp_sft_all.jsonl` | `schema_version`, `id`, `messages` | postprocess -> SFT/ToolRL/GAD | SFT validator |
| RL prompt | `mcp_rl_prompts_all.jsonl` | implementation-implied | postprocess -> prompt consumers | doc-only |
| ToolRL step | `*.toolrl_steps.jsonl` | `prompt`, `label`, `metadata`, targets | ToolRL converter -> ToolRL | ToolRL validator |
| GAD decision | `gad_steps.jsonl` | state, teacher response, label, metadata | GAD converter -> Stage2/3 | doc-only |
| GAD negative/pair | `stage2_negatives.jsonl` | teacher/current student pair context | Stage2 rollout -> discriminator | implementation checks |
| Training outputs | `$VERL_DATA/...runs`, configured save dirs | logs/checkpoint-specific files | Slime/GAD/OPD -> operator/resume | worker runtime |

## 正文、Metadata 与 Sidecar

- ReAct-SFT 训练正文保持最小：`schema_version`、`id`、`messages`。
- provenance、清洗动作、审计摘要、路径映射和 rejection reason 应留在 report/sidecar。
- 时间戳、绝对 worker 路径等非确定字段不应成为 golden sample 的逐字比较目标。
- raw session 与 trajectory export 是证据层，不应直接冒充已清洗训练正文。

## 关键破坏性变更

| 变更 | 风险 | 修改前必须确认 |
| --- | --- | --- |
| 重命名/删除必需字段 | consumer 读取失败或静默丢数据 | producer、全部 consumer、validator、golden sample |
| 改 ReAct tag 或消息边界 | SFT mask、ToolRL/GAD state 切分变化 | protocol parser、validators、训练消费 |
| 把 sidecar 字段移入正文 | 训练数据膨胀或泄漏非确定信息 | schema 文档和训练输入约束 |
| 改 accepted/rejected 条件 | 数据清洗和质量门行为变化 | 本轮文档任务禁止 |
| 改路径清洗/artifact handle | 可能泄漏 worker 路径或破坏下游 | postprocess tests 与 schema report |
| 改 ToolRL/GAD state boundary | future observation/target 泄漏 | converters、offline policy、tests |

## Contract 维护动作

新增字段优先做向后兼容的 optional field；删除或语义变化先升级版本并保留
legacy-read-compatible 路径。`docs/contracts/catalog.json` 只记录真实存在的 model、
validator 或 doc-only contract，不用文档伪造 schema。

下一步应该读：[Contract Guide](contracts/contract-guide.md)  
如果要修改相关代码，请先读：[开发者指南](developer-guide.md)

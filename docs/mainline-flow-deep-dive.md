# Mainline Flow Deep Dive

适合读者：需要理解端到端输入、动作、输出和失败边界的工程师  
依赖文档：[主线架构](architecture.md)、[术语表](glossary.md)  
相关入口：[入口目录](entrypoints.md)  
相关 contract：[Contract Catalog](contracts/README.md)  
最后更新意图：用同一结构描述当前主线，不改变或抽象现有逻辑

## 总览

```text
MolClaw tool sources -> tool cards -> adjudicated graph -> grounded tasks
-> mol-pipeline raw sessions -> trajectory quality gate -> ReAct data
-> SFT / ToolRL / GAD / OPD offline training
```

## 1. KG Stage1：Snapshot、Skills、Tool Cards

- **输入**：工具快照、skills、配置与 prompt。
- **入口**：`molclaw-kg/scripts/run_full_pipeline.sh` 或 `molclaw_kg` CLI。
- **关键动作**：生成 snapshot/doc chunks；抽取 ToolCard。ToolCard 记录工具标识、
  标题、摘要、主/次 stage、别名、输入输出 slot、可连接 slot、输入需求集合、
  前置条件、副作用和 `needs_review`。
- **输出/消费方**：tool cards 与 provenance，供 Stage2 构造候选边。
- **关键 contract**：`molclaw_kg_internal_models`。
- **失败/跳过**：来源缺失、解析失败、远程抽取失败或审核标记。
- **不负责**：不执行 MolBench task，不产生训练样本。
- **证据**：`molclaw-kg/src/molclaw_kg/pipeline.py`、`models.py`。

## 2. KG Stage2：Candidate、Adjudication、Graph Export

- **输入**：ToolCard、stage taxonomy、edge ontology。
- **入口**：Stage1/2 orchestration 与 `molclaw_kg` CLI。
- **关键动作**：按 stage 和 slot 可连接性产生 candidate pair；判定 relation status、
  direct transition、edge types、slot mappings、未满足必需输入、证据、理由和置信度。
- **输出/消费方**：瘦身主图供 Stage3；sidecar 保留解释、证据、provenance 和审计细节。
- **关键 contract**：内部 models。Edge type 包括生成完整/部分输入、预处理、格式转换、
  参数化、过滤、排序评分、验证、细化、报告总结和替代关系。
- **失败/跳过**：候选不连接、必需输入未满足、adjudication 失败或需人工复核。
- **不负责**：stage taxonomy 用于剪枝，不等同于 confidence score；主图不承载全部调试字段。
- **证据**：`pipeline.py`、`models.py`、`configs/edge_ontology_v1.yaml`。

## 3. KG Stage3：Science-KB Grounding 与采样

- **输入**：Stage2 图、local Science-KB、采样配置。
- **入口**：`molclaw-kg/scripts/run_sample_questions.sh`。
- **关键动作**：基于图路径和 Science-KB grounding 生成问题并验证图轨迹。
- **输出/消费方**：`trajectory_v2_graph` 样本，供 mol-pipeline KG adapter 转为 task spec。
- **关键 contract**：`trajectory_v2_graph`；当前 simple mode 是主线，
  `dag_closure`/linear debug 属于兼容或调试路径。
- **失败/跳过**：grounding/验证不通过、路径不满足、修复仍失败。
- **不负责**：不执行任务，不产生 MCP session。
- **证据**：`run_sample_questions.sh`、Stage3 sampler/validator、KG adapter schema 文档。

## 4. Task Adapter 与执行

- **输入**：MolBench CSV、KG sampled task 或 E2E 构造任务。
- **入口**：`mol-pipeline/pipeline/kg/run_kg_pipeline.sh`、
  `pipeline/e2e/run_e2e_pipeline.sh`、`pipeline/claude_agent/run_execute.sh`。
- **关键动作**：adapter 形成执行输入；claude_agent 执行任务并写 raw artifacts。
- **输出/消费方**：run config/summary、question、prompt、`complete_session.jsonl`、
  parsed answer、run metadata 和预测；供评测与 postprocess。
- **关键 contract**：`kg_task_spec_v0.2`、`complete_session`。
- **失败/跳过**：输入不合法、provider/MCP 错误、runner error。
- **不负责**：执行器只写 raw，不负责训练清洗或 reward。
- **证据**：`pipeline/kg/README.md`、`pipeline/e2e/README.md`、
  `pipeline/claude_agent/README.md`。

## 5. Raw Session

- **输入**：执行过程中的 stream-json events。
- **入口**：由 claude_agent 写入，不应手工构造为训练正文。
- **关键动作**：按事件保留 assistant text/thinking、tool use、tool result 和 runner error。
- **输出/消费方**：`complete_session.jsonl`，供 trajectory exporter 重建步骤。
- **关键 contract**：`complete_session` 当前为 `doc-only`。
- **失败/跳过**：损坏 JSON 行可能被跳过；末行 `[runner-error]` 不可被接受。
- **不负责**：不是 ReAct-SFT 样本，也不保证每次 tool use 都有结果。
- **证据**：claude_agent README、`trajectory_exporter.py`。

## 6. Postprocess 三段链

- **输入**：raw run/session 与评测信息。
- **入口**：`mol-pipeline/scripts/run_postprocess.sh`。
- **关键动作**：`trajectory_exporter` 重建/评测 trajectory；
  `scan_molclaw_usage` 汇总 accepted session 与任务指标；
  `post_process_sft` 形成确定性 ReAct SFT/RL prompt。
- **输出/消费方**：accepted/rejected、usage CSV、stage2 rejection、SFT/RL prompt、
  cleaning/schema reports，供 Slime 数据转换与训练。
- **关键 contract**：`trajectory_exports`、`react_sft`、`rl_prompt`。
- **失败/跳过**：runner error；VS/AC/PF 缺必需 task metrics；非 MolClaw/orphan result；
  schema/protocol 不合法。
- **不负责**：不引入 reward，不重新排序 VS，不改变 observation 的错误状态。
- **证据**：`pipeline/postprocess/README.md` 与三段实现文件。

## 7. ReAct-SFT 数据

- **输入**：accepted MolClaw sessions。
- **关键动作**：assistant thought -> `<thought>`；tool use -> `<tool_call>`；
  result -> `<observation tool_name="...">`；结论 -> `<final_answer>`。
  本地绝对路径变 artifact handle，fpocket observation 会压缩。
- **输出/消费方**：正文仅 `schema_version`、`id`、`messages`；审计/provenance 放 sidecar/report。
- **关键 contract**：`drug_agent_sft_react_json_v1`，由 Slime validator 校验。
- **不负责**：不把时间戳、路径和审计字段强塞入训练正文。
- **证据**：`react_sft_schema_v1.md`、`post_process_sft.py`。

## 8. ToolRL 数据

- **输入**：ReAct-SFT records。
- **关键动作**：对每个含 MolClaw tool call 的 assistant turn，截取此前 messages 为
  fixed state，并保存 reference assistant/tool calls。
- **输出/消费方**：`prompt`、`label`、`metadata`、`target_assistant`、
  `target_tool_calls`；供 offline ToolRL。
- **关键 contract**：`toolrl_step_v1`。
- **失败/跳过**：无 messages、解析失败、无 MolClaw call、空 state。
- **不负责**：不执行生成动作。
- **证据**：`convert_react_to_toolrl_steps.py`、ToolRL README。

## 9. GAD 数据与训练

- **输入**：cleaned ReAct-SFT 与已有 SFT student checkpoint。
- **关键动作**：保留 tool-call 和 final-answer decision state；Stage2 生成当前 student
  negatives、零 reward 缓存并做 BT warmup；Stage3 用独立 discriminator
  `/score-and-update` 与 rule components 做 GRPO。
- **输出/消费方**：GAD steps、negative pairs、discriminator/student checkpoints 和日志。
- **关键 contract**：`drug_agent_gad_step_v1`，当前 `doc-only`。
- **失败/跳过**：parse 失败、非 MolClaw 工具、无 decision、无有效 state。
- **不负责**：任何 stage 都不执行生成的 tool call。
- **证据**：`slime/drug_agent/gad/data.py`、GAD README。

## 10. Slime Formal Training 与 Online Debug

- **输入**：固定离线数据、worker-local model/checkpoint。
- **入口**：SFT、ToolRL、GAD、OPD wrappers；状态见入口目录。
- **关键动作**：SFT teacher forcing；ToolRL reference-action rule reward + GRPO；
  GAD discriminator + GRPO；OPD frozen teacher KL + GRPO。
- **输出**：训练日志和 checkpoint。
- **边界**：formal training source `offline_training_env.sh`，生成动作绝不换取新 observation。
  真实 MCP 仅允许在显式 online debug utilities 中。
- **证据**：`slime/drug_agent/OFFLINE_TRAINING_POLICY.md`、各方法 README/脚本。

下一步应该读：[数据生命周期](data-lifecycle.md)  
如果要修改相关代码，请先读：[开发者指南](developer-guide.md)

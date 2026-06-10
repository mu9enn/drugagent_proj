# Data Generation And Postprocess Runbook

适合读者：准备生成 MolBench/KG/E2E raw data 并形成 ReAct 数据的操作人员  
依赖文档：[数据生命周期](../data-lifecycle.md)、[入口目录](../entrypoints.md)  
相关入口：KG/E2E/claude_agent、evaluate、`run_postprocess.sh`、`run_llm_clean.sh`  
相关 contract：`trajectory_v2_graph`、`kg_task_spec`、`complete_session`、`react_sft`  
最后更新意图：按任务说明产物与检查点，不复制项目级命令细节

## 1. 选择任务来源

- KG sampled task：先按 `molclaw-kg` Stage3 生成并验证 `trajectory_v2_graph`，再由
  KG adapter 构造 task spec。
- MolBench task：使用 `run_molbench_workflow.sh` 构造任务数据。
- E2E task：使用 E2E pipeline 构造并执行。

先查入口目录：上述入口可 `local-write`，生成/执行阶段还可能 `remote`。

## 2. 执行与 Raw 产物

`pipeline/claude_agent/run_execute.sh` 只负责执行任务和写 raw artifacts，包括 run config、
run summary、question、prompt、`complete_session.jsonl`、parsed answer、run metadata 和
predictions。它不负责训练清洗、reward 或 accepted/rejected 判定。

## 3. 评测与 Postprocess

VS/AC/PF 使用 evaluate 入口形成任务指标。之后固定三段链是：

```text
trajectory_exporter -> scan_molclaw_usage -> post_process_sft
```

`trajectory_exporter` 重建 trajectory 和质量门；`scan_molclaw_usage` 收集 accepted
session 与指标；`post_process_sft` 形成 ReAct SFT 和 RL prompt。此链不引入 reward。

## 4. 阅读输出

- `accepted.jsonl`：通过 trajectory quality gate 的候选。
- rejected / `stage2_rejected_candidates.jsonl`：带拒绝原因，不能当训练正文。
- quarantine / validator quarantine：硬清洗或验证未通过。
- `molclaw_usage_summary.csv`：任务指标和使用汇总。
- `sft_outputs/mcp_sft_all/`、`mcp_sft_all.jsonl`：ReAct-SFT。
- `mcp_rl_prompts_all.jsonl`：RL prompt contract，目前 doc-only。
- cleaning/schema reports：审计与验证证据。

## 5. 下游可用性检查

确认 session 不以 runner error 结束；VS/AC/PF accepted 数据含必需 task metrics；
SFT 正文只含最小字段；运行 SFT validator，检查 rejected/quarantine 和 schema report。
LLM clean 可能 remote；`--skip-llm` 的实际行为以其脚本为准。任何清洗规则修改都不是
runbook 操作。

下一步应该读：[数据生命周期](../data-lifecycle.md)  
如果要修改相关代码，请先读：[开发者指南](../developer-guide.md)

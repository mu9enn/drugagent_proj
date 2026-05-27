# mol-pipeline

统一分子任务执行与后处理工程（`vs/ac/pf/e2e/kg`），当前采用硬切后的 `pipeline/` 架构。

## 目录结构

- `pipeline/claude_agent`：只负责执行任务与落盘 raw 会话（`complete_session.jsonl` 等）
- `pipeline/evaluate`：只负责 `vs/ac/pf` 评测
- `pipeline/postprocess`：后处理（trajectory 重建、molclaw usage 汇总、SFT/RL 转换）
- `pipeline/e2e`：E2E 数据构建与运行入口
- `pipeline/kg`：KG-sampled 数据构建、运行与审计
- `results/`：统一运行产物根目录
- `molbench/`：统一数据集目录
- `skills/skills_vs`、`skills/skills_full`：统一技能与系统提示目录

## 一键入口

执行（只跑并落盘 raw）：

```bash
bash pipeline/claude_agent/run_execute.sh --run-dataset --task vs --dataset-csv molbench/molbench-vs-30.csv
```

评测（仅 `vs/ac/pf`）：

```bash
bash pipeline/evaluate/run_evaluate.sh results/<run_dir> vs
```

后处理（全量，从 raw 会话重建）：

```bash
bash pipeline/postprocess/run_postprocess.sh --results-root results
```

`run_postprocess.sh` 固定流程：

1. `trajectory_exporter.py`
2. `scan_molclaw_usage.py`
3. `post_process_sft.py`

输出位于：

- `results/postprocess_candidates/mcp_sft_all.jsonl`
- `results/postprocess_candidates/mcp_rl_prompts_all.jsonl`
- `results/postprocess_candidates/sft_outputs/*`

## 规则约定

- 不引入 reward 字段。
- `vs/ac/pf` 保留单样本指标（如 `top3_hit_num/is_correct/f1`）。
- `e2e/kg` 不做任务质量门，但必须执行完成（`return_code==0 && !timed_out && session存在`）。
- **全任务 accepted 必须满足 `molclaw_usage > 0`**，否则标记 `missing_molclaw_usage`。
- `--answer-hit-only` 仅在 `post_process_sft.py` 阶段作用于 `vs/ac/pf`，不影响 `kg/e2e`。

## 常用工作流

生成并下发 AC/VS/PF：

```bash
bash scripts/run_molbench_workflow.sh --seed 42 --n-cases 30
```

构建与运行 KG：

```bash
python pipeline/kg/scripts/build_kg_task_dataset.py \
  --kg-run-dir /path/to/molclaw-kg/runs/<run_id> \
  --output-dir pipeline/kg/data/<run_id>

bash pipeline/kg/run_kg_pipeline.sh \
  --kg-task-file pipeline/kg/data/<run_id>/kg_sampled_tasks.jsonl \
  --n-cases 1
```

构建与运行 E2E：

```bash
bash pipeline/e2e/run_e2e_pipeline.sh --questions E2E-Q01,E2E-Q02
```

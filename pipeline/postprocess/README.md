# Postprocess Module

`pipeline/postprocess` 负责后处理全链路，且以 raw `complete_session.jsonl` 为唯一真源。

## 一键运行

```bash
bash pipeline/postprocess/run_postprocess.sh --results-root results
```

固定阶段：

1. `trajectory_exporter.py`：重建 `trajectories/*`
2. `scan_molclaw_usage.py`：汇总 accepted 候选会话（全任务）
3. `post_process_sft.py`：生成统一 SFT/RL 数据

## 关键规则

- `vs/ac/pf`：保留原任务质量门。
- `kg/e2e`：按完成性门控（`return_code==0 && !timed_out && session存在`）。
- **全任务统一要求 `molclaw_usage_count > 0`**，否则 `missing_molclaw_usage`。
- 不引入 reward 字段。
- `--answer-hit-only` 仅作用于 `vs/ac/pf`，不影响 `kg/e2e`。

## 输出

- `results/postprocess_candidates/molclaw_usage_summary.csv`
- `results/postprocess_candidates/sft_outputs/mcp_sft_all.jsonl`
- `results/postprocess_candidates/sft_outputs/mcp_rl_prompts_all.jsonl`
- `results/postprocess_candidates/sft_outputs/rejected_samples.jsonl`

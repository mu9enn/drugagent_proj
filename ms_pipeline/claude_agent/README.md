# Claude Agent Pipeline（MolBench-VS）

本目录负责 MolBench-VS 的 agent 执行、轨迹落盘、轨迹数据导出。

## 1. 脚本职责

## `run_claude.py`（主执行真源）

用途：
- 读取 CSV 数据集，逐样本调用 Claude CLI
- 支持单样本多 rollout
- 产出 session、解析答案、预测 JSON
- 自动执行完成性检查
- 自动触发 trajectory 导出（可关闭）

关键参数：
- `--dataset-csv`
- `--skills-root`
- `--results-root`
- `--provider`
- `--claude-bin`
- `--start-row`
- `--end-row`
- `--limit`
- `--num-rollouts`
- `--parallel-rollouts`
- `--rollout-seed-base`
- `--skip-provider-switch`
- `--no-export-trajectories`

关键行为：
- 每条样本都会写 `question.json`（包含 `candidates`）
- 每个 rollout 都写：`complete_session.jsonl`、`parsed_answer.json`、`run_meta.json`、`prompt.txt`
- 完成后写：
  - `preds/molbench_vs/molbench_vs.json`（rollout 1 兼容口径）
  - `preds/molbench_vs/rollouts/rollout_XXXX.json`
  - `completion_report.json`

## `launch_claude.sh`（环境与入口封装）

用途：
- provider 切换（`cc-switch`）
- MCP 服务检查/注册
- 将参数转发到 `run_claude.py`

模式：
- 单样本模式（默认）
- 数据集模式（`--run-dataset`）

数据集相关新增参数：
- `--num-rollouts`
- `--parallel-rollouts`
- `--rollout-seed-base`
- `--no-export-trajectories`

## `test_flow_claude.sh`（推理+评估编排）

用途：
- 调 `launch_claude.sh --run-dataset`
- 抓取 `RESULTS_DIR`
- 调 `evaluate/run_eval_bench.py`

参数：
- `$1 PROVIDER`（默认 `qwen-397b`）
- `$2 CLAUDE_BIN`（默认 `claude`）
- `$3 LIMIT`（默认 `0`）
- `$4 NUM_ROLLOUTS`（默认 `1`）
- `$5 PARALLEL_ROLLOUTS`（默认 `1`）

## `trajectory_exporter.py`（轨迹标准化导出器）

输入：
- `results/molbench_vs_*_run_*/`（`run_claude.py` 产物）

输出：
- `trajectories/trajectory_level.jsonl`
- `trajectories/step_level.jsonl`
- `trajectories/accepted.jsonl`
- `trajectories/rejected.jsonl`
- `trajectories/dataset_summary.json`

质量门（accepted/rejected）：
- parse error
- 空候选集
- 预测长度与候选长度不一致
- 重复预测
- 预测不在候选集中
- RDKit 不可用（拒绝）

奖励口径（当前）：
- `reward_outcome = 2 * top3_hit_num + top10_hit_num`
- 仅在 `step_level` 最后一步打 reward

可审计分层（artifact audit）：
- `tool_generated.*`：工具调用/工具结果（含 docking 次数）
- `llm_generated.*`：assistant 文本块与亲和力提及统计

## `test_claude.sh`（CLI/MCP 健康检查）

用途：快速验证 Claude CLI 与 MCP 基础连通性。

---

## 2. 执行关系

```text
test_flow_claude.sh
  -> launch_claude.sh --run-dataset
    -> run_claude.py
      -> trajectory_exporter.py (默认开启)
  -> evaluate/run_eval_bench.py
```

---

## 3. 常用命令

## 最小链路

```bash
cd /home/sunxiangyu/sunxiangyu/vs_pipeline
bash claude_agent/test_flow_claude.sh qwen-397b claude 1 1 1
```

## 多 rollout

```bash
cd /home/sunxiangyu/sunxiangyu/vs_pipeline
bash claude_agent/test_flow_claude.sh qwen-397b claude 25 4 2
```

## 仅导出轨迹（已有 results）

```bash
python claude_agent/trajectory_exporter.py /path/to/results/molbench_vs_xxx_run_xxx
```

---

## 4. 产物结构示例

```text
results/molbench_vs_qwen_397b_run_20260506_153000/
  run_config.json
  run_summary.jsonl
  completion_report.json
  row0001_idx1/
    question.json
    rollout0001/
      complete_session.jsonl
      parsed_answer.json
      run_meta.json
      prompt.txt
      question.json
  preds/molbench_vs/
    molbench_vs.json
    rollouts/rollout_0001.json
  trajectories/
    trajectory_level.jsonl
    step_level.jsonl
    accepted.jsonl
    rejected.jsonl
    dataset_summary.json
  bench_scores.json
```

---

## 5. 复现风险提示

1. `rdkit` 未安装会导致 trajectory 全拒绝（用于 RL 数据集门控是预期行为）。
2. 外部 MCP 服务不可达会影响工具调用成功率。
3. provider 或 claude 二进制不可用会直接失败。
4. 若模型输出不满足 `<answer>` 规范，`parse_error` 会升高。
5. 多 rollout 并发过高会触发资源/速率瓶颈。

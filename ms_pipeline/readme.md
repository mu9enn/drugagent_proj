# VS Pipeline 改造总览（Agent Trajectory / SFT-DPO-RL 数据化）

## 多任务扩展（VS / AC / PF）

当前已支持三任务运行：
- `vs`：使用 `skills/` + `molclaw-vs`
- `ac`：使用 `skills_full/` + `molclaw-scp`
- `pf`：使用 `skills_full/` + `molclaw-scp`

任务切换由 `claude_agent/launch_claude.sh --task {vs|ac|pf}` 自动完成，无需手动改 MCP 配置。

### 单任务测试

```bash
# VS
bash claude_agent/test_flow_claude.sh qwen-397b claude 3 1 1 vs /home/sunxiangyu/sunxiangyu/get-molbench/outputs/vs/molbench-vs-900.csv

# AC
bash claude_agent/test_flow_claude.sh qwen-397b claude 3 1 1 ac /home/sunxiangyu/sunxiangyu/get-molbench/outputs/ac/molbench-ac-900.csv

# PF
bash claude_agent/test_flow_claude.sh qwen-397b claude 3 1 1 pf /home/sunxiangyu/sunxiangyu/get-molbench/outputs/pf/molbench-pf-900.csv
```

### 三任务并行测试

```bash
bash claude_agent/test_parallel.sh qwen-397b claude 3 1 1
```

## 1. 改造目标

本次改造面向你提出的“`complete_session.jsonl` 向标准化 agent trajectory 数据升级”路线，目标是把当前项目从“可跑通 MolBench-VS”的 PoC，升级为“可持续产出可审计轨迹数据集”的工程基线。

核心目标：
- 单一执行真源（Single Source of Truth）
- 多 rollout 采样能力
- 轨迹标准化导出（trajectory-level + step-level）
- 质量闸门（完整性检查、候选集合审计、格式审计）
- canonical SMILES 评估与审计指标
- 工具产物 vs LLM 文本产物分层记录

---

## 2. 建议点落地状态（逐条）

| 建议点 | 状态 | 落地位置 |
|---|---|---|
| 统一执行入口（`run_claude.py` 为主流程） | 已完成 | `claude_agent/run_claude.py`, `claude_agent/launch_claude.sh`, `claude_agent/test_flow_claude.sh` |
| 多 rollout（K 条轨迹/任务） | 已完成 | `run_claude.py` 参数：`--num-rollouts`, `--parallel-rollouts` |
| 轨迹标准化导出器（normalizer） | 已完成 | `claude_agent/trajectory_exporter.py` |
| 候选集合强制落盘（审计所需） | 已完成 | `question.json`、`preds/*.json` 内均保存 `candidates` |
| 完成性检查门（completion gate） | 已完成 | `run_claude.py` 内 `_check_run_completeness` + `completion_report.json` |
| canonical SMILES 评估 | 已完成（RDKit可用时生效） | `evaluate/eval_runner.py` |
| 过程/格式审计指标 | 已完成（基础版） | `trajectory_exporter.py`, `evaluate/eval_runner.py` |
| 工具产物 vs LLM 文本产物分层 | 已完成（统计层） | `trajectory_exporter.py` 的 `artifact_audit` |
| Token 治理/上限策略 | 本轮未做 | 后续项 |
| 历史结果批量回填导出 | 本轮未做 | 后续项 |
| 过程奖励（step-level dense reward） | 本轮未做（仅 outcome reward） | 后续项 |

---

## 3. 当前主链路（新）

```text
test_flow_claude.sh
  -> launch_claude.sh --run-dataset
    -> run_claude.py
      -> (可选) trajectory_exporter.py
  -> evaluate/run_eval_bench.py
```

### 单一真源原则
- 数据集批处理执行逻辑由 `run_claude.py` 统一承载。
- `launch_claude.sh` 只负责 provider/MCP 初始化与参数转发。
- `test_flow_claude.sh` 只负责“推理 + 评估”编排。

---

## 4. 关键代码变更细节

## 4.1 `claude_agent/run_claude.py`

新增/强化：
- 多 rollout 采样：
  - `--num-rollouts`：每个 row 生成 K 条轨迹
  - `--parallel-rollouts`：单 row 内并发 rollout
  - `--rollout-seed-base`：记录用 seed 基值（当前仅 metadata）
- 结果目录命名包含 provider：
  - `results/molbench_vs_{provider}_run_{YYYYMMDD_HHMMSS}`
- 产物组织：
  - `rowXXXX_idxY/rollout0001...`（K>1）
  - K=1 时保持兼容（不额外加 rollout 子目录）
- 强制保留候选：
  - `question.json` 与预测条目中都保存 `candidates`
- 导出器集成：
  - 默认调用 `trajectory_exporter.py`
  - 支持 `--no-export-trajectories`
- 完整性闸门：
  - 生成 `completion_report.json`
  - 若结构不完整则抛错退出（非零）

新增关键输出：
- `run_config.json`
- `completion_report.json`
- `preds/molbench_vs/rollouts/rollout_XXXX.json`

## 4.2 `claude_agent/launch_claude.sh`

支持两种模式：
- 单样本模式：`--workdir + --prompt-file|--prompt`
- 数据集模式：`--run-dataset`（转发到 `run_claude.py`）

数据集新增参数：
- `--num-rollouts`
- `--parallel-rollouts`
- `--rollout-seed-base`
- `--no-export-trajectories`

保持：
- `cc-switch` provider 切换
- MCP server 注册与验证

## 4.3 `claude_agent/test_flow_claude.sh`

改为薄编排：
- 先调用 `launch_claude.sh --run-dataset`
- 从日志抓取 `RESULTS_DIR=...`
- 再调用 `evaluate/run_eval_bench.py`

新增位置参数：
- 第4位：`NUM_ROLLOUTS`（默认 1）
- 第5位：`PARALLEL_ROLLOUTS`（默认 1）

## 4.4 `claude_agent/trajectory_exporter.py`

导出标准化数据：
- `trajectories/trajectory_level.jsonl`
- `trajectories/step_level.jsonl`
- `trajectories/accepted.jsonl`
- `trajectories/rejected.jsonl`
- `trajectories/dataset_summary.json`

内置质量门：
- `parse_error` 拒绝
- 候选集为空拒绝
- 预测长度必须等于候选长度
- 禁止重复预测
- 预测必须来自候选集
- RDKit 不可用时样本拒绝（`rdkit_unavailable`）

奖励定义（当前）：
- `reward_outcome = 2 * top3_hit_num + top10_hit_num`
- 仅终点步注入 reward（step-level 最后一条记录）

新增可审计分层：
- `artifact_audit.tool_generated.*`
- `artifact_audit.llm_generated.*`

用于区分：
- 工具调用/工具结果计数（特别是 docking）
- assistant 文本块与亲和力文本提及计数

## 4.5 `evaluate/eval_runner.py`

增强评估方式：
- RDKit 可用时进行 canonical SMILES 对齐再计算 top3/top10
- RDKit 不可用时降级为原始字符串评估

新增评估审计：
- `quality_issue_hist`
  - `length_mismatch`
  - `outside_candidate_set`
  - `duplicate_predictions`
  - `empty_candidate_set`
- `invalid_smiles_hist`
- 每条预测写回 `eval_audit`

---

## 5. 运行方式

## 5.1 最小可运行路径（Minimal Path）

```bash
cd /home/sunxiangyu/sunxiangyu/vs_pipeline
bash claude_agent/test_flow_claude.sh qwen-397b claude 1 1 1
```

说明：
- 跑 1 条样本，1 rollout，串行。
- 输出目录由日志中的 `RESULTS_DIR=` 指定。

## 5.2 全量复现路径（Full Path）

```bash
cd /home/sunxiangyu/sunxiangyu/vs_pipeline
bash claude_agent/test_flow_claude.sh qwen-397b claude 0 8 4
```

说明：
- `LIMIT=0` 代表数据集切片后不再限制。
- 每条样本 8 rollout，单样本内最多并发 4 rollout。

## 5.3 仅跑推理（不跑评估）

```bash
cd /home/sunxiangyu/sunxiangyu/vs_pipeline
bash claude_agent/launch_claude.sh \
  --run-dataset \
  --dataset-csv molbench-vs/MolBench-vs-25.csv \
  --skills-root skills \
  --results-root results \
  --provider qwen-397b \
  --claude-bin claude \
  --start-row 1 \
  --end-row 25 \
  --num-rollouts 4 \
  --parallel-rollouts 2
```

---

## 6. 产物结构（新）

```text
results/molbench_vs_{provider}_run_{ts}/
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
    rollout0002/...
  preds/molbench_vs/
    molbench_vs.json                  # rollout 1（兼容旧评估入口）
    rollouts/
      rollout_0001.json
      rollout_0002.json
  trajectories/
    trajectory_level.jsonl
    step_level.jsonl
    accepted.jsonl
    rejected.jsonl
    dataset_summary.json
  bench_scores.json                   # test_flow 完成后生成
```

---

## 7. 关键数据口径

- `trajectory_level.jsonl`：任务/轨迹级记录，含 `status`、拒绝原因、top3/top10、reward。
- `step_level.jsonl`：逐 step 记录，含 `action_type`、`tool_name`、`observation`、`done`、`reward`。
- `accepted/rejected.jsonl`：基于质量门的拆分。
- `completion_report.json`：结构完整性报告（是否缺文件、summary 对齐情况、pred 文件完整性）。

---

## 8. 当前仍保留的边界

本轮明确未改：
- Token 预算与成本治理（例如工具调用预算、早停策略）
- 历史 run 批量回填导出（仅对新 run 自动导出）
- 过程奖励（dense/process reward）自动标注
- 在线 RL 所需可重放环境包装

---

## 9. 推荐下一步

1. 新增 `backfill_trajectories.py`，对旧 `results/*` 一键补导出。
2. 在 exporter 增加 process reward 代理（重复 docking 惩罚、工具失败惩罚、有效口袋发现奖励）。
3. 构建同任务多 rollout 偏好对（`good > bad`）并导出 DPO 数据。
4. 增加“每个 rollout 独立评估”并产出 `bench_scores_rollouts.json`。

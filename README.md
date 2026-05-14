<a id="top"></a>

# Mol-Pipeline

<!-- ![Paper](https://img.shields.io/badge/Paper-MolBench--MS%20aligned-informational)
![License](https://img.shields.io/badge/License-Unspecified-lightgrey) -->
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
<!-- ![Runtime](https://img.shields.io/badge/Runtime-Conda%20%2B%20tmux-6f42c1) -->

Unified **dataset generation + agent execution + evaluation** workflow for MolBench-style tasks (`AC`, `VS`, `PF`).

If this helps your experiments, a star is always appreciated.

## 🚀 Overview
This repository combines two previously separate codebases into one practical research pipeline:

- **`get-molbench/`** generates benchmark CSVs for three complementary molecular reasoning tasks.
- **`ms_pipeline/`** runs agent rollouts, exports trajectories, and evaluates predictions.
- **`scripts/run_molbench_workflow.sh`** provides a one-command path from dataset generation to tmux-dispatched task runs.

Design-wise, the project focuses on four contribution-level goals reflected in code:

- **Single execution truth** for dataset runs (`run_claude.py` as the core runner).
- **Multi-task support** across `vs`, `ac`, `pf` with task-aware prompts/MCP routing.
- **Trajectory-first outputs** (`trajectory_level`, `step_level`, accepted/rejected splits).
- **Audit-ready evaluation** with quality checks and RDKit-aware canonical matching.

## 🧪 Benchmarks & Datasets
MolBench-style evaluation here targets distinct but complementary capabilities in molecular agents: **pairwise affinity reasoning (AC)**, **ranking under realistic candidate sets (VS)**, and **rule-grounded filtering/similarity reasoning (PF)**.

- **AC (Binding Affinity Comparison)**
  - Predict which molecule is stronger/weaker for a target.
  - Generator: `get-molbench/pipelines/generate_molbench_ac.py`
- **VS (Virtual Screening)**
  - Rank candidates for target-specific activity.
  - Generator: `get-molbench/pipelines/generate_molbench_vs.py`
- **PF (Property Filtering / Similarity)**
  - Filter molecules by constraints or perform similarity-style tasks.
  - Generator: `get-molbench/pipelines/generate_molbench_pf.py` (`v0`, `v1`, `sim`)

Reference samples are available in `get-molbench/examples/` and default run datasets in `ms_pipeline/molbench/`.

## 🧩 Skills & Modules
- **Dataset construction (`get-molbench/`)**
  - Canonical generators and wrappers for AC/VS/PF.
  - Includes merge utilities like `scripts/merge_molbench_pf.py`.
- **Agent orchestration (`ms_pipeline/claude_agent/`)**
  - `launch_claude.sh`: environment and runner entry.
  - `test_flow_claude.sh`: inference + evaluation orchestration.
  - `run_claude.py`: rollout execution, logging, completeness checks.
  - `trajectory_exporter.py`: normalized trajectory datasets.
- **Evaluation (`ms_pipeline/evaluate/`)**
  - `run_eval_bench.py`: evaluation entrypoint.
  - `eval_runner.py`: task-specific metrics and audit fields.
- **End-to-end automation (`scripts/`)**
  - `run_molbench_workflow.sh`: generate datasets and dispatch three tmux tasks.

## ⚙️ Setup
```bash
# 1) Clone
git clone <YOUR_REPO_URL>
cd mol-pipeline

# 2) Create environment
conda env create -f get-molbench/environment.yml
conda activate get-molbench

# 3) (Optional) keep pip dependencies aligned
pip install -r get-molbench/requirements.txt
```

## 🔐 Quickstart Config
Create runtime config from template (do not commit secrets):

```bash
cp .env.template .env
# Fill required fields in .env:
# - MOLCLAW_VS_MCP_URL
# - MOLCLAW_VS_MCP_AUTH
# - MOLCLAW_SCP_MCP_URL
# - MOLCLAW_SCP_MCP_AUTH
```

## ▶️ Run
### 1) One-command workflow (recommended)
```bash
# Generates AC/VS/PF datasets under get-molbench/outputs/auto/
# Then dispatches 3 tmux targets:
#   vs_pipe-2:0, ac_pipe-4:0, pf_pipe-5:0
# Prerequisite: these tmux targets already exist.
bash scripts/run_molbench_workflow.sh --seed 42 --n-cases 30
```

### 2) Generate datasets manually
```bash
# AC
python get-molbench/pipelines/generate_molbench_ac.py \
  --n-cases 30 --seed 42 \
  --out-dir outputs/auto/ac \
  --out-name molbench-ac-30-42.csv

# VS
python get-molbench/pipelines/generate_molbench_vs.py \
  --n-cases 30 --seed 42 \
  --out-dir outputs/auto/vs \
  --out-name molbench-vs-30-42.csv \
  --no-remote-target-name

# PF (split + merge, sim skipped by default in the integrated workflow)
python get-molbench/pipelines/generate_molbench_pf.py \
  --variant v0 --n-cases 15 --seed 42 \
  --out-dir outputs/auto/pf \
  --out-name molbench-pf-v0-15-42.csv

python get-molbench/pipelines/generate_molbench_pf.py \
  --variant v1 --n-cases 15 --seed 43 \
  --out-dir outputs/auto/pf \
  --out-name molbench-pf-v1-15-43.csv

python get-molbench/scripts/merge_molbench_pf.py \
  --v0-csv get-molbench/outputs/auto/pf/molbench-pf-v0-15-42.csv \
  --v1-csv get-molbench/outputs/auto/pf/molbench-pf-v1-15-43.csv \
  --out get-molbench/outputs/auto/pf/molbench-pf-30-42.csv
```

### 3) Run a single task pipeline
```bash
# Example: VS
bash ms_pipeline/claude_agent/test_flow_claude.sh \
  qwen-397b claude 0 1 1 vs \
  ../get-molbench/outputs/auto/vs/molbench-vs-30-42.csv 1
```

### 4) Evaluation entrypoint
```bash
python ms_pipeline/evaluate/run_eval_bench.py <RESULTS_DIR> --task vs
# --task can be: vs | ac | pf (or omit to auto-infer)
```

## 📦 Output Snapshot
Typical run outputs are written under:

- `get-molbench/outputs/...` for generated datasets
- `ms_pipeline/results/molbench_<task>_<provider>_run_<timestamp>/...` for rollouts and metrics

Inside each run directory, you can expect:

- `run_config.json`, `run_summary.jsonl`, `completion_report.json`
- `preds/molbench_<task>/...`
- `trajectories/trajectory_level.jsonl`, `step_level.jsonl`, `accepted.jsonl`, `rejected.jsonl`
- `bench_scores.json`

<!-- ## 📄 License
This repository currently does **not** include a `LICENSE` file in the root. Add one before public distribution if you need explicit open-source licensing terms.

## 📚 Citation
If you use this repository in research, please cite it as software:

```bibtex
@software{mol_pipeline,
  title   = {Mol-Pipeline: Unified MolBench Dataset, Agent, and Evaluation Workflow},
  author  = {Mol-Pipeline Contributors},
  year    = {2026},
  url     = {<YOUR_REPO_URL>}
}
``` -->

<p align="center">
  Xiangyu Sun • <a href="https://github.com/mu9enn">Repository</a> • <a href="#top">Back to top ↑</a>
</p>

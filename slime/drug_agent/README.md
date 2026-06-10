# Slime-Native DrugAgent

`drug_agent` is a thin plugin layer on the existing Slime training stack. It
does not replace Slime trainers or move training logic into a separate
framework.

## Mainline Boundary

- Canonical ReAct SFT data is produced by `mol-pipeline/pipeline/postprocess`.
- Formal SFT, ToolRL, GAD, and OPD training consumes fixed offline states.
- Formal training never executes generated actions or calls MCP.
- Real MCP execution is retained only for explicitly opted-in online
  evaluation/debug.

See:

- [`OFFLINE_TRAINING_POLICY.md`](OFFLINE_TRAINING_POLICY.md)
- [`../../docs/architecture.md`](../../docs/architecture.md)
- [`../../docs/entrypoints.md`](../../docs/entrypoints.md)
- [`../../docs/contracts/catalog.json`](../../docs/contracts/catalog.json)

## Active Data And Validation

```bash
python drug_agent/data/materialize_sft_jsonl.py --help
python drug_agent/data/validate_sft_messages.py --help
python drug_agent/toolrl/convert_react_to_toolrl_steps.py --help
python drug_agent/toolrl/validate_toolrl_offline_data.py --help
python -m drug_agent.gad.data --help
```

`drug_agent/data/convert_pipelined_to_slime_grpo.py` remains compatibility
support for retained online evaluation/debug data. It is not the canonical
ReAct SFT producer.

## Active Training

Formal training must source the worker-local Slime environment and run from
`$SLIME`. Worker model, checkpoint, Megatron, and environment paths are
intentionally unchanged.

```bash
bash drug_agent/scripts/run_qwen3_5_0_8b_drug_sft_smoke.sh
bash drug_agent/scripts/run_qwen3_5_4b_drug_sft_smoke.sh
bash drug_agent/scripts/run_qwen3_5_4b_drug_sft_full.sh

bash drug_agent/toolrl/scripts/run_toolrl_grpo_smoke.sh
bash drug_agent/gad/scripts/run_stage3_gad_grpo_smoke.sh
bash drug_agent/opd/scripts/run_qwen3_5_4b_opd_smoke.sh
```

The existing launchers retain their current model paths, worker paths,
parallelism checks, allocator guards, and training arguments.

## Online MCP Evaluation And Debug

These commands may call real MCP tools. They are not training entrypoints and
require explicit opt-in:

```bash
export DRUG_AGENT_ALLOW_TOOL_ENV=1

python drug_agent/tools_debug/debug_mcp_tools.py --list-tools
python drug_agent/tools_debug/debug_replay_trajectory.py --help
python drug_agent/tools_debug/debug_one_task.py --help
```

`debug_one_task.py` may also start or use SGLang/model resources depending on
its arguments. Consult the root [entrypoint catalog](../../docs/entrypoints.md)
before running debug commands.

## Non-Invasive Checks

From the monorepo root:

```bash
make check
```

From `slime/`:

```bash
python -m unittest discover -s drug_agent/tests -p 'test_*.py' -v
python drug_agent/toolrl/tests/run_toolrl_tests.py
python -m unittest discover -s drug_agent/gad/tests -p 'test_*.py' -v
python drug_agent/tools_debug/audit_offline_training.py
```

# Entrypoint Catalog

Run commands from the owning project directory unless stated otherwise.

Side-effect labels:

- `read-only`: validation, inspection, or tests; may create Python caches.
- `local-write`: writes datasets, reports, runs, checkpoints, or logs.
- `remote`: calls Claude, MCP, or another remote service.
- `ray-gpu`: starts Ray, SGLang, model loading, or GPU training.

## Active Mainline

| Entrypoint | Status | Side effects | Purpose |
| --- | --- | --- | --- |
| `molclaw-kg: PYTHONPATH=src python -m molclaw_kg ...` | active | command-dependent: local-write; snapshot/adjudication/sampling may be remote | Native KG CLI |
| `molclaw-kg/scripts/run_full_pipeline.sh` | active | local-write, remote | KG Stage1 and Stage2 orchestration |
| `molclaw-kg/scripts/run_sample_questions.sh` | active | local-write, remote | Grounded Stage3 question sampling |
| `molclaw-kg/scripts/download_science_kb_sources.sh` | active setup | local-write, remote download | Explicitly download Science-KB sources |
| `molclaw-kg/scripts/build_science_kb.py` | active setup | local-write | Build local Science-KB |
| `mol-pipeline/pipeline/claude_agent/run_execute.sh` | active | local-write, remote | Execute VS/AC/PF/KG/E2E tasks and write raw sessions |
| `mol-pipeline/pipeline/evaluate/run_evaluate.sh` | active | local-write | Evaluate VS/AC/PF run artifacts |
| `mol-pipeline/scripts/run_postprocess.sh` | active | local-write | Raw session to trajectory, candidate scan, and ReAct outputs |
| `mol-pipeline/scripts/run_llm_clean.sh` | active | local-write, remote unless `--skip-llm` | Semantic repair, final hard-clean, and validation |
| `mol-pipeline/scripts/run_molbench_workflow.sh` | active | local-write | Build MolBench task datasets |
| `mol-pipeline/pipeline/e2e/run_e2e_pipeline.sh` | active | local-write, remote | Build and execute E2E tasks |
| `mol-pipeline/pipeline/kg/run_kg_pipeline.sh` | active | local-write, remote | Execute KG-sampled tasks |
| `slime/train.py`, `slime/train_async.py` | framework core | local-write, ray-gpu | Slime training entrypoints used by wrappers |
| `slime/drug_agent/scripts/check_env.sh` | active setup | read-only | Check worker environment |
| `slime/drug_agent/scripts/prepare_qwen3_5_4B_torch_dist.sh` | active setup | local-write, ray-gpu/model loading | Convert checkpoint for training |
| `slime/drug_agent/scripts/run_qwen3_5_0_8b_drug_sft_smoke.sh` | active training | local-write, ray-gpu | Generic parameterized ReAct SFT launcher |
| `slime/drug_agent/scripts/run_qwen3_5_4b_drug_sft_smoke.sh` | active training | local-write, ray-gpu | Conservative Qwen3.5-4B SFT smoke wrapper |
| `slime/drug_agent/scripts/run_qwen3_5_4b_drug_sft_full.sh` | active training | local-write, ray-gpu | Qwen3.5-4B SFT full wrapper |
| `slime/drug_agent/toolrl/scripts/run_toolrl_grpo.sh` | active training | local-write, ray-gpu; no MCP | Offline ToolRL launcher |
| `slime/drug_agent/toolrl/scripts/run_toolrl_grpo_{smoke,learn}.sh` | active training wrappers | local-write, ray-gpu; no MCP | Offline ToolRL smoke/learn wrappers |
| `slime/drug_agent/toolrl/scripts/run_qwen3_5_4b_toolrl_{smoke,full}.sh` | active training wrappers | local-write, ray-gpu; no MCP | Qwen3.5-4B ToolRL wrappers |
| `slime/drug_agent/gad/scripts/prepare_gad_step_data.sh` | active data | local-write | Prepare GAD fixed decision states |
| `slime/drug_agent/gad/scripts/generate_stage2_negatives.sh` | active training | local-write, ray-gpu; no MCP | Generate current-student negatives |
| `slime/drug_agent/gad/scripts/run_stage2_discriminator_warmup.sh` | active training | local-write, may load model/GPU | GAD discriminator warmup |
| `slime/drug_agent/gad/scripts/serve_discriminator.sh` | active training service | local-write, local HTTP, may load model/GPU | Serve GAD discriminator |
| `slime/drug_agent/gad/scripts/run_stage3_gad_grpo.sh` | active training | local-write, ray-gpu; local discriminator HTTP; no MCP | GAD Stage3 |
| `slime/drug_agent/gad/scripts/run_stage3_gad_grpo_smoke.sh` | active training wrapper | local-write, ray-gpu; local discriminator HTTP; no MCP | GAD Stage3 smoke |
| `slime/drug_agent/opd/scripts/run_qwen3_5_4b_opd.sh` | active training | local-write, ray-gpu; no MCP | Offline OPD |
| `slime/drug_agent/opd/scripts/run_qwen3_5_4b_opd_{smoke,full}.sh` | active training wrappers | local-write, ray-gpu; no MCP | Offline OPD wrappers |

## Active Data And Validation

| Entrypoint | Status | Side effects | Purpose |
| --- | --- | --- | --- |
| `slime/drug_agent/data/materialize_sft_jsonl.py` | active | local-write | Materialize pretty ReAct JSON files into JSONL |
| `slime/drug_agent/data/validate_sft_messages.py` | active | read-only, optional report write | Validate SFT structure/protocol and tokenizer compatibility |
| `slime/drug_agent/data/inspect_pipelined_data.py` | compatibility inspection | local-write report | Inspect historical pipelined-data joins |
| `slime/drug_agent/data/sample_debug.py` | debug | read-only | Print JSONL sample previews |
| `slime/drug_agent/toolrl/convert_react_to_toolrl_steps.py` | active | local-write | Convert ReAct SFT into ToolRL decision steps |
| `slime/drug_agent/toolrl/validate_toolrl_offline_data.py` | active | local-write reports | Validate offline ToolRL data |
| `slime: python -m drug_agent.gad.data` | active | local-write | Convert ReAct SFT into GAD decision states |
| `slime/drug_agent/data/convert_pipelined_to_slime_grpo.py` | compatibility support | local-write | Build historical action-json data used by retained online debug |

## Online Evaluation And Debug

These are intentionally retained because trained models still require real MCP
inference testing. They are not formal training entrypoints.

| Entrypoint | Status | Side effects | Purpose |
| --- | --- | --- | --- |
| `slime/drug_agent/tools_debug/debug_one_task.py` | online debug | local-write, remote MCP, may load/start SGLang/GPU | Run one model task with real tools |
| `slime/drug_agent/tools_debug/debug_replay_trajectory.py` | online debug | local-write, remote MCP | Replay historical tool calls |
| `slime/drug_agent/tools_debug/debug_mcp_tools.py` | online debug | remote MCP | MCP connectivity/tool smoke test |
| `slime/drug_agent/tools_debug/debug_sglang_launch.py` | debug | may start SGLang/GPU | Diagnose SGLang launch compatibility |
| `slime/drug_agent/tools_debug/debug_sft_mask_qwen.py` | debug | may load tokenizer/model assets | Inspect SFT masking |
| `slime/drug_agent/tools_debug/debug_reward.py` | debug | read-only | Inspect historical online reward behavior without executing tools |
| `slime/drug_agent/tools_debug/debug_toolrl_offline_no_tool_call.py` | active audit | read-only; explicitly no MCP | Verify ToolRL reward stays offline |
| `slime/drug_agent/tools_debug/audit_offline_training.py` | active audit | read-only | Static offline-training boundary audit |

## Non-Invasive Repository Checks

`make check` and its component targets must never start training, Ray, GPUs,
Claude, MCP, model loading, or remote requests.

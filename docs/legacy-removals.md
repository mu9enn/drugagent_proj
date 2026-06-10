# Legacy Removal Record

Files listed here are removed only after `git grep` confirms they are not
required by an active mainline or retained online-debug entrypoint.

Restore any removed file with:

```bash
git restore --source=8e2e9ac1698aca07efcd16f71b37e4aec5b509ae -- <path>
```

## Removed Code And Protocols

| Paths | Reason |
| --- | --- |
| `slime/drug_agent/data/convert_pipelined_to_slime_sft.py` | Explicitly deprecated action-json SFT converter; canonical SFT is produced by mol-pipeline ReAct postprocess |
| `slime/drug_agent/tools_debug/debug_training_compliance.py` | Explicitly deprecated helper; active authority is offline audit plus focused validators |
| `slime/drug_agent/scripts/run_qwen3_5_0_8b_drug_{ppo_smoke,grpo_smoke,grpo_learn}.sh` | Historical online-training launchers that are deliberately rejected before launch |
| `slime/drug_agent/scripts/reject_legacy_online_training.sh` | Exists only to reject the three removed launchers |
| `mol-pipeline/pipeline/postprocess/{export_verl_training_bundle.py,validate_verl_training_bundle.py}` | Optional legacy VERL handoff, outside the current Slime training mainline |
| `mol-pipeline/docs/mol_pipeline_to_verl_bundle_v0.1.md` | Documentation for the removed optional VERL handoff |
| `mol-pipeline/pipeline/kg/schemas/kg_task_spec_v0.1.md` | Superseded contract document; runtime historical-input compatibility remains in code |

## Removed Historical Documents

The following categories are superseded by current READMEs and the root
architecture, entrypoint, contract, known-issue, and removal records:

- dated handoff documents under project `docs/`;
- `PROJECT_RESEARCH_REPORT.md` reports;
- `TRAJECTORY_FLOW_4_5_DEEP_REPORT.md`;
- old `ToFix.md`;
- historical Slime DrugAgent deep-dive/runbook documents;
- old schema handoff notes.

Useful still-current facts are migrated before removal. These files remain
recoverable from Git history.

Exact historical-document removal paths:

- `mol-pipeline/docs/mol-pipeline_deep_handoff_20260603.md`
- `mol-pipeline/docs/mol-pipeline_handoff_20260526_115527.md`
- `mol-pipeline/docs/molclaw-kg_deep_handoff_20260603.md`
- `mol-pipeline/docs/postprocess_hard_clean_handoff_20260608.md`
- `mol-pipeline/get-molbench/PROJECT_RESEARCH_REPORT.md`
- `mol-pipeline/pipeline/PROJECT_RESEARCH_REPORT.md`
- `mol-pipeline/pipeline/TRAJECTORY_FLOW_4_5_DEEP_REPORT.md`
- `mol-pipeline/pipeline/ToFix.md`
- `mol-pipeline/scripts/slime_mcp_vs_sft_schema_handoff.md`
- `molclaw-kg/docs/molclaw-kg_handoff_20260526_115419.md`
- `slime/docs/DRUG_AGENT_PROJECT_DEEP_DIVE_zh.md`
- `slime/docs/SLIME_DRUG_AGENT_RUNBOOK_zh.md`
- `slime/drug_agent/RUN_COMMANDS.md`

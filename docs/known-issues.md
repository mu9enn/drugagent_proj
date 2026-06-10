# Known Issues

This document keeps current, actionable issues. Historical investigation
reports are available through Git history.

## Environment And Execution

- Slime training and online model debug depend on worker-local model,
  checkpoint, Megatron, and environment-script paths. They are intentionally
  not normalized by repository cleanup.
- Formal training requires a GPU-worker environment and cannot be fully
  validated on this development machine.
- The local development environment does not provide FastAPI, so the GAD
  service-route test is skipped locally.
- Molclaw-KG uses a `src` package layout. Without installation, invoke it with
  `PYTHONPATH=src python -m molclaw_kg`.

## Operational Risks

- Concurrent task execution may encounter provider-side errors or concurrency
  limits. Start with conservative parallelism and increase only after verifying
  the target provider.
- Long SFT samples can cause GPU OOM even with dynamic packing because one
  sample is not truncated by the packing limit.
- Qwen3.5-4B colocated SGLang/TorchMemorySaver runs must not inherit
  incompatible expandable-segment allocator settings.

## Contract Gaps

- Raw `complete_session.jsonl`, trajectory exports, RL prompts, and GAD steps
  do not currently have independent machine-readable schemas.
- These contracts are therefore marked `doc-only` in the contract catalog.
  Do not treat documentation as stronger validation than the implementation.

## Historical Import Pollution

- The active DrugAgent extension under `slime/drug_agent/` is checked against
  the erroneous `git_cl.drugagent_proj` import prefix.
- The wider imported Slime tree still contains that prefix in framework,
  example, plugin, and test files. This conflicts with broad historical wording
  that implied repository-wide removal. It is not changed by documentation
  work; assess and repair it as a separately scoped code task.

For symptom-oriented handling, see [Troubleshooting](runbooks/troubleshooting.md).

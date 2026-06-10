# Mainline Cleanup Report

## Before

- Baseline commit:
  `8e2e9ac1698aca07efcd16f71b37e4aec5b509ae`.
- DrugAgent tests required the development-machine compatibility path
  `PYTHONPATH=/Users/sunx/code_proj` because imports used
  `git_cl.drugagent_proj`.
- Entrypoints, side effects, contracts, active paths, and retired paths were
  spread across current READMEs and dated reports.
- Deprecated online-training launchers and an optional VERL handoff remained
  in the active source tree.

## After

- DrugAgent imports use the established `drug_agent.*` and `slime.*` package
  semantics when run from `slime/`.
- Root facts now live in architecture, entrypoint, contract, known-issue, and
  legacy-removal documents.
- Contracts without real schemas or validators are explicitly `doc-only`.
- Deprecated launchers, converter/helper code, VERL handoff, superseded KG
  v0.1 documentation, and dated reports were removed and recorded.
- Real MCP online evaluation/debug remains available, including its parser,
  executor, replay, one-task, and connectivity tools.
- Root `make check` provides only non-invasive static and unit checks.

## Behavior Preserved

No training behavior, data-cleaning rule, reward logic, sampling logic, quality
gate, MCP executor behavior, model path, checkpoint path, or worker environment
path was intentionally changed.

The only changes to retained production/debug Python modules are:

- removal of the erroneous `git_cl.drugagent_proj` import prefix;
- offline audit now verifies retired online-training launchers are absent
  instead of verifying they abort before launch.

## Verification

`make check` results:

- non-invasive repository checks: passed;
- golden contract-flow tests: 3 passed;
- Mol-pipeline postprocess tests: 10 passed;
- Molclaw-KG tests: 14 passed;
- DrugAgent offline-boundary tests: 5 passed;
- DrugAgent ToolRL runner: passed;
- DrugAgent GAD tests: 9 passed, 1 skipped because FastAPI is unavailable
  locally.

Not run automatically:

- GPU/Ray/SGLang/model-loading training;
- Claude/provider execution;
- real MCP execution;
- worker-local checkpoint and environment validation.

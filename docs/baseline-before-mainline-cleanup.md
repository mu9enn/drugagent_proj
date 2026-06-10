# Baseline Before Mainline Cleanup

Recorded on 2026-06-11 before the mainline-convergence cleanup.

## Repository State

- Commit: `8e2e9ac1698aca07efcd16f71b37e4aec5b509ae`
- Branch: `main`
- Tracking: `origin/main`
- Existing user work: untracked `core_flow.html`

## Baseline Checks

DrugAgent tests require the temporary machine-level compatibility path
`PYTHONPATH=/Users/sunx/code_proj` because source imports currently contain the
incorrect `git_cl.drugagent_proj` prefix.

| Check | Baseline result |
| --- | --- |
| DrugAgent offline-boundary tests | 5 passed |
| DrugAgent ToolRL runner | passed |
| DrugAgent GAD tests | 9 passed, 1 skipped because FastAPI is unavailable locally |
| Mol-pipeline postprocess tests | 10 passed |
| Molclaw-KG tests | 14 passed |
| Molclaw-KG CLI help with `PYTHONPATH=src` | passed |
| Shell syntax (`bash -n`) | passed |
| Python `compileall` | passed |

This cleanup must preserve those behavioral results while removing the
temporary machine-level import requirement.

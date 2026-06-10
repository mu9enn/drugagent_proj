# DrugAgent Mainline Architecture

This document is the current architectural fact source. The repository is a
monorepo, but each producer continues to own its implementation and contracts.

## Mainline

```text
molclaw-kg
  build tool knowledge graph and sample grounded questions
        |
        v
mol-pipeline
  execute tasks -> raw complete_session.jsonl
  -> trajectory export and quality gate
  -> accepted MolClaw session scan
  -> cleaned ReAct SFT and RL-prompt artifacts
        |
        v
slime/drug_agent
  validate/materialize fixed offline data
  -> ReAct SFT / ToolRL / GAD / OPD training
```

## Ownership Boundaries

### `molclaw-kg`

- Owns tool-card, graph-edge, provenance, sampling, and KG-run artifacts.
- Owns `trajectory_v2_graph` generation and Stage3 sampling validation.
- Has a package CLI under `molclaw_kg.cli`.

### `mol-pipeline`

- Owns task execution and raw `complete_session.jsonl` artifacts.
- Owns trajectory reconstruction, accepted/rejected quality gates, and
  deterministic ReAct postprocessing.
- Owns the canonical ReAct SFT producer:
  `drug_agent_sft_react_json_v1`.

### `slime/drug_agent`

- Is a thin plugin layer on the existing Slime training stack.
- Owns offline training-data validation and ToolRL/GAD conversion.
- Formal training consumes fixed states and never executes generated actions.
- Explicit online evaluation/debug utilities may call real MCP tools.

## Training And Online Evaluation Boundary

Formal SFT, ToolRL, GAD, and OPD training is offline. Model-generated actions
are scored or used for loss calculation but are not executed against MCP.

Real MCP execution is retained for explicitly named online evaluation/debug
utilities. These utilities require explicit tool-environment opt-in and are not
formal training entrypoints.

## Change Constraints

Engineering cleanup must not silently change:

- training arguments or behavior;
- data-cleaning and hard-clean rules;
- reward or sampling logic;
- accepted/rejected quality gates;
- MCP executor behavior;
- model, checkpoint, worker environment, or offline resource paths.

Cross-project sharing should begin with documentation and validation contracts,
not by moving working logic into a new shared package.

For stage-by-stage inputs, outputs, consumers, and failure boundaries, continue
with [Mainline Flow Deep Dive](mainline-flow-deep-dive.md).

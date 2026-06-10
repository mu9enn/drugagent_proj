# DrugAgent

DrugAgent is a monorepo containing the training, data-pipeline, and knowledge-graph
projects used for molecular-agent development.

## Projects

- [`slime/`](slime/README.md): Slime-based training and rollout code, including
  DrugAgent extensions.
- [`mol-pipeline/`](mol-pipeline/README.md): Molecular task execution,
  evaluation, and post-processing pipelines.
- [`molclaw-kg/`](molclaw-kg/README.md): MolClaw tool knowledge-graph
  construction and sampling.

Each project keeps its own README and entry points. Run project-specific
commands from that project's directory unless its documentation says otherwise.

## Engineering Guide

- [Mainline architecture](docs/architecture.md)
- [Entrypoints and side effects](docs/entrypoints.md)
- [Contract catalog](docs/contracts/README.md)
- [Known issues](docs/known-issues.md)
- [Legacy removal record](docs/legacy-removals.md)

Non-invasive repository checks:

```bash
make check
```

These checks do not start training, Ray, GPUs, Claude, MCP, model loading, or
remote requests.

## Repository History

The three projects were previously maintained as independent Git repositories.
Their complete `main` branch histories were imported into this monorepo without
squashing.

`slime/` is derived from and was originally maintained as a fork of
[THUDM/slime](https://github.com/THUDM/slime). GitHub cannot display the
original "forked from" relationship on this multi-project monorepo, but the
upstream history and attribution are retained.

## Syncing Slime Upstream

The `slime-upstream` remote is local Git configuration and must be added once
after cloning:

```bash
git remote add slime-upstream git@github.com:THUDM/slime.git
git fetch slime-upstream
```

Pull upstream Slime changes into the `slime/` subtree with:

```bash
git subtree pull --prefix=slime slime-upstream main
```

Review and test upstream merges carefully because `slime/` contains
DrugAgent-specific changes.

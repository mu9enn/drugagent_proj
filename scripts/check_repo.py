#!/usr/bin/env python3
"""Non-invasive repository checks for mainline engineering contracts."""
from __future__ import annotations

import compileall
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_IMPORT = "git_cl.drugagent_proj"
PYTHON_ROOTS = [
    ROOT / "slime/drug_agent",
    ROOT / "mol-pipeline/pipeline",
    ROOT / "molclaw-kg/src/molclaw_kg",
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def check_forbidden_imports() -> None:
    hits: list[str] = []
    for path in (ROOT / "slime/drug_agent").rglob("*.py"):
        if FORBIDDEN_IMPORT in path.read_text(encoding="utf-8"):
            hits.append(str(path.relative_to(ROOT)))
    if hits:
        fail(f"forbidden machine-path import prefix in: {hits}")


def check_contract_catalog() -> None:
    catalog_path = ROOT / "docs/contracts/catalog.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    contracts = payload.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        fail("contract catalog must contain contracts")

    valid_levels = {"model", "validator", "doc-only"}
    for contract in contracts:
        contract_id = contract.get("id")
        level = contract.get("level")
        if level not in valid_levels:
            fail(f"{contract_id}: invalid contract level {level!r}")
        definition = contract.get("definition")
        if not isinstance(definition, str) or not (ROOT / definition).exists():
            fail(f"{contract_id}: missing definition path {definition!r}")
        validator = contract.get("validator")
        if validator is not None and not (ROOT / validator).exists():
            fail(f"{contract_id}: missing validator path {validator!r}")
        if level == "validator" and not validator:
            fail(f"{contract_id}: validator-level contract has no validator")


def check_entrypoint_paths() -> None:
    required = [
        "molclaw-kg/scripts/run_full_pipeline.sh",
        "molclaw-kg/scripts/run_sample_questions.sh",
        "mol-pipeline/pipeline/claude_agent/run_execute.sh",
        "mol-pipeline/scripts/run_postprocess.sh",
        "mol-pipeline/scripts/run_llm_clean.sh",
        "slime/drug_agent/scripts/run_qwen3_5_0_8b_drug_sft_smoke.sh",
        "slime/drug_agent/toolrl/scripts/run_toolrl_grpo.sh",
        "slime/drug_agent/gad/scripts/run_stage3_gad_grpo.sh",
        "slime/drug_agent/opd/scripts/run_qwen3_5_4b_opd.sh",
        "slime/drug_agent/tools_debug/debug_one_task.py",
        "slime/drug_agent/tools_debug/debug_replay_trajectory.py",
        "slime/drug_agent/tools_debug/debug_mcp_tools.py",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    if missing:
        fail(f"documented entrypoints are missing: {missing}")


def check_shell_syntax() -> None:
    scripts = sorted(
        path
        for path in ROOT.rglob("*.sh")
        if ".git" not in path.parts
    )
    for script in scripts:
        subprocess.run(["bash", "-n", str(script)], check=True)


def check_python_syntax() -> None:
    for root in PYTHON_ROOTS:
        if not compileall.compile_dir(root, quiet=1):
            fail(f"compileall failed: {root.relative_to(ROOT)}")


def main() -> int:
    checks = [
        check_forbidden_imports,
        check_contract_catalog,
        check_entrypoint_paths,
        check_shell_syntax,
        check_python_syntax,
    ]
    for check in checks:
        check()
        print(f"[ok] {check.__name__}")
    print("[ok] non-invasive repository checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise

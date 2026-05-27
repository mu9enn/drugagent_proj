#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def _load_questions_csv(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    if not path.is_file():
        return out
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = str(row.get("sample_id") or "").strip()
            if sid:
                out[sid] = {k: (v or "") for k, v in row.items()}
    return out


def _tool_like_mcp(name: str) -> bool:
    s = (name or "").strip()
    if not s:
        return False
    # Stage3 usually stores short tool ids; treat these as valid too.
    return s.startswith("mcp__") or ("__" not in s and " " not in s)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect molclaw-kg sampled outputs for schema and field quality.")
    parser.add_argument("--kg-run-dir", required=True, help="Path like .../molclaw-kg/runs/<run_id>")
    parser.add_argument("--report-out", default="", help="Optional JSON report output path")
    args = parser.parse_args()

    kg_run_dir = Path(args.kg_run_dir).expanduser().resolve()
    sample_dir = kg_run_dir / "sample_results"
    success_path = sample_dir / "sample_success.jsonl"
    questions_path = sample_dir / "questions.csv"

    rows = _load_jsonl(success_path)
    qmap = _load_questions_csv(questions_path)

    missing_question = 0
    missing_expected = 0
    missing_toolchain = 0
    invalid_tool_names = 0
    leak_suspected = 0
    status_hist: dict[str, int] = {}

    per_sample: list[dict[str, Any]] = []
    for i, rec in enumerate(rows, start=1):
        sid = str(rec.get("sample_id") or f"sample_{i:04d}")
        status = str(rec.get("status") or "unknown").strip().lower()
        status_hist[status] = status_hist.get(status, 0) + 1

        q1 = str(rec.get("public_question_text") or "").strip()
        qrow = qmap.get(sid, {})
        q2 = str(qrow.get("public_question_text") or "").strip()
        question = q1 or q2

        expected = rec.get("expected_trajectory")
        tools = rec.get("toolchain_nodes")
        edges = rec.get("toolchain_edges")

        has_question = bool(question)
        has_expected = isinstance(expected, (dict, list)) and bool(expected)
        has_tools = isinstance(tools, list) and len(tools) > 0
        has_edges = isinstance(edges, list) and len(edges) > 0

        if not has_question:
            missing_question += 1
        if not has_expected:
            missing_expected += 1
        if not (has_tools and has_edges):
            missing_toolchain += 1

        tool_valid = True
        if isinstance(tools, list):
            for t in tools:
                if not _tool_like_mcp(str(t)):
                    tool_valid = False
                    break
        else:
            tool_valid = False
        if not tool_valid:
            invalid_tool_names += 1

        leak_flag = False
        if question and isinstance(tools, list):
            ql = question.lower()
            for t in tools:
                tt = str(t).strip().lower()
                if tt and tt in ql:
                    leak_flag = True
                    break
        if leak_flag:
            leak_suspected += 1

        per_sample.append(
            {
                "sample_id": sid,
                "status": status,
                "has_question": has_question,
                "has_expected_trajectory": has_expected,
                "has_toolchain_nodes": has_tools,
                "has_toolchain_edges": has_edges,
                "tool_name_format_ok": tool_valid,
                "question_leak_suspected": leak_flag,
                "question_source": "public_question_text" if q1 else ("questions.csv" if q2 else "missing"),
            }
        )

    report = {
        "kg_run_dir": str(kg_run_dir),
        "sample_success_path": str(success_path),
        "questions_csv_path": str(questions_path),
        "sample_count": len(rows),
        "questions_csv_rows": len(qmap),
        "status_hist": status_hist,
        "quality": {
            "missing_question": missing_question,
            "missing_expected_trajectory": missing_expected,
            "missing_toolchain": missing_toolchain,
            "invalid_tool_name_format": invalid_tool_names,
            "question_leak_suspected": leak_suspected,
        },
        "samples": per_sample,
    }

    if args.report_out.strip():
        out_path = Path(args.report_out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

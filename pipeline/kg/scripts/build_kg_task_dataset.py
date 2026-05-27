#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
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


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _as_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _extract_question(rec: dict[str, Any], qcsv_row: dict[str, str]) -> tuple[str, str]:
    q1 = str(rec.get("public_question_text") or "").strip()
    if q1:
        return q1, "public_question_text"
    q2 = str(qcsv_row.get("public_question_text") or "").strip()
    if q2:
        return q2, "questions.csv.public_question_text"
    return "", "missing"


def _build_task_spec(
    *,
    rec: dict[str, Any],
    kg_project_root: Path,
    kg_run_id: str,
    sample_file: Path,
    sample_index: int,
    sample_id: str,
    question: str,
    schema_version: str,
    include_raw_sample: bool,
) -> dict[str, Any]:
    tools = rec.get("toolchain_nodes") if isinstance(rec.get("toolchain_nodes"), list) else []
    edges = rec.get("toolchain_edges") if isinstance(rec.get("toolchain_edges"), list) else []
    expected = rec.get("expected_trajectory")

    task_id = f"kg_{kg_run_id}_{sample_id}"
    payload = rec.get("question_payload") if isinstance(rec.get("question_payload"), dict) else {}
    difficulty = str(payload.get("difficulty") or "unknown")

    metadata: dict[str, Any] = {
        "schema_version": schema_version,
        "created_by": "molclaw-kg Stage3",
        "difficulty": difficulty,
        "question_payload": payload,
        "source_created_at_utc": rec.get("created_at_utc"),
    }
    if include_raw_sample:
        metadata["raw_kg_sample"] = rec

    return {
        "task_id": task_id,
        "task_type": "kg_sampled",
        "question": question,
        "source": {
            "type": "molclaw_kg",
            "kg_project_root": str(kg_project_root),
            "kg_run_id": kg_run_id,
            "sample_file": str(sample_file),
            "sample_index": sample_index,
            "sample_id": sample_id,
        },
        "toolchain": {
            "tools": tools,
            "edges": edges,
            "hops": _as_int(rec.get("walk_hops"), 0),
            "start_tool": rec.get("start_tool"),
            "end_tool": rec.get("end_tool"),
        },
        "expected_trajectory": expected,
        "execution": {
            "allowed_tools": "all_molclaw",
            "must_follow_expected_trajectory": False,
            "leak_toolchain_to_agent": False,
        },
        "evaluation": {
            "mode": "none",
            "notes": "KG-sampled exploratory task; evaluate trajectory executability and molclaw usage only.",
        },
        "metadata": metadata,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build KG sampled tasks for mol-pipeline execution.")
    parser.add_argument("--kg-run-dir", required=True, help="Path like .../molclaw-kg/runs/<run_id>")
    parser.add_argument("--output-dir", required=True, help="Output directory for kg_sampled_tasks.jsonl and artifacts")
    parser.add_argument("--max-samples", type=int, default=0, help="Max accepted samples to export; 0 means all")
    parser.add_argument("--schema-version", default="kg_task_spec_v0.1")
    parser.add_argument("--no-include-raw-sample", action="store_true", help="Do not embed raw KG record in metadata")
    args = parser.parse_args()

    kg_run_dir = Path(args.kg_run_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    sample_dir = kg_run_dir / "sample_results"
    success_path = sample_dir / "sample_success.jsonl"
    questions_path = sample_dir / "questions.csv"

    if not success_path.is_file():
        raise FileNotFoundError(f"sample_success.jsonl not found: {success_path}")

    rows = _load_jsonl(success_path)
    qmap = _load_questions_csv(questions_path)
    kg_run_id = kg_run_dir.name
    kg_project_root = kg_run_dir.parent.parent
    include_raw_sample = not args.no_include_raw_sample

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for i, rec in enumerate(rows, start=1):
        sample_id = str(rec.get("sample_id") or f"sample_{i:04d}").strip()
        sample_index = _as_int(rec.get("index"), i)
        status = str(rec.get("status") or "").strip().lower()

        qcsv_row = qmap.get(sample_id, {})
        question, q_source = _extract_question(rec, qcsv_row)

        tools = rec.get("toolchain_nodes")
        edges = rec.get("toolchain_edges")
        expected = rec.get("expected_trajectory")

        reasons: list[str] = []
        if status and status != "success":
            reasons.append(f"status_not_success:{status}")
        if not question:
            reasons.append("missing_question")
        if not isinstance(tools, list) or not tools:
            reasons.append("missing_toolchain_nodes")
        if not isinstance(edges, list) or not edges:
            reasons.append("missing_toolchain_edges")
        if not isinstance(expected, (dict, list)) or not expected:
            reasons.append("missing_expected_trajectory")

        if reasons:
            rejected.append(
                {
                    "sample_id": sample_id,
                    "sample_index": sample_index,
                    "question_source": q_source,
                    "reasons": reasons,
                }
            )
            continue

        task = _build_task_spec(
            rec=rec,
            kg_project_root=kg_project_root,
            kg_run_id=kg_run_id,
            sample_file=success_path,
            sample_index=sample_index,
            sample_id=sample_id,
            question=question,
            schema_version=args.schema_version,
            include_raw_sample=include_raw_sample,
        )
        accepted.append(task)

    accepted.sort(key=lambda x: int(x.get("source", {}).get("sample_index", 0)))
    if args.max_samples > 0:
        accepted = accepted[: args.max_samples]

    output_dir.mkdir(parents=True, exist_ok=True)
    tasks_jsonl = output_dir / "kg_sampled_tasks.jsonl"
    exec_csv = output_dir / "kg_tasks_exec.csv"
    manifest_path = output_dir / "manifest.json"
    report_path = output_dir / "schema_validation_report.md"

    _write_jsonl(tasks_jsonl, accepted)

    with exec_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["index", "question_id", "question", "answer", "raw_question_json"],
        )
        writer.writeheader()
        for i, task in enumerate(accepted, start=1):
            writer.writerow(
                {
                    "index": i,
                    "question_id": task.get("task_id", f"kg_task_{i:06d}"),
                    "question": task.get("question", ""),
                    "answer": "[]",
                    "raw_question_json": json.dumps(task, ensure_ascii=False),
                }
            )

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "kg_run_dir": str(kg_run_dir),
        "kg_run_id": kg_run_id,
        "input": {
            "sample_success": str(success_path),
            "questions_csv": str(questions_path),
        },
        "output": {
            "kg_sampled_tasks_jsonl": str(tasks_jsonl),
            "kg_tasks_exec_csv": str(exec_csv),
            "schema_validation_report": str(report_path),
        },
        "counts": {
            "raw_rows": len(rows),
            "accepted": len(accepted),
            "rejected": len(rejected),
            "questions_csv_rows": len(qmap),
            "max_samples": args.max_samples,
        },
        "rejected_samples": rejected,
        "task_ids": [str(t.get("task_id")) for t in accepted],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# KG Task Dataset Validation Report",
        "",
        f"- kg_run_id: `{kg_run_id}`",
        f"- raw rows: {len(rows)}",
        f"- accepted: {len(accepted)}",
        f"- rejected: {len(rejected)}",
        f"- questions.csv rows: {len(qmap)}",
        "",
        "## Rejected Samples",
        "",
    ]
    if rejected:
        for rec in rejected:
            lines.append(
                f"- `{rec['sample_id']}` (idx={rec['sample_index']}, question_source={rec['question_source']}): {', '.join(rec['reasons'])}"
            )
    else:
        lines.append("- None")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SUPPORTED_TASKS = ("vs", "ac", "pf", "kg", "e2e")
SFT_SCHEMA_VERSION = "mcp-sft-v2-all"
RL_SCHEMA_VERSION = "mcp-rl-prompt-v2-all"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


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


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def _extract_text_items(content: Any) -> list[str]:
    out: list[str] = []
    if isinstance(content, str):
        s = content.strip()
        if s:
            out.append(s)
        return out
    if not isinstance(content, list):
        return out
    for item in content:
        if not isinstance(item, dict):
            continue
        it = str(item.get("type") or "")
        if it == "text":
            txt = item.get("text")
            if isinstance(txt, str) and txt.strip():
                out.append(txt.strip())
        elif it == "thinking":
            txt = item.get("thinking")
            if isinstance(txt, str) and txt.strip():
                out.append(txt.strip())
    return out


def _extract_tool_use_items(content: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(content, list):
        return out
    for item in content:
        if not isinstance(item, dict):
            continue
        if str(item.get("type") or "") == "tool_use":
            out.append(item)
    return out


def _extract_tool_result_items(content: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(content, list):
        return out
    for item in content:
        if not isinstance(item, dict):
            continue
        if str(item.get("type") or "") == "tool_result":
            out.append(item)
    return out


def _to_obs_content(tool_name: str, raw_content: Any, mode: str) -> str:
    payload: Any
    if isinstance(raw_content, str):
        payload = raw_content
    else:
        payload = json.dumps(raw_content, ensure_ascii=False)

    if mode == "tool":
        return f"<tool_response tool_name=\"{tool_name}\">{payload}</tool_response>"
    return f"<observation tool_name=\"{tool_name}\">{payload}</observation>"


def _load_question_text_from_original(original_session_path: str) -> str:
    if not original_session_path:
        return ""
    p = Path(original_session_path)
    if not p.is_file():
        return ""
    sample_dir = p.parent
    q = _load_json(sample_dir / "question.json")
    if not q:
        q = _load_json(sample_dir.parent / "question.json")
    qtxt = str(q.get("question_text") or q.get("question") or "").strip()
    return qtxt


def _process_session(
    *,
    copied_path: Path,
    task: str,
    tool_role_mode: str,
    original_path: str,
    summary_row: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    events = _load_jsonl(copied_path)
    if not events:
        return None, {"copied_path": str(copied_path), "reason": "empty_or_invalid_jsonl"}

    system_prompt = "You are a scientific agent. Use tools when needed and provide a final answer."
    question_text = _load_question_text_from_original(original_path)

    first_user_text = ""
    for ev in events:
        if str(ev.get("type") or "") != "user":
            continue
        msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
        txts = _extract_text_items(msg.get("content"))
        if txts:
            first_user_text = "\n".join(txts).strip()
            break

    if not question_text:
        question_text = first_user_text or "Task execution session"

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt, "step_loss_mask": 0},
        {"role": "user", "content": question_text, "step_loss_mask": 0},
    ]

    tools_seen: set[str] = set()
    tool_name_by_id: dict[str, str] = {}
    assistant_action_count = 0
    tool_obs_count = 0

    for ev in events:
        et = str(ev.get("type") or "")
        if et == "assistant":
            msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
            content = msg.get("content")

            for tu in _extract_tool_use_items(content):
                tool_name = str(tu.get("name") or "").strip()
                if not tool_name:
                    continue
                call_id = str(tu.get("id") or "").strip()
                if call_id:
                    tool_name_by_id[call_id] = tool_name
                tools_seen.add(tool_name)
                call_obj = {
                    "type": "tool_call",
                    "tool_name": tool_name,
                    "arguments": tu.get("input") if isinstance(tu.get("input"), dict) else {},
                }
                messages.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(call_obj, ensure_ascii=False, separators=(",", ":")),
                        "step_loss_mask": 1,
                    }
                )
                assistant_action_count += 1

            for txt in _extract_text_items(content):
                messages.append({"role": "assistant", "content": txt, "step_loss_mask": 1})

        elif et == "user":
            msg = ev.get("message") if isinstance(ev.get("message"), dict) else {}
            for tr in _extract_tool_result_items(msg.get("content")):
                tool_use_id = str(tr.get("tool_use_id") or "").strip()
                tool_name = tool_name_by_id.get(tool_use_id, "unknown_tool")
                obs_content = _to_obs_content(tool_name, tr.get("content"), tool_role_mode)
                role = "tool" if tool_role_mode == "tool" else "user"
                obs_msg: dict[str, Any] = {
                    "role": role,
                    "content": obs_content,
                    "step_loss_mask": 0,
                }
                if role == "tool":
                    obs_msg["name"] = tool_name
                messages.append(obs_msg)
                tool_obs_count += 1

        elif et == "result":
            result_text = str(ev.get("result") or "").strip()
            if result_text:
                final_obj = {
                    "type": "final_answer",
                    "answer": {
                        "summary": "Final answer from trajectory",
                        "evidence": [],
                        "result": {
                            "task_type": task,
                            "raw_answer": result_text,
                        },
                    },
                }
                messages.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(final_obj, ensure_ascii=False, separators=(",", ":")),
                        "step_loss_mask": 1,
                    }
                )
                assistant_action_count += 1

    if len(messages) < 3:
        return None, {"copied_path": str(copied_path), "reason": "insufficient_messages"}

    stable_id = f"mcp_sft_{task}_{_sha(str(copied_path.resolve()))}"
    run_dir_name = copied_path.name.split("__", 1)[0]

    tools_sorted = sorted(tools_seen)
    tools_schema = [
        {
            "name": t,
            "description": "Tool observed in accepted trajectory",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
        for t in tools_sorted
    ]

    metadata = {
        "source_project": "mol-pipeline",
        "task_type": task,
        "source_run": run_dir_name,
        "trajectory_path": str(copied_path),
        "original_session_path": original_path,
        "accepted": True,
        "answer_hit_pass": summary_row.get("answer_hit_pass"),
        "molclaw_usage_count": summary_row.get("molclaw_usage_count"),
        "metrics": {
            "vs_top3_hit_num": summary_row.get("vs_top3_hit_num"),
            "vs_top10_hit_num": summary_row.get("vs_top10_hit_num"),
            "ac_is_correct": summary_row.get("ac_is_correct"),
            "pf_precision": summary_row.get("pf_precision"),
            "pf_recall": summary_row.get("pf_recall"),
            "pf_f1": summary_row.get("pf_f1"),
            "pf_is_correct": summary_row.get("pf_is_correct"),
        },
        "tool_call_count": len(tools_sorted),
        "assistant_action_count": assistant_action_count,
        "tool_observation_count": tool_obs_count,
    }

    sft_rec = {
        "schema_version": SFT_SCHEMA_VERSION,
        "id": stable_id,
        "messages": messages,
        "tools": tools_schema,
        "metadata": metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return sft_rec, None


def _build_rl_prompt_from_sft(rec: dict[str, Any], idx: int) -> dict[str, Any]:
    msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    prompt: list[dict[str, str]] = []
    for m in msgs:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "")
        if role in {"system", "user"}:
            prompt.append({"role": role, "content": str(m.get("content") or "")})
        if len(prompt) >= 2:
            break

    meta = rec.get("metadata") if isinstance(rec.get("metadata"), dict) else {}
    task = str(meta.get("task_type") or "unknown")
    data_source = f"mol_pipeline_{task}"

    return {
        "id": rec.get("id"),
        "data_source": data_source,
        "prompt": prompt,
        "ability": "mol_pipeline_tool_use",
        "reward_model": {"style": "rule", "ground_truth": ""},
        "extra_info": {
            "index": idx,
            "task_type": task,
            "source_run": meta.get("source_run"),
            "trajectory_id": rec.get("id"),
            "used_molclaw": True,
            "answer_hit_pass": meta.get("answer_hit_pass"),
            "tool_call_count": meta.get("tool_call_count"),
        },
        "env_kwargs": {
            "task": {
                "task_id": rec.get("id"),
                "task_type": task,
                "instruction": prompt[1]["content"] if len(prompt) > 1 else "",
                "inputs": {},
                "allowed_tools": [t.get("name") for t in (rec.get("tools") or []) if isinstance(t, dict) and isinstance(t.get("name"), str)],
                "max_steps": 8,
                "data_source": data_source,
            }
        },
        "metadata": {
            "source_project": "mol-pipeline",
            "schema_version": RL_SCHEMA_VERSION,
        },
    }


def _load_summary_map(csv_path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not csv_path.is_file():
        return out
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            copied = str(row.get("copied_path") or "").strip()
            if copied:
                out[str(Path(copied).resolve())] = row
    return out


def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y"}


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert accepted molclaw usage sessions to unified SFT/RL JSONL (all-in-one).")
    ap.add_argument("--input-root", required=True, help="Directory from scan_molclaw_usage.py")
    ap.add_argument("--output-dir", default="", help="Default: <input-root>/sft_outputs")
    ap.add_argument("--summary-csv", default="", help="Default: <input-root>/molclaw_usage_summary.csv")
    ap.add_argument("--answer-hit-only", action="store_true", help="Only keep answer-hit samples for vs/ac/pf. kg/e2e are not filtered.")
    ap.add_argument(
        "--tool-role-mode",
        choices=["tool", "user_observation"],
        default="user_observation",
        help="Tool observation role representation.",
    )
    args = ap.parse_args()

    input_root = Path(args.input_root).expanduser().resolve()
    if not input_root.is_dir():
        raise NotADirectoryError(input_root)

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir.strip() else (input_root / "sft_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_csv = Path(args.summary_csv).expanduser().resolve() if args.summary_csv.strip() else (input_root / "molclaw_usage_summary.csv")
    summary_map = _load_summary_map(summary_csv)

    candidates: list[tuple[str, Path]] = []
    for task in SUPPORTED_TASKS:
        task_dir = input_root / task
        if not task_dir.is_dir():
            continue
        for p in sorted(task_dir.glob("*.jsonl")):
            candidates.append((task, p.resolve()))

    sft_records: list[dict[str, Any]] = []
    rl_records: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    filtered_answer_hit = 0

    for task, copied_path in candidates:
        summary_row = summary_map.get(str(copied_path), {})
        if args.answer_hit_only and task in {"vs", "ac", "pf"}:
            if not _to_bool(summary_row.get("answer_hit_pass")):
                filtered_answer_hit += 1
                continue

        original_path = str(summary_row.get("original_path") or "")
        rec, rej = _process_session(
            copied_path=copied_path,
            task=task,
            tool_role_mode=args.tool_role_mode,
            original_path=original_path,
            summary_row=summary_row,
        )
        if rec is None:
            rejected.append(rej or {"copied_path": str(copied_path), "reason": "unknown"})
            continue

        sft_records.append(rec)

    for i, rec in enumerate(sft_records):
        rl_records.append(_build_rl_prompt_from_sft(rec, i))

    sft_path = output_dir / "mcp_sft_all.jsonl"
    rl_path = output_dir / "mcp_rl_prompts_all.jsonl"
    rej_path = output_dir / "rejected_samples.jsonl"
    manifest_path = output_dir / "dataset_manifest.json"
    report_path = output_dir / "schema_validation_report.md"

    _write_jsonl(sft_path, sft_records)
    _write_jsonl(rl_path, rl_records)
    _write_jsonl(rej_path, rejected)

    manifest = {
        "schema_version": SFT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_root": str(input_root),
        "summary_csv": str(summary_csv),
        "output_files": {
            "sft_all": str(sft_path),
            "rl_all": str(rl_path),
            "rejected": str(rej_path),
        },
        "counts": {
            "raw_candidates": len(candidates),
            "accepted": len(sft_records),
            "rejected": len(rejected),
            "filtered_by_answer_hit": filtered_answer_hit,
        },
        "tasks": {task: sum(1 for r in sft_records if (r.get("metadata") or {}).get("task_type") == task) for task in SUPPORTED_TASKS},
        "options": {
            "answer_hit_only": bool(args.answer_hit_only),
            "tool_role_mode": args.tool_role_mode,
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_lines = [
        "# Postprocess Report",
        "",
        f"- input_root: `{input_root}`",
        f"- summary_csv: `{summary_csv}`",
        f"- raw_candidates: {len(candidates)}",
        f"- accepted: {len(sft_records)}",
        f"- rejected: {len(rejected)}",
        f"- filtered_by_answer_hit: {filtered_answer_hit}",
        f"- answer_hit_only: {int(bool(args.answer_hit_only))}",
        "",
        "## Task Counts",
        "",
    ]
    for task in SUPPORTED_TASKS:
        report_lines.append(f"- `{task}`: {manifest['tasks'][task]}")
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "input_root": str(input_root),
        "output_dir": str(output_dir),
        "sft_all": str(sft_path),
        "rl_all": str(rl_path),
        "rejected": str(rej_path),
        "manifest": str(manifest_path),
        "raw_candidates": len(candidates),
        "accepted": len(sft_records),
        "rejected_count": len(rejected),
        "filtered_by_answer_hit": filtered_answer_hit,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

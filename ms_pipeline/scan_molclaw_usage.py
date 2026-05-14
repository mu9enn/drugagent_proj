#!/usr/bin/env python3
import argparse
import csv
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set

NEEDLE = '"name":"mcp__molclaw'
RUN_RE = re.compile(r"^molbench_(vs|ac|pf)_.+_run_(\d{8})_(\d{6})(?:_.+)?$")
ROW_RE = re.compile(r"^row\d+_idx\d+$")


def parse_meta(path: Path) -> Dict[str, str]:
    # Supports:
    # 1) .../run_xxx/rowXXXX_idxYY/complete_session.jsonl
    # 2) .../run_xxx/rowXXXX_idxYY/rollout0001/complete_session.jsonl
    row_dir = ""
    run_dir = ""
    for anc in [path.parent] + list(path.parents):
        if not row_dir and ROW_RE.match(anc.name):
            row_dir = anc.name
        if not run_dir and RUN_RE.match(anc.name):
            run_dir = anc.name
        if row_dir and run_dir:
            break

    task = "unknown"
    task_m = re.search(r"molbench_(vs|ac|pf)_", run_dir)
    if task_m:
        task = task_m.group(1)

    date_str = "unknown_date"
    time_str = "unknown_time"
    run_m = re.search(r"run_(\d{8})_(\d{6})", run_dir)
    if run_m:
        date_str = run_m.group(1)
        time_str = run_m.group(2)

    idx_str = "unknown_idx"
    idx_m = re.search(r"idx\d+", row_dir)
    if idx_m:
        idx_str = idx_m.group(0)

    row_str = "unknown_row"
    row_m = re.search(r"row\d+", row_dir)
    if row_m:
        row_str = row_m.group(0)

    return {
        "task": task,
        "run_dir": run_dir,
        "row_dir": row_dir,
        "date": date_str,
        "time": time_str,
        "idx": idx_str,
        "row": row_str,
    }


def count_needle_in_file(file_path: Path, needle: str) -> int:
    cnt = 0
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            cnt += line.count(needle)
    return cnt


def unique_dst(dst: Path) -> Path:
    if not dst.exists():
        return dst
    stem = dst.stem
    suffix = dst.suffix
    i = 2
    while True:
        candidate = dst.with_name(f"{stem}__dup{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def ensure_task_dirs(output_root: Path) -> Dict[str, Path]:
    task_dirs = {
        "vs": output_root / "vs",
        "ac": output_root / "ac",
        "pf": output_root / "pf",
    }
    for d in task_dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return task_dirs


def _resolve_session_path_from_record(rec: Dict, run_dir: Path) -> Optional[Path]:
    def _try_from_sample_dir(sample_dir_str: str) -> Optional[Path]:
        p = Path(sample_dir_str)
        if not p.is_absolute():
            p = run_dir / p
        p = p.resolve()

        direct = p / "complete_session.jsonl"
        if direct.exists():
            return direct

        rollout_idx = rec.get("rollout_index")
        if isinstance(rollout_idx, int):
            one = p / f"rollout{rollout_idx:04d}" / "complete_session.jsonl"
            if one.exists():
                return one

        cand = sorted(p.glob("rollout*/complete_session.jsonl"))
        if cand:
            return cand[0]
        return None

    sample_dir = rec.get("sample_dir")
    if isinstance(sample_dir, str) and sample_dir.strip():
        resolved = _try_from_sample_dir(sample_dir)
        if resolved is not None:
            return resolved

    task_id = rec.get("task_id", "")
    m = re.search(r"(row\d+_idx\d+)", task_id)
    row_dir = m.group(1) if m else ""
    if not row_dir:
        row_number = rec.get("row_number")
        dataset_index = rec.get("dataset_index")
        if isinstance(row_number, int) and dataset_index is not None:
            row_dir = f"row{row_number:04d}_idx{dataset_index}"

    if row_dir:
        base = run_dir / row_dir
        direct = base / "complete_session.jsonl"
        if direct.exists():
            return direct
        rollout_idx = rec.get("rollout_index")
        if isinstance(rollout_idx, int):
            one = base / f"rollout{rollout_idx:04d}" / "complete_session.jsonl"
            if one.exists():
                return one
        cand = sorted(base.glob("rollout*/complete_session.jsonl"))
        if cand:
            return cand[0]

    return None


def collect_all_complete_session_files(results_root: Path) -> List[Path]:
    return sorted(results_root.rglob("complete_session.jsonl"))


def collect_complete_session_files_from_accepted(results_root: Path) -> Dict[str, object]:
    accepted_files = sorted(results_root.rglob("trajectories/accepted.jsonl"))
    resolved: Set[Path] = set()
    stats = {
        "accepted_jsonl_files": len(accepted_files),
        "accepted_lines_total": 0,
        "accepted_lines_valid_json": 0,
        "accepted_lines_selected": 0,
        "accepted_lines_unresolved": 0,
        "accepted_lines_bad_json": 0,
        "accepted_lines_empty": 0,
    }

    for accepted_path in accepted_files:
        run_dir = accepted_path.parent.parent
        if not run_dir.exists():
            continue
        try:
            with accepted_path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stats["accepted_lines_total"] += 1
                    line = line.strip()
                    if not line:
                        stats["accepted_lines_empty"] += 1
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        stats["accepted_lines_bad_json"] += 1
                        continue
                    stats["accepted_lines_valid_json"] += 1

                    # accepted.jsonl should already be accepted-only, but keep a safe check.
                    status = str(rec.get("status", "")).lower()
                    if status and status != "accepted":
                        continue

                    stats["accepted_lines_selected"] += 1
                    session_path = _resolve_session_path_from_record(rec, run_dir)
                    if session_path is None:
                        stats["accepted_lines_unresolved"] += 1
                        continue
                    resolved.add(session_path)
        except OSError:
            continue

    return {
        "files": sorted(resolved),
        "stats": stats,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    default_results_root = repo_root / "results"
    default_output_root = default_results_root / "molclaw_usage_export"

    parser = argparse.ArgumentParser(
        description="Scan complete_session.jsonl files for mcp__molclaw usage, export CSV, and copy matched files by task."
    )
    parser.add_argument(
        "--results-root",
        default=str(default_results_root),
        help="Root directory to scan recursively (default: %(default)s)",
    )
    parser.add_argument(
        "--output-root",
        default=str(default_output_root),
        help="Output root directory for CSV and copied files (default: %(default)s)",
    )
    parser.add_argument(
        "--csv-name",
        default="molclaw_usage_summary.csv",
        help="CSV filename under output root (default: %(default)s)",
    )
    parser.add_argument(
        "--needle",
        default=NEEDLE,
        help="Substring to count in each jsonl file (default: %(default)s)",
    )
    parser.add_argument(
        "--use-accepted-only",
        action="store_true",
        help=(
            "Only scan complete_session.jsonl referenced by each run's "
            "trajectories/accepted.jsonl records."
        ),
    )
    args = parser.parse_args()

    results_root = Path(args.results_root).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    csv_path = output_root / args.csv_name

    if not results_root.exists():
        raise FileNotFoundError(f"results_root does not exist: {results_root}")

    output_root.mkdir(parents=True, exist_ok=True)
    task_dirs = ensure_task_dirs(output_root)

    accepted_stats = None
    if args.use_accepted_only:
        accepted_result = collect_complete_session_files_from_accepted(results_root)
        jsonl_files = accepted_result["files"]
        accepted_stats = accepted_result["stats"]
    else:
        jsonl_files = collect_all_complete_session_files(results_root)

    rows = []
    matched_files = 0
    matched_calls = 0

    for jsonl in jsonl_files:
        call_count = count_needle_in_file(jsonl, args.needle)
        if call_count <= 0:
            continue

        meta = parse_meta(jsonl)
        task = meta["task"]

        if task in task_dirs:
            dst_dir = task_dirs[task]
        else:
            dst_dir = output_root / "unknown"
            dst_dir.mkdir(parents=True, exist_ok=True)

        new_name = f"{meta['task']}_{meta['date']}_{meta['time']}_{meta['row']}_{meta['idx']}.jsonl"
        dst_path = unique_dst(dst_dir / new_name)
        shutil.copy2(jsonl, dst_path)

        rows.append(
            {
                "original_path": str(jsonl),
                "molclaw_call_count": call_count,
                "task": meta["task"],
                "date": meta["date"],
                "time": meta["time"],
                "row": meta["row"],
                "idx": meta["idx"],
                "copied_path": str(dst_path),
            }
        )
        matched_files += 1
        matched_calls += call_count

    fieldnames = [
        "original_path",
        "molclaw_call_count",
        "task",
        "date",
        "time",
        "row",
        "idx",
        "copied_path",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Scanned complete_session.jsonl files: {len(jsonl_files)}")
    if accepted_stats is not None:
        print("Accepted filter mode: ON")
        print(
            "Accepted files discovered: "
            f"{accepted_stats['accepted_jsonl_files']}, "
            f"lines total: {accepted_stats['accepted_lines_total']}, "
            f"valid JSON: {accepted_stats['accepted_lines_valid_json']}, "
            f"selected: {accepted_stats['accepted_lines_selected']}, "
            f"unresolved: {accepted_stats['accepted_lines_unresolved']}"
        )
    else:
        print("Accepted filter mode: OFF")
    print(f"Matched files (count > 0): {matched_files}")
    print(f"Total '{args.needle}' occurrences: {matched_calls}")
    print(f"CSV written to: {csv_path}")
    print(f"Copied files root: {output_root}")


if __name__ == "__main__":
    main()

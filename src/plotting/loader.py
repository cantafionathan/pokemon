from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from .models import LogEntry, RunLog


def load_log_file(path: Path) -> List[LogEntry]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError(f"Expected list in log file {path}")

    return [LogEntry.from_json(obj) for obj in raw]


def load_logs_from_path(path: Path) -> List[RunLog]:
    if path.is_file():
        paths = [path]
    elif path.is_dir():
        paths = sorted(path.rglob("*.json"))
    else:
        raise FileNotFoundError(path)

    entries: List[LogEntry] = []
    for p in paths:
        entries.extend(load_log_file(p))

    return group_entries_by_run(entries)


def group_entries_by_run(entries: List[LogEntry]) -> List[RunLog]:
    """
    Group by (method, run_seed, run_id).
    Each group corresponds to exactly one optimizer execution.
    """
    grouped: Dict[Tuple[str, int | None, str], List[LogEntry]] = {}

    for e in entries:
        key = (e.method, e.run_seed, e.run_id, e.format)
        grouped.setdefault(key, []).append(e)

    return [
        RunLog(
            method=method,
            run_seed=seed,
            run_id=run_id,
            format=format,
            entries=ents,
        )
        for (method, seed, run_id, format), ents in grouped.items()
    ]


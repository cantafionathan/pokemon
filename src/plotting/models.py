from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from collections import defaultdict

Team = Tuple[List[int], List[List[int]]]


@dataclass(frozen=True)
class LogEntry:
    """
    Represents a single logged evaluation of one team.
    """
    timestamp: str
    generation: int
    score: float
    total_battles_used: int
    runtime_sec: float
    run_seed: int | None
    method: str
    run_id: str
    team: Team
    format: str
    raw: Dict[str, Any]

    @staticmethod
    def from_json(obj: Dict[str, Any]) -> "LogEntry":
        team_field = obj.get("team")

        if isinstance(team_field, str):
            team: Team = tuple(json.loads(team_field))
        else:
            team = tuple(team_field)

        return LogEntry(
            timestamp=obj["timestamp"],
            generation=int(obj["generation"]),
            score=float(obj["score"]),
            total_battles_used=int(obj["total_battles_used"]),
            runtime_sec=float(obj["runtime_sec"]),
            run_seed=obj.get("run_seed"),
            method=obj.get("method", "unknown"),
            run_id=obj.get("run_id", "unknown"),
            team=team,
            format=obj.get("format", "unknown"),
            raw=obj,
        )


@dataclass
class RunLog:
    """
    Represents all log entries from a single run
    (one optimizer execution, one seed, one method).
    """
    run_seed: int | None
    method: str
    run_id: str
    format: str
    entries: List[LogEntry]

    def __post_init__(self):
        self.entries.sort(key=lambda e: e.total_battles_used)

    @property
    def generations(self) -> List[int]:
        return sorted({e.generation for e in self.entries})

    def entries_by_generation(self) -> Dict[int, List[LogEntry]]:
        by_gen: Dict[int, List[LogEntry]] = defaultdict(list)
        for e in self.entries:
            by_gen[e.generation].append(e)
        return by_gen

    def best_per_generation(self) -> List[LogEntry]:
        """
        Best-scoring team in each generation.
        """
        best = []
        for gen, entries in self.entries_by_generation().items():
            best.append(max(entries, key=lambda e: e.score))
        return sorted(best, key=lambda e: e.generation)

    def global_best(self) -> LogEntry:
        return max(self.entries, key=lambda e: e.score)

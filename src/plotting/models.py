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
        by_gen = self.entries_by_generation()
        best = []

        for gen in sorted(by_gen.keys()):
            best.append(max(by_gen[gen], key=lambda e: e.score))

        return best

    
    def best_so_far_per_generation(self) -> List[LogEntry]:
        """
        Best-scoring team seen up to and including each generation.
        (Cumulative maximum over generations.)
        """
        best_by_gen = self.best_per_generation()

        best_so_far: List[LogEntry] = []
        current_best: LogEntry | None = None

        for entry in best_by_gen:
            if current_best is None or entry.score > current_best.score:
                current_best = entry
            best_so_far.append(current_best)

        return best_so_far




    def global_best(self) -> LogEntry:
        return max(self.entries, key=lambda e: e.score)

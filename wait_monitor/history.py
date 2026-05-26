from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import AggregatedWaitStat, StoredSnapshot
from .util import parse_iso_datetime


def history_file_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "wait_history.jsonl"


def ensure_history_file() -> Path:
    file_path = history_file_path()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.write_text("", encoding="utf-8")
    return file_path


def start_run(started_at: datetime) -> tuple[Path, str]:
    return ensure_history_file(), started_at.isoformat(timespec="seconds")


def load_snapshot_history_map(airport_code: str, limit_per_key: int = 2) -> dict[tuple[str, str, str], list[StoredSnapshot]]:
    file_path = ensure_history_file()
    snapshots: dict[tuple[str, str, str], list[StoredSnapshot]] = {}
    lines = file_path.read_text(encoding="utf-8").splitlines()

    for raw_line in reversed(lines):
        if not raw_line.strip():
            continue
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        if payload.get("airport_code") != airport_code:
            continue

        recorded_at = parse_iso_datetime(payload.get("recorded_at"))
        if recorded_at is None:
            continue

        key = (
            str(payload.get("service") or ""),
            str(payload.get("checkpoint") or ""),
            str(payload.get("gates") or ""),
        )
        bucket = snapshots.setdefault(key, [])
        if len(bucket) >= limit_per_key:
            continue

        avg_value = payload.get("avg")
        low_value = payload.get("low")
        high_value = payload.get("high")
        samples = payload.get("samples")
        airport_name = payload.get("airport_name")
        if avg_value is None or low_value is None or high_value is None or samples is None or not airport_name:
            continue

        bucket.append(
            StoredSnapshot(
            airport_code=airport_code,
            airport_name=str(airport_name),
            service=key[0],
            checkpoint=key[1],
            gates=key[2] or None,
            low=float(low_value),
            avg=float(avg_value),
            high=float(high_value),
            samples=int(samples),
            recorded_at=recorded_at,
        )
        )

    return snapshots


def append_snapshots(run_id: str, recorded_at: datetime, stats: list[AggregatedWaitStat]) -> None:
    if not stats:
        return

    file_path = ensure_history_file()
    with file_path.open("a", encoding="utf-8") as handle:
        for stat in stats:
            payload = {
                "run_id": run_id,
                "recorded_at": recorded_at.isoformat(timespec="seconds"),
                "airport_code": stat.airport_code,
                "airport_name": stat.airport_name,
                "service": stat.service,
                "checkpoint": stat.checkpoint,
                "gates": stat.gates,
                "low": stat.low,
                "avg": stat.avg,
                "high": stat.high,
                "samples": stat.samples,
            }
            handle.write(json.dumps(payload, separators=(",", ":")) + "\n")

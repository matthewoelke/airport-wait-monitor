from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import re
from statistics import mean

from .config import AIRPORTS, static_metadata
from .history import append_snapshots, load_snapshot_history_map, start_run
from .models import (
    AggregatedWaitStat,
    CheckpointMetadata,
    SourceResult,
    StoredSnapshot,
    WaitObservation,
)
from .sources import collect_airporstinsights_dca, collect_flightqueue, collect_takeofftimer


SUPPORTED_AIRPORTS = tuple(sorted(AIRPORTS))
MIN_FETCH_INTERVAL_SECONDS = 60


def format_age(now: datetime, then: datetime) -> str:
    seconds = age_seconds(now, then)
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def age_seconds(now: datetime, then: datetime) -> int:
    delta = now - then
    return max(int(delta.total_seconds()), 0)


def normalize_airport_code(value: str) -> str | None:
    cleaned = (value or "").strip().upper()
    if re.fullmatch(r"[A-Z]{3}", cleaned):
        return cleaned
    return None


def snapshot_key(service: str, checkpoint: str, gates: str | None) -> tuple[str, str, str]:
    return service, checkpoint, gates or ""


def collect_airport(airport_code: str) -> SourceResult:
    aggregate = SourceResult()
    sources = [
        collect_takeofftimer(airport_code),
        collect_flightqueue(airport_code),
        collect_airporstinsights_dca(airport_code),
    ]

    for source_result in sources:
        aggregate.observations.extend(source_result.observations)
        aggregate.metadata.extend(source_result.metadata)
        aggregate.warnings.extend(source_result.warnings)

    aggregate.metadata.extend(
        [row for row in static_metadata() if row.airport_code == airport_code]
    )
    return aggregate


def aggregate_waits(airport_code: str, airport_name: str, observations: list[WaitObservation]) -> list[AggregatedWaitStat]:
    groups: dict[tuple[str, str, str], list[WaitObservation]] = defaultdict(list)
    for observation in observations:
        if observation.wait_minutes is None:
            continue
        groups[snapshot_key(observation.service, observation.checkpoint, observation.gates)].append(observation)

    rows: list[AggregatedWaitStat] = []
    for (service, checkpoint, gates), items in sorted(groups.items()):
        values = [item.wait_minutes for item in items if item.wait_minutes is not None]
        if not values:
            continue
        rows.append(
            AggregatedWaitStat(
                airport_code=airport_code,
                airport_name=airport_name,
                service=service,
                checkpoint=checkpoint,
                gates=gates or None,
                low=min(values),
                avg=mean(values),
                high=max(values),
                samples=len(values),
            )
        )
    return rows


def stat_matches_snapshot(stat: AggregatedWaitStat, snapshot: StoredSnapshot) -> bool:
    return (
        stat.low == snapshot.low
        and stat.avg == snapshot.avg
        and stat.high == snapshot.high
        and stat.samples == snapshot.samples
    )


def checkpoint_label(checkpoint: str, gates: str | None) -> str:
    return checkpoint if not gates else f"{checkpoint} ({gates})"


def invalid_airport_payload(requested_code: str, generated_at: datetime) -> dict:
    return {
        "requested_airport_code": requested_code,
        "airport_code": requested_code,
        "found": False,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "services": [
            {
                "service": "Security",
                "entries": [
                    {
                        "checkpoint": "All Checkpoints",
                        "gates": None,
                        "status": "Airport Not Found",
                    }
                ],
            }
        ],
        "warnings": [],
    }


def build_airport_payload(airport_code: str) -> dict:
    requested_code = (airport_code or "").strip().upper()
    generated_at = datetime.now(timezone.utc)
    normalized_code = normalize_airport_code(airport_code)

    if normalized_code is None or normalized_code not in AIRPORTS:
        return invalid_airport_payload(requested_code, generated_at)

    airport_name = AIRPORTS[normalized_code]["name"]
    _, run_id = start_run(generated_at)
    history_map = load_snapshot_history_map(normalized_code, limit_per_key=2)
    latest_cached_time = max(
        (snapshots[0].recorded_at for snapshots in history_map.values() if snapshots),
        default=None,
    )
    skip_live_fetch = (
        latest_cached_time is not None
        and age_seconds(generated_at, latest_cached_time) < MIN_FETCH_INTERVAL_SECONDS
    )
    if skip_live_fetch:
        source_result = SourceResult(
            metadata=[row for row in static_metadata() if row.airport_code == normalized_code],
            warnings=[
                (
                    "Skipped live refresh because cached values were updated "
                    f"{format_age(generated_at, latest_cached_time)}."
                )
            ],
        )
        current_stats: list[AggregatedWaitStat] = []
    else:
        source_result = collect_airport(normalized_code)
        current_stats = aggregate_waits(normalized_code, airport_name, source_result.observations)
    changed_stats: list[AggregatedWaitStat] = []
    service_groups: dict[str, list[dict]] = defaultdict(list)
    overall_current_times: list[datetime] = []
    used_stored_current = skip_live_fetch or not current_stats

    stat_map = {snapshot_key(stat.service, stat.checkpoint, stat.gates): stat for stat in current_stats}
    all_keys = set(history_map) | set(stat_map)

    for key in sorted(all_keys):
        service, checkpoint, gates_text = key
        gates = gates_text or None
        stat = stat_map.get(key)
        history = history_map.get(key, [])
        latest = history[0] if history else None
        previous = history[1] if len(history) > 1 else None

        current_block: dict | None = None
        previous_block: dict | None = None

        if stat is not None:
            if latest and stat_matches_snapshot(stat, latest):
                used_stored_current = True
                current_snapshot = latest
                previous_snapshot = previous
            else:
                current_snapshot = StoredSnapshot(
                    airport_code=stat.airport_code,
                    airport_name=stat.airport_name,
                    service=stat.service,
                    checkpoint=stat.checkpoint,
                    gates=stat.gates,
                    low=stat.low,
                    avg=stat.avg,
                    high=stat.high,
                    samples=stat.samples,
                    recorded_at=generated_at,
                )
                previous_snapshot = latest
                changed_stats.append(stat)

            current_block = {
                "low_minutes": current_snapshot.low,
                "avg_minutes": current_snapshot.avg,
                "high_minutes": current_snapshot.high,
                "samples": current_snapshot.samples,
                "recorded_at": current_snapshot.recorded_at.isoformat(timespec="seconds"),
                "updated_ago": format_age(generated_at, current_snapshot.recorded_at),
                "updated_age_seconds": age_seconds(generated_at, current_snapshot.recorded_at),
            }
            overall_current_times.append(current_snapshot.recorded_at)
            if previous_snapshot is not None:
                previous_block = {
                    "low_minutes": previous_snapshot.low,
                    "avg_minutes": previous_snapshot.avg,
                    "high_minutes": previous_snapshot.high,
                    "samples": previous_snapshot.samples,
                    "recorded_at": previous_snapshot.recorded_at.isoformat(timespec="seconds"),
                    "updated_ago": format_age(generated_at, previous_snapshot.recorded_at),
                    "updated_age_seconds": age_seconds(generated_at, previous_snapshot.recorded_at),
                }
        elif latest is not None:
            used_stored_current = True
            current_block = {
                "low_minutes": latest.low,
                "avg_minutes": latest.avg,
                "high_minutes": latest.high,
                "samples": latest.samples,
                "recorded_at": latest.recorded_at.isoformat(timespec="seconds"),
                "updated_ago": format_age(generated_at, latest.recorded_at),
                "updated_age_seconds": age_seconds(generated_at, latest.recorded_at),
            }
            overall_current_times.append(latest.recorded_at)
            if previous is not None:
                previous_block = {
                    "low_minutes": previous.low,
                    "avg_minutes": previous.avg,
                    "high_minutes": previous.high,
                    "samples": previous.samples,
                    "recorded_at": previous.recorded_at.isoformat(timespec="seconds"),
                    "updated_ago": format_age(generated_at, previous.recorded_at),
                    "updated_age_seconds": age_seconds(generated_at, previous.recorded_at),
                }

        if current_block is None:
            continue

        delta = None
        direction = "same"
        if previous_block is not None:
            delta = round(current_block["avg_minutes"] - previous_block["avg_minutes"], 1)
            if delta > 0:
                direction = "up"
            elif delta < 0:
                direction = "down"

        service_groups[service].append(
            {
                "checkpoint": checkpoint,
                "checkpoint_label": checkpoint_label(checkpoint, gates),
                "gates": gates,
                "current": current_block,
                "previous": previous_block,
                "delta_avg_minutes": delta,
                "delta_direction": direction if delta is not None else None,
            }
        )

    if changed_stats:
        append_snapshots(run_id, generated_at, changed_stats)

    metadata_rows: list[dict] = []
    deduped_metadata: dict[tuple[str, str, str], CheckpointMetadata] = {}
    for item in source_result.metadata:
        deduped_metadata[(item.checkpoint, item.gates or "", item.source_name)] = item
    for item in sorted(deduped_metadata.values(), key=lambda row: (row.checkpoint, row.source_name, row.gates or "")):
        metadata_rows.append(
            {
                "checkpoint": item.checkpoint,
                "checkpoint_label": checkpoint_label(item.checkpoint, item.gates),
                "gates": item.gates,
                "services": list(item.services),
                "status": item.status,
                "hours": item.hours,
                "source_name": item.source_name,
                "source_url": item.source_url,
            }
        )

    services = [
        {
            "service": service,
            "entries": sorted(
                entries,
                key=lambda entry: (
                    entry["checkpoint"] != "All Checkpoints",
                    entry["checkpoint_label"],
                ),
            ),
        }
        for service, entries in sorted(service_groups.items())
    ]

    latest_current_time = max(overall_current_times) if overall_current_times else None
    return {
        "requested_airport_code": requested_code,
        "airport_code": normalized_code,
        "airport_name": airport_name,
        "found": True,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "last_updated_at": latest_current_time.isoformat(timespec="seconds") if latest_current_time else None,
        "last_updated_ago": format_age(generated_at, latest_current_time) if latest_current_time else None,
        "last_updated_age_seconds": age_seconds(generated_at, latest_current_time) if latest_current_time else None,
        "used_cached_current": used_stored_current and not changed_stats,
        "live_fetch_skipped": skip_live_fetch,
        "services": services,
        "metadata": metadata_rows,
        "warnings": source_result.warnings,
    }


def build_all_airports_payload() -> dict:
    generated_at = datetime.now(timezone.utc)
    airports = [build_airport_payload(code) for code in SUPPORTED_AIRPORTS]
    return {
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "airports": airports,
    }

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class WaitObservation:
    airport_code: str
    airport_name: str
    service: str
    checkpoint: str
    gates: str | None
    wait_minutes: float | None
    wait_text: str
    source_name: str
    source_url: str
    fetched_at: datetime
    source_refreshed_at: datetime | None = None
    source_refresh_note: str | None = None
    notes: str | None = None
    is_upper_bound: bool = False


@dataclass(frozen=True)
class CheckpointMetadata:
    airport_code: str
    airport_name: str
    checkpoint: str
    gates: str | None
    services: tuple[str, ...]
    status: str | None
    hours: str | None
    source_name: str
    source_url: str
    source_refreshed_at: datetime | None = None
    source_refresh_note: str | None = None
    notes: str | None = None


@dataclass
class SourceResult:
    observations: list[WaitObservation] = field(default_factory=list)
    metadata: list[CheckpointMetadata] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AggregatedWaitStat:
    airport_code: str
    airport_name: str
    service: str
    checkpoint: str
    gates: str | None
    low: float
    avg: float
    high: float
    samples: int


@dataclass(frozen=True)
class PreviousSnapshot:
    airport_code: str
    service: str
    checkpoint: str
    gates: str | None
    avg: float
    recorded_at: datetime


@dataclass(frozen=True)
class StoredSnapshot:
    airport_code: str
    airport_name: str
    service: str
    checkpoint: str
    gates: str | None
    low: float
    avg: float
    high: float
    samples: int
    recorded_at: datetime

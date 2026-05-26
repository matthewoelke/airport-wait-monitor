from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup

from .config import AIRPORTS
from .models import CheckpointMetadata, SourceResult, WaitObservation
from .util import (
    collapse_spaces,
    fetch_text,
    find_json_ld_blocks,
    normalize_minutes_text,
    parse_iso_datetime,
    safe_float,
    soup_from_html,
)


def collect_takeofftimer(airport_code: str) -> SourceResult:
    airport = AIRPORTS[airport_code]
    fetched_at = datetime.now(timezone.utc)
    result = SourceResult()

    try:
        raw = fetch_text(airport["takeofftimer_api"])
        data = json.loads(raw)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        result.warnings.append(f"TakeoffTimer failed for {airport_code}: {exc}")
        return result

    current = data.get("currentWait", {})
    wait_minutes = safe_float(current.get("standard"))
    wait_text = collapse_spaces(str(current.get("standardDescription") or current.get("standard") or ""))
    refreshed_at = parse_iso_datetime(current.get("timestamp"))

    if wait_minutes is not None:
        result.observations.append(
            WaitObservation(
                airport_code=airport_code,
                airport_name=airport["name"],
                service="Security",
                checkpoint="All Checkpoints",
                gates=None,
                wait_minutes=wait_minutes,
                wait_text=wait_text or f"{int(wait_minutes)} min",
                source_name="TakeoffTimer API",
                source_url=airport["takeofftimer_page"],
                fetched_at=fetched_at,
                source_refreshed_at=refreshed_at,
                source_refresh_note="API payload includes a source timestamp.",
            )
        )

    precheck_checkpoints = data.get("precheckCheckpoints") or {}
    for terminal, checkpoint_map in precheck_checkpoints.items():
        if not isinstance(checkpoint_map, dict):
            continue
        for checkpoint_name, status in checkpoint_map.items():
            result.metadata.append(
                CheckpointMetadata(
                    airport_code=airport_code,
                    airport_name=airport["name"],
                    checkpoint=terminal,
                    gates=checkpoint_name,
                    services=("TSA PreCheck",),
                    status=collapse_spaces(str(status)),
                    hours=None,
                    source_name="TakeoffTimer API",
                    source_url=airport["takeofftimer_page"],
                    source_refreshed_at=refreshed_at,
                    source_refresh_note="Live checkpoint status from TakeoffTimer API.",
                )
            )

    return result


def collect_flightqueue(airport_code: str) -> SourceResult:
    airport = AIRPORTS[airport_code]
    fetched_at = datetime.now(timezone.utc)
    result = SourceResult()

    try:
        html = fetch_text(airport["flightqueue"])
    except (HTTPError, URLError, TimeoutError) as exc:
        result.warnings.append(f"FlightQueue failed for {airport_code}: {exc}")
        return result

    soup = soup_from_html(html)
    title_text = collapse_spaces(soup.title.get_text(" ", strip=True) if soup.title else "")
    title_match = re.search(r"\)\s+[–-]\s+(\d+)\s+Min Right Now", title_text)
    if title_match:
        wait_minutes = float(title_match.group(1))
        result.observations.append(
            WaitObservation(
                airport_code=airport_code,
                airport_name=airport["name"],
                service="Security",
                checkpoint="All Checkpoints",
                gates=None,
                wait_minutes=wait_minutes,
                wait_text=f"{int(wait_minutes)} min",
                source_name="FlightQueue",
                source_url=airport["flightqueue"],
                fetched_at=fetched_at,
                source_refreshed_at=None,
                source_refresh_note="Page claims wait times are updated every 5 minutes, but no exact timestamp was exposed.",
            )
        )

    for meta in soup.find_all("meta", attrs={"name": "description"}):
        description = collapse_spaces(meta.get("content", ""))
        refresh_match = re.search(r"Updated every\s+(\d+)\s+min", description, re.IGNORECASE)
        precheck_match = re.search(r"TSA PreCheck lanes are typically under\s+(\d+)\s+minutes?", html, re.IGNORECASE)
        if precheck_match:
            minutes = float(precheck_match.group(1))
            result.observations.append(
                WaitObservation(
                    airport_code=airport_code,
                    airport_name=airport["name"],
                    service="TSA PreCheck",
                    checkpoint="All Checkpoints",
                    gates=None,
                    wait_minutes=minutes,
                    wait_text=f"<={int(minutes)} min",
                    source_name="FlightQueue",
                    source_url=airport["flightqueue"],
                    fetched_at=fetched_at,
                    source_refreshed_at=None,
                    source_refresh_note=(
                        f"Page claims updates every {refresh_match.group(1)} minutes."
                        if refresh_match
                        else "Page claims a frequent refresh interval, but no exact timestamp was exposed."
                    ),
                    notes="Approximate upper bound parsed from the FAQ content.",
                    is_upper_bound=True,
                )
            )
        break

    return result


def collect_airporstinsights_dca(airport_code: str) -> SourceResult:
    result = SourceResult()
    if airport_code != "DCA":
        return result

    airport = AIRPORTS[airport_code]
    fetched_at = datetime.now(timezone.utc)
    url = airport["checkpoint_waits"]

    try:
        html = fetch_text(url)
    except (HTTPError, URLError, TimeoutError) as exc:
        result.warnings.append(f"AirporstInsights failed for {airport_code}: {exc}")
        return result

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    refresh_match = re.search(r"latest update at\s+([0-9: ]+[AP]M)", text, re.IGNORECASE)
    refresh_note = (
        f"Page text says latest update at {refresh_match.group(1)} local time."
        if refresh_match
        else None
    )

    for table in soup.find_all("table"):
        rows = []
        for row in table.find_all("tr"):
            cells = [collapse_spaces(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if not rows:
            continue
        headers = [cell.lower() for cell in rows[0]]
        if "checkpoint" not in headers or "general lines" not in headers:
            continue

        checkpoint_index = headers.index("checkpoint")
        general_index = headers.index("general lines")
        precheck_index = headers.index("tsa precheck") if "tsa precheck" in headers else -1

        for row in rows[1:]:
            if len(row) <= max(checkpoint_index, general_index, max(precheck_index, 0)):
                continue
            checkpoint = row[checkpoint_index]
            if not checkpoint:
                continue

            general_minutes, general_text, general_upper = normalize_minutes_text(row[general_index])
            if general_minutes is not None:
                result.observations.append(
                    WaitObservation(
                        airport_code=airport_code,
                        airport_name=airport["name"],
                        service="Security",
                        checkpoint=checkpoint,
                        gates=None,
                        wait_minutes=general_minutes,
                        wait_text=general_text,
                        source_name="AirporstInsights",
                        source_url=url,
                        fetched_at=fetched_at,
                        source_refreshed_at=None,
                        source_refresh_note=refresh_note,
                        notes="Parsed from the DCA checkpoint table.",
                        is_upper_bound=general_upper,
                    )
                )

            if precheck_index >= 0 and precheck_index < len(row):
                pre_minutes, pre_text, pre_upper = normalize_minutes_text(row[precheck_index])
                if pre_minutes is not None:
                    result.observations.append(
                        WaitObservation(
                            airport_code=airport_code,
                            airport_name=airport["name"],
                            service="TSA PreCheck",
                            checkpoint=checkpoint,
                            gates=None,
                            wait_minutes=pre_minutes,
                            wait_text=pre_text,
                            source_name="AirporstInsights",
                            source_url=url,
                            fetched_at=fetched_at,
                            source_refreshed_at=None,
                            source_refresh_note=refresh_note,
                            notes="Parsed from the DCA checkpoint table.",
                            is_upper_bound=pre_upper,
                        )
                    )
        break

    return result

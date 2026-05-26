from __future__ import annotations

import argparse

from .config import AIRPORTS
from .models import CheckpointMetadata, WaitObservation
from .service import build_airport_payload, collect_airport


def shorten(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and aggregate posted airport security wait times for BWI, IAD, DCA, and BOS."
    )
    parser.add_argument(
        "airports",
        nargs="*",
        default=["BWI", "IAD", "DCA", "BOS"],
        help="Airport codes to query. Defaults to BWI IAD DCA BOS.",
    )
    return parser.parse_args()
def render_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    def format_row(values: list[str]) -> str:
        return " | ".join(value.ljust(widths[index]) for index, value in enumerate(values))

    parts = [format_row(headers), "-+-".join("-" * width for width in widths)]
    parts.extend(format_row(row) for row in rows)
    return "\n".join(parts)


def aggregated_rows(services: list[dict]) -> list[list[str]]:
    rows: list[list[str]] = []
    for service_group in services:
        service = service_group["service"]
        for entry in service_group["entries"]:
            current = entry["current"]
            previous = entry.get("previous")
            rows.append(
                [
                    service,
                    shorten(entry["checkpoint_label"], 37),
                    f"{current['low_minutes']:.1f}",
                    f"{current['avg_minutes']:.1f}",
                    f"{previous['avg_minutes']:.1f}" if previous else "-",
                    previous["updated_ago"] if previous else "-",
                    f"{current['high_minutes']:.1f}",
                    str(current["samples"]),
                ]
            )
    return rows


def observation_rows(observations: list[WaitObservation]) -> list[list[str]]:
    rows: list[list[str]] = []
    for item in sorted(
        observations,
        key=lambda observation: (observation.service, observation.checkpoint, observation.source_name),
    ):
        refreshed = (
            item.source_refreshed_at.isoformat(timespec="seconds")
            if item.source_refreshed_at
            else item.source_refresh_note or "unknown"
        )
        checkpoint = item.checkpoint if not item.gates else f"{item.checkpoint} ({item.gates})"
        note = item.notes or ""
        rows.append(
            [
                item.source_name,
                item.service,
                shorten(checkpoint, 34),
                item.wait_text,
                shorten(refreshed, 42),
                shorten(note, 42),
                shorten(item.source_url.replace("https://", ""), 56),
            ]
        )
    return rows


def metadata_rows(items: list[CheckpointMetadata]) -> list[list[str]]:
    deduped: dict[tuple[str, str, str], CheckpointMetadata] = {}
    for item in items:
        deduped[(item.checkpoint, item.gates or "", item.source_name)] = item

    rows: list[list[str]] = []
    for item in sorted(deduped.values(), key=lambda row: (row.checkpoint, row.source_name, row.gates or "")):
        checkpoint = item.checkpoint if not item.gates else f"{item.checkpoint} ({item.gates})"
        rows.append(
            [
                shorten(checkpoint, 34),
                shorten(", ".join(item.services), 28),
                item.status or "",
                shorten(item.hours or "", 36),
                item.source_name,
                shorten(item.source_url.replace("https://", ""), 56),
            ]
        )
    return rows


def main() -> int:
    args = parse_args()
    airport_codes = [code.upper() for code in args.airports]

    unsupported = [code for code in airport_codes if code not in AIRPORTS]
    if unsupported:
        supported = ", ".join(sorted(AIRPORTS))
        raise SystemExit(f"Unsupported airport(s): {', '.join(unsupported)}. Supported: {supported}")

    for airport_code in airport_codes:
        payload = build_airport_payload(airport_code)
        airport_name = payload["airport_name"]

        print(f"\n=== {airport_code} - {airport_name} ===\n")

        aggregated = aggregated_rows(payload["services"])
        if aggregated:
            print("Aggregated waits (minutes)")
            print(
                render_table(
                    ["Service", "Checkpoint / Gate", "Low", "Avg", "Prev Avg", "Prev Age", "High", "Samples"],
                    aggregated,
                )
            )
            print()
        else:
            print("No numeric wait observations found.\n")

        result = collect_airport(airport_code)
        details = observation_rows(result.observations)
        if details:
            print("Source observations")
            print(
                render_table(
                    ["Source", "Service", "Checkpoint / Gate", "Wait", "Source refreshed", "Notes", "URL"],
                    details,
                )
            )
            print()

        metadata = metadata_rows(result.metadata)
        if metadata:
            print("Checkpoint / service metadata")
            print(
                render_table(
                    ["Checkpoint / Gate", "Services", "Status", "Hours", "Source", "URL"],
                    metadata,
                )
            )
            print()

        if result.warnings:
            print("Warnings")
            for warning in result.warnings:
                print(f"- {warning}")
            print()

    return 0

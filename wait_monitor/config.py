from __future__ import annotations

from .models import CheckpointMetadata


USER_AGENT = "airport-wait-monitor/0.1 (+cli prototype)"

AIRPORTS: dict[str, dict[str, str]] = {
    "BOS": {
        "name": "Boston Logan International Airport",
        "takeofftimer_api": "https://www.takeofftimer.com/api/tsa-wait-times?code=BOS",
        "takeofftimer_page": "https://www.takeofftimer.com/tsa-wait-times/BOS",
        "flightqueue": "https://flightqueue.com/logan-international-airport-security-wait-times",
        "checkpoint_info": "https://www.airporstinsights.com/bos-airport/wait-times/",
    },
    "BWI": {
        "name": "Baltimore/Washington International Thurgood Marshall Airport",
        "takeofftimer_api": "https://www.takeofftimer.com/api/tsa-wait-times?code=BWI",
        "takeofftimer_page": "https://www.takeofftimer.com/tsa-wait-times/BWI",
        "flightqueue": "https://flightqueue.com/baltimorewashington-international-thurgood-marshall-airport-security-wait-times",
        "checkpoint_info": "https://www.ifly.com/airports/baltimore-washington-international-airport/wait-times",
    },
    "DCA": {
        "name": "Ronald Reagan Washington National Airport",
        "takeofftimer_api": "https://www.takeofftimer.com/api/tsa-wait-times?code=DCA",
        "takeofftimer_page": "https://www.takeofftimer.com/tsa-wait-times/DCA",
        "flightqueue": "https://flightqueue.com/ronald-reagan-washington-national-airport-security-wait-times",
        "checkpoint_info": "https://www.flyreagan.com/travel-information/security-information",
        "checkpoint_waits": "https://www.airporstinsights.com/dca-airport/wait-times/",
    },
    "IAD": {
        "name": "Washington Dulles International Airport",
        "takeofftimer_api": "https://www.takeofftimer.com/api/tsa-wait-times?code=IAD",
        "takeofftimer_page": "https://www.takeofftimer.com/tsa-wait-times/IAD",
        "flightqueue": "https://flightqueue.com/washington-dulles-international-airport-security-wait-times",
        "checkpoint_info": "https://www.flydulles.com/travel-information/security-information",
        "checkpoint_notes": "https://www.airporstinsights.com/iad-airport/wait-times/",
    },
}


def static_metadata() -> list[CheckpointMetadata]:
    rows: list[CheckpointMetadata] = []

    rows.extend(
        [
            CheckpointMetadata(
                airport_code="DCA",
                airport_name=AIRPORTS["DCA"]["name"],
                checkpoint="Terminal 1",
                gates="Gates A1-A9",
                services=("Security", "CLEAR"),
                status=None,
                hours="4:00 AM - 9:00 PM",
                source_name="FlyReagan",
                source_url=AIRPORTS["DCA"]["checkpoint_info"],
                notes="Serves Air Canada, Frontier, and Southwest.",
            ),
            CheckpointMetadata(
                airport_code="DCA",
                airport_name=AIRPORTS["DCA"]["name"],
                checkpoint="Terminal 2 North",
                gates="Closest to Gates B/C/D/E (American focus)",
                services=("Security", "TSA PreCheck", "CLEAR"),
                status=None,
                hours="4:00 AM - 11:00 PM",
                source_name="FlyReagan",
                source_url=AIRPORTS["DCA"]["checkpoint_info"],
            ),
            CheckpointMetadata(
                airport_code="DCA",
                airport_name=AIRPORTS["DCA"]["name"],
                checkpoint="Terminal 2 South",
                gates="Closest to Gates B/C/D/E",
                services=("Security", "TSA PreCheck", "CLEAR"),
                status=None,
                hours="4:00 AM - 9:00 PM",
                source_name="FlyReagan",
                source_url=AIRPORTS["DCA"]["checkpoint_info"],
                notes="Closest to Alaska, Delta, JetBlue, and United; also serves American.",
            ),
        ]
    )

    rows.extend(
        [
            CheckpointMetadata(
                airport_code="IAD",
                airport_name=AIRPORTS["IAD"]["name"],
                checkpoint="East Security Checkpoint",
                gates=None,
                services=("Security", "CLEAR"),
                status=None,
                hours="3:45 AM - 10:30 PM",
                source_name="FlyDulles",
                source_url=AIRPORTS["IAD"]["checkpoint_info"],
            ),
            CheckpointMetadata(
                airport_code="IAD",
                airport_name=AIRPORTS["IAD"]["name"],
                checkpoint="West Security Checkpoint",
                gates=None,
                services=("Security",),
                status=None,
                hours="4:45 AM - 9:00 PM",
                source_name="FlyDulles",
                source_url=AIRPORTS["IAD"]["checkpoint_info"],
            ),
            CheckpointMetadata(
                airport_code="IAD",
                airport_name=AIRPORTS["IAD"]["name"],
                checkpoint="TSA PreCheck Checkpoint",
                gates=None,
                services=("TSA PreCheck", "CLEAR"),
                status=None,
                hours="4:00 AM - 9:00 PM",
                source_name="FlyDulles",
                source_url=AIRPORTS["IAD"]["checkpoint_info"],
                notes="Official page also highlights limited West checkpoint PreCheck windows during peak periods.",
            ),
        ]
    )

    rows.extend(
        [
            CheckpointMetadata(
                airport_code="BWI",
                airport_name=AIRPORTS["BWI"]["name"],
                checkpoint="Checkpoint A",
                gates=None,
                services=("Security", "TSA PreCheck", "CLEAR"),
                status=None,
                hours="CLEAR lane: 4:00 AM - 9:00 AM",
                source_name="iFly",
                source_url=AIRPORTS["BWI"]["checkpoint_info"],
            ),
            CheckpointMetadata(
                airport_code="BWI",
                airport_name=AIRPORTS["BWI"]["name"],
                checkpoint="Checkpoint B",
                gates=None,
                services=("Security", "TSA PreCheck", "CLEAR"),
                status=None,
                hours="CLEAR lane: 4:00 AM - 9:00 PM; TSA PreCheck enrollment: 6:00 AM - 8:00 PM",
                source_name="iFly",
                source_url=AIRPORTS["BWI"]["checkpoint_info"],
            ),
            CheckpointMetadata(
                airport_code="BWI",
                airport_name=AIRPORTS["BWI"]["name"],
                checkpoint="Checkpoint C",
                gates=None,
                services=("Security", "TSA PreCheck", "CLEAR"),
                status=None,
                hours="CLEAR lane: 6:00 AM - 8:30 PM",
                source_name="iFly",
                source_url=AIRPORTS["BWI"]["checkpoint_info"],
            ),
            CheckpointMetadata(
                airport_code="BWI",
                airport_name=AIRPORTS["BWI"]["name"],
                checkpoint="Checkpoint D/E",
                gates=None,
                services=("Security", "TSA PreCheck", "CLEAR"),
                status=None,
                hours="CLEAR lane: 4:00 AM - 8:30 PM",
                source_name="iFly",
                source_url=AIRPORTS["BWI"]["checkpoint_info"],
            ),
        ]
    )

    rows.extend(
        [
            CheckpointMetadata(
                airport_code="BOS",
                airport_name=AIRPORTS["BOS"]["name"],
                checkpoint="Terminal A",
                gates="Terminal A checkpoint",
                services=("Security", "TSA PreCheck", "CLEAR"),
                status=None,
                hours=None,
                source_name="AirporstInsights",
                source_url=AIRPORTS["BOS"]["checkpoint_info"],
            ),
            CheckpointMetadata(
                airport_code="BOS",
                airport_name=AIRPORTS["BOS"]["name"],
                checkpoint="Terminal B",
                gates="Terminal B checkpoints",
                services=("Security", "TSA PreCheck", "CLEAR"),
                status=None,
                hours=None,
                source_name="AirporstInsights",
                source_url=AIRPORTS["BOS"]["checkpoint_info"],
            ),
            CheckpointMetadata(
                airport_code="BOS",
                airport_name=AIRPORTS["BOS"]["name"],
                checkpoint="Terminal C",
                gates="Terminal C checkpoints",
                services=("Security", "TSA PreCheck"),
                status=None,
                hours=None,
                source_name="AirporstInsights",
                source_url=AIRPORTS["BOS"]["checkpoint_info"],
            ),
            CheckpointMetadata(
                airport_code="BOS",
                airport_name=AIRPORTS["BOS"]["name"],
                checkpoint="Terminal E",
                gates="Terminal E checkpoints",
                services=("Security", "TSA PreCheck", "Global Entry"),
                status=None,
                hours=None,
                source_name="AirporstInsights",
                source_url=AIRPORTS["BOS"]["checkpoint_info"],
            ),
        ]
    )

    return rows

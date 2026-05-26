# Airport Wait Monitor

Aggregates posted TSA security wait times for **BWI**, **IAD**, **DCA**, and **BOS** from several public sources (TakeoffTimer, FlightQueue, iFly, FlyReagan, FlyDulles, AirporstInsights) and presents them via a CLI or a small local web UI.

## Features

- Fetches and normalizes wait observations from multiple sources per airport
- Aggregates low / average / high wait times per checkpoint and service (Security, TSA PreCheck, CLEAR, etc.)
- Tracks history in `data/wait_history.jsonl` for previous-average comparisons
- CLI table output and a lightweight HTTP server with a static web dashboard
- Static checkpoint metadata (hours, services, terminals) for each supported airport

## Requirements

- Python 3.10+
- See [`requirements.txt`](requirements.txt) (`beautifulsoup4`)

## Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage

### CLI

```powershell
# All four default airports
python -m wait_monitor

# A subset
python -m wait_monitor BWI DCA
```

### Web server

```powershell
python -m wait_monitor serve
# then open http://localhost:8000
```

Server flags (see `wait_monitor/server.py`) include `--host` and `--port`.

## Project layout

```
airport-wait-monitor/
├── data/                       # Persisted history (wait_history.jsonl)
├── tests/                      # Unit tests
├── wait_monitor/
│   ├── __main__.py             # `python -m wait_monitor` entry
│   ├── cli.py                  # CLI table renderer
│   ├── server.py               # HTTP server + JSON API
│   ├── service.py              # Aggregation pipeline
│   ├── sources.py              # Per-source fetchers / parsers
│   ├── config.py               # Airport + checkpoint metadata
│   ├── history.py              # JSONL history persistence
│   ├── models.py               # Dataclasses
│   ├── util.py
│   └── static/                 # Web UI (index.html, app.js, styles.css)
└── requirements.txt
```

## Tests

```powershell
python -m unittest discover -s tests
```

## Data sources

Wait times are scraped from public, third-party pages. This project is for personal / educational use; respect each source's terms of service and rate limits.

## License

MIT — see [LICENSE](LICENSE).

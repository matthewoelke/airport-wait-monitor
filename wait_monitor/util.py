from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from .config import USER_AGENT


def fetch_text(url: str, timeout_seconds: int = 20) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="replace")


def soup_from_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def find_json_ld_blocks(html: str) -> list[dict]:
    blocks: list[dict] = []
    soup = soup_from_html(html)
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            blocks.append(parsed)
    return blocks


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def normalize_minutes_text(value: str) -> tuple[float | None, str, bool]:
    text = collapse_spaces(value)
    lowered = text.lower()

    if not text:
        return None, "", False

    less_than_match = re.search(r"less than\s+(\d+)", lowered)
    if less_than_match:
        minutes = float(less_than_match.group(1))
        return minutes, f"<={int(minutes)} min", True

    under_match = re.search(r"under\s+(\d+)", lowered)
    if under_match:
        minutes = float(under_match.group(1))
        return minutes, f"<={int(minutes)} min", True

    exact_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|min)\b", lowered)
    if exact_match:
        minutes = float(exact_match.group(1))
        if minutes.is_integer():
            return minutes, f"{int(minutes)} min", False
        return minutes, f"{minutes:.1f} min", False

    return None, text, False


def safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

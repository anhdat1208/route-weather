from __future__ import annotations

import re
from typing import Any

_HOUSE_NUMBER_RE = re.compile(
    r"^\s*(?P<number>\d+(?:[/-]\d+)*)\s+(?P<rest>.+?)\s*$",
    re.UNICODE,
)


def parse_leading_house_number(query: str) -> tuple[str | None, str]:
    match = _HOUSE_NUMBER_RE.match(query.strip())
    if not match:
        return None, query.strip()
    return match.group("number"), match.group("rest").strip()


def build_address_label(hit: dict[str, Any]) -> str:
    housenumber = hit.get("housenumber")
    street = hit.get("street")
    name = hit.get("name")
    city = hit.get("city")
    district = hit.get("district") or hit.get("state")

    if isinstance(housenumber, str) and housenumber.strip() and isinstance(street, str) and street.strip():
        parts = [f"{housenumber.strip()} {street.strip()}"]
    elif isinstance(name, str) and name.strip():
        parts = [name.strip()]
    elif isinstance(street, str) and street.strip():
        parts = [street.strip()]
    else:
        parts = []

    for value in (district, city):
        if isinstance(value, str) and value.strip() and value.strip() not in parts:
            parts.append(value.strip())

    return ", ".join(parts) if parts else "Không xác định"


def result_has_house_number(label: str, house_number: str) -> bool:
    normalized = label.strip().lower()
    number = house_number.strip().lower()
    return normalized.startswith(f"{number} ") or normalized.startswith(f"{number},")


def is_ho_chi_minh_hit(hit: dict[str, Any]) -> bool:
    city = str(hit.get("city") or "")
    state = str(hit.get("state") or "")
    combined = f"{city} {state}".casefold()
    return "hồ chí minh" in combined or "ho chi minh" in combined


def prefer_local_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hcmc_hits = [hit for hit in hits if is_ho_chi_minh_hit(hit)]
    return hcmc_hits if hcmc_hits else hits


def build_timeline_label(hit: dict[str, Any]) -> str:
    """Short label for timeline cards: street/place + district when available."""
    name = hit.get("name")
    street = hit.get("street")
    district = hit.get("district") or hit.get("state")

    primary: str | None = None
    if isinstance(name, str) and name.strip():
        primary = name.strip()
    elif isinstance(street, str) and street.strip():
        primary = street.strip()

    if not primary:
        return build_address_label(hit)

    if isinstance(district, str) and district.strip() and district.strip() not in primary:
        return f"{primary}, {district.strip()}"
    return primary


def format_route_distance_label(distance_km: float) -> str:
    return f"Km {distance_km:.1f} trên lộ trình"


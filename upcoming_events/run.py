#!/usr/bin/env -S uv run
# /// script
# dependencies = ["requests"]
# ///

import json
import math
import re
import sys
from pathlib import Path

import requests


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def main() -> None:
    # cometogether.live removed its /ssr/event/upcoming API (observed 2026-07).
    # The site now embeds ALL events (Greece-wide) in the homepage's __NEXT_DATA__
    # SSR payload and filters by location client-side, so we scrape that payload
    # and do the proximity filtering ourselves.
    config = json.loads(Path("../config.json").read_text())
    location = config["location"]
    radius_km = config.get("radius_km", 50)

    lat_str, lng_str = location.split(",")
    origin_lat = float(lat_str.strip())
    origin_lng = float(lng_str.strip())

    resp = requests.get(
        "https://cometogether.live/",
        headers={
            "user-agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            ),
        },
    )
    resp.raise_for_status()

    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        resp.text,
        re.DOTALL,
    )
    if not match:
        print("__NEXT_DATA__ not found in homepage HTML", file=sys.stderr)
        sys.exit(1)

    data = json.loads(match.group(1))

    try:
        events = data["props"]["pageProps"]["data"]["events"]
    except (KeyError, TypeError):
        print("Unexpected __NEXT_DATA__ shape", file=sys.stderr)
        sys.exit(1)

    results = []
    for event in events:
        if event.get("cardType") != "EVENT":
            continue
        venues = event.get("newVenues")
        if not venues:
            continue
        coords = ((venues[0].get("venueLocation") or {}).get("location") or {}).get("coordinates")
        if not coords or len(coords) != 2:
            continue

        # GeoJSON order: [lng, lat]
        venue_lng, venue_lat = coords[0], coords[1]

        dist = haversine_km(origin_lat, origin_lng, venue_lat, venue_lng)
        if dist > radius_km:
            continue

        results.append(
            {
                "name": event["boxName"],
                "category": event["category"],
                "start": event.get("start"),
                "end": event.get("end"),
                "time_zone": event.get("timeZone"),
                "venues": event.get("venueNames", []),
                "url": f"https://cometogether.live/event/{event['boxId']}",
            }
        )

    json.dump({"events": results}, sys.stdout, ensure_ascii=False)


main()

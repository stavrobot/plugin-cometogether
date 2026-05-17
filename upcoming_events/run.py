#!/usr/bin/env -S uv run
# /// script
# dependencies = ["requests"]
# ///

import json
import sys

import requests


def main() -> None:
    params = json.load(sys.stdin)

    location = params.get("location", "40.6400629,22.9444191")
    latitude, longitude = location.split(",")

    response = requests.get(
        "https://cometogether.live/ssr/event/upcoming",
        params={"latitude": latitude, "longitude": longitude},
        headers={
            "accept": "application/json",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        },
    )
    response.raise_for_status()
    data = response.json()

    events = [
        {
            "name": event["boxName"],
            "category": event["category"],
            "start": event.get("start"),
            "end": event["end"],
            "time_zone": event["timeZone"],
            "venues": event["venueNames"],
            "image": event["image"],
            "url": f"https://cometogether.live/event/{event['boxId']}",
        }
        for event in data["events"]
    ]

    json.dump({"events": events}, sys.stdout)


main()

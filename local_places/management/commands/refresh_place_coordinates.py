"""MAPA task: recompute LocalPlace.latitude/longitude from Google Place
Details, since older data was saved from the viewport center instead of the
place's actual point location (see admin_places.js and CHANGES_ADMIN_ISSUES.md
for context — the mismatch was up to ~1.7km for a few places).

Usage:
    python manage.py refresh_place_coordinates --dry-run   # preview only
    python manage.py refresh_place_coordinates              # write changes

Places whose google_places_id is shared by more than one LocalPlace are
always skipped (updating them would collapse every place sharing that ID
onto the same point) and listed at the end for manual review.
"""

import math

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from local_places.models import LocalPlace

PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def haversine_meters(lat1, lon1, lat2, lon2):
    radius = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


class Command(BaseCommand):
    help = "Recompute place coordinates from Google Place Details (point location, not viewport)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would change without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # GOOGLE_MAPS_API_KEY is normally used from the browser (admin JS)
        # and may be restricted by HTTP referrer, which a server-side
        # request can't satisfy. Prefer a dedicated server key if one is
        # configured; fall back to the browser key for local/dev use.
        api_key = getattr(settings, "GOOGLE_MAPS_SERVER_API_KEY", "") or getattr(
            settings, "GOOGLE_MAPS_API_KEY", ""
        )
        if not api_key:
            self.stderr.write(self.style.ERROR(
                "No GOOGLE_MAPS_SERVER_API_KEY or GOOGLE_MAPS_API_KEY configured."
            ))
            return

        places = LocalPlace.objects.exclude(google_places_id__isnull=True).exclude(
            google_places_id=""
        )

        # Group by google_places_id to find ones shared by multiple places —
        # those get skipped entirely and reported for manual review.
        by_place_id = {}
        for place in places:
            by_place_id.setdefault(place.google_places_id, []).append(place)

        shared = {pid: plist for pid, plist in by_place_id.items() if len(plist) > 1}
        unique = {pid: plist[0] for pid, plist in by_place_id.items() if len(plist) == 1}

        updated, unchanged, failed = 0, 0, 0

        for place_id, place in unique.items():
            try:
                response = requests.get(
                    PLACE_DETAILS_URL,
                    params={"place_id": place_id, "fields": "geometry", "key": api_key},
                    timeout=10,
                )
                data = response.json()
            except requests.RequestException as exc:
                failed += 1
                self.stderr.write(self.style.ERROR(f"{place.name}: request failed ({exc})"))
                continue

            if data.get("status") != "OK":
                failed += 1
                self.stderr.write(
                    self.style.ERROR(f"{place.name}: Google returned {data.get('status')}")
                )
                continue

            location = data["result"]["geometry"]["location"]
            new_lat, new_lng = location["lat"], location["lng"]

            if place.latitude is None or place.longitude is None:
                distance = None
            else:
                distance = haversine_meters(place.latitude, place.longitude, new_lat, new_lng)

            if distance is not None and distance < 1:
                unchanged += 1
                continue

            moved_by = f"{distance:.0f}m" if distance is not None else "unknown distance (no prior coordinates)"
            self.stdout.write(
                f"{place.name}: ({place.latitude}, {place.longitude}) -> "
                f"({new_lat}, {new_lng}) [moved {moved_by}]"
            )

            if not dry_run:
                place.latitude = new_lat
                place.longitude = new_lng
                place.save(update_fields=["latitude", "longitude"])
            updated += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"{'Would update' if dry_run else 'Updated'}: {updated}   "
            f"Unchanged: {unchanged}   Failed: {failed}"
        ))

        if shared:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(
                f"Skipped {len(shared)} shared Place ID(s) — review manually, "
                "updating these would collapse all of them onto one point:"
            ))
            for place_id, place_list in shared.items():
                names = ", ".join(p.name for p in place_list)
                self.stdout.write(f"  {place_id}: {names}")

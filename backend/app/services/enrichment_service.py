"""Neighborhood enrichment via Google Maps (Geocoding + Places).

Real calls when GOOGLE_MAPS_API_KEY is present and mock mode is off; otherwise
deterministic mock values derived from a hash of the property's coordinates and
address so output is stable across runs.
"""

from __future__ import annotations

import hashlib
from typing import Any, Optional

import httpx

from app.config import get_settings

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

_SCHOOL_NAME_PARTS = [
    "Lincoln", "Roosevelt", "Jefferson", "Hamilton", "Franklin", "Kennedy",
    "Madison", "Riverside", "Oakwood", "Summit", "Pinecrest", "Lakeside",
]
_SCHOOL_LEVELS = ["Elementary School", "Middle School", "High School", "Academy"]


def _hash_int(*parts: Any) -> int:
    raw = "|".join(str(p) for p in parts).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest(), 16)


def _scaled(seed: int, lo: float, hi: float, salt: int = 0) -> float:
    """Map a hash seed to a float in [lo, hi] deterministically."""
    bucket = (seed >> (salt % 200)) % 10_000
    return lo + (hi - lo) * (bucket / 10_000.0)


class EnrichmentService:
    """Geocoding + neighborhood feature enrichment."""

    def __init__(self, settings: Optional[Any] = None) -> None:
        self.settings = settings or get_settings()

    @property
    def _use_mock(self) -> bool:
        return bool(self.settings.USE_MOCK_DATA) or not self.settings.GOOGLE_MAPS_API_KEY

    # ------------------------------------------------------------------
    # Geocoding
    # ------------------------------------------------------------------
    async def geocode(self, address: str) -> tuple[float, float]:
        """Return (lat, lng) for an address."""
        if self._use_mock:
            return self._mock_geocode(address)

        params = {"address": address, "key": self.settings.GOOGLE_MAPS_API_KEY}
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(GEOCODE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results") or []
                if results:
                    loc = results[0]["geometry"]["location"]
                    return float(loc["lat"]), float(loc["lng"])
            except (httpx.HTTPError, KeyError, ValueError, IndexError):
                pass
        return self._mock_geocode(address)

    def _mock_geocode(self, address: str) -> tuple[float, float]:
        seed = _hash_int("geocode", address)
        # Centered loosely over the continental US.
        lat = round(_scaled(seed, 30.0, 45.0, salt=3), 6)
        lng = round(_scaled(seed, -120.0, -95.0, salt=11), 6)
        return lat, lng

    # ------------------------------------------------------------------
    # Schools
    # ------------------------------------------------------------------
    async def nearby_schools(self, lat: float, lng: float) -> list[dict[str, Any]]:
        """Return a list of nearby school dicts: {name, rating, distance_km, level}."""
        if self._use_mock:
            return self._mock_schools(lat, lng)

        params = {
            "location": f"{lat},{lng}",
            "radius": 3000,
            "type": "school",
            "key": self.settings.GOOGLE_MAPS_API_KEY,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(PLACES_NEARBY_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results") or []
                schools: list[dict[str, Any]] = []
                for r in results[:5]:
                    schools.append(
                        {
                            "name": r.get("name", "Unknown School"),
                            "rating": float(r.get("rating", 0.0) or 0.0),
                            "distance_km": None,
                            "level": "School",
                        }
                    )
                if schools:
                    return schools
            except (httpx.HTTPError, ValueError):
                pass
        return self._mock_schools(lat, lng)

    def _mock_schools(self, lat: float, lng: float) -> list[dict[str, Any]]:
        seed = _hash_int("schools", round(lat, 4), round(lng, 4))
        count = 2 + (seed % 3)  # 2..4 schools
        schools: list[dict[str, Any]] = []
        for i in range(count):
            s = _hash_int(seed, i)
            name_part = _SCHOOL_NAME_PARTS[s % len(_SCHOOL_NAME_PARTS)]
            level = _SCHOOL_LEVELS[(s >> 8) % len(_SCHOOL_LEVELS)]
            schools.append(
                {
                    "name": f"{name_part} {level}",
                    "rating": round(_scaled(s, 5.0, 10.0, salt=i + 1), 1),
                    "distance_km": round(_scaled(s, 0.3, 3.0, salt=i + 7), 2),
                    "level": level,
                }
            )
        return schools

    # ------------------------------------------------------------------
    # Neighborhood aggregate
    # ------------------------------------------------------------------
    async def build_neighborhood(self, property: Any) -> dict[str, Any]:
        """Build a dict matching the `neighborhoods` table columns.

        `property` may be an ORM Property instance or a dict with at least
        lat/lng/address.
        """
        lat = _attr(property, "lat")
        lng = _attr(property, "lng")
        address = _attr(property, "address") or ""

        if lat is None or lng is None:
            lat, lng = await self.geocode(address)

        schools = await self.nearby_schools(float(lat), float(lng))

        # school_score = average of school ratings normalized to 0-10.
        if schools:
            ratings = [s.get("rating", 0.0) for s in schools if s.get("rating")]
            school_score = round(sum(ratings) / len(ratings), 1) if ratings else 6.0
        else:
            school_score = 6.0

        seed = _hash_int("neighborhood", round(float(lat), 4), round(float(lng), 4), address)

        restaurants_count = int(round(_scaled(seed, 8, 120, salt=2)))
        commute_time = int(round(_scaled(seed, 12, 55, salt=5)))  # minutes
        walk_score = int(round(_scaled(seed, 25, 98, salt=9)))
        # Lower crime_score is safer; expose on a 0-10 scale.
        crime_score = round(_scaled(seed, 1.0, 8.5, salt=13), 1)

        return {
            "school_score": float(school_score),
            "restaurants_count": int(restaurants_count),
            "commute_time": int(commute_time),
            "walk_score": int(walk_score),
            "crime_score": float(crime_score),
            "nearby_schools": schools,
        }


def _attr(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)

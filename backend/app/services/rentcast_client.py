"""RentCast listings client.

Real network call to https://api.rentcast.io/v1/listings when a key is
configured AND mock mode is disabled. Otherwise a deterministic generator
produces ~30 varied, realistic listings so the app runs with zero accounts.

Output dicts are normalized to match the `properties` table columns plus
`external_id`.
"""

from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta
from typing import Any, Optional

import httpx

from app.config import get_settings

RENTCAST_BASE_URL = "https://api.rentcast.io/v1"

# ---------------------------------------------------------------------------
# Mock data generation
# ---------------------------------------------------------------------------

# (city, state, zip, lat, lng) anchors for mock listings.
_CITY_ANCHORS: list[tuple[str, str, str, float, float]] = [
    ("Austin", "TX", "78701", 30.2672, -97.7431),
    ("Denver", "CO", "80202", 39.7392, -104.9903),
    ("Phoenix", "AZ", "85004", 33.4484, -112.0740),
    ("Austin", "TX", "78745", 30.2110, -97.7990),
    ("Denver", "CO", "80211", 39.7650, -105.0090),
    ("Phoenix", "AZ", "85016", 33.5020, -112.0320),
]

_STREET_NAMES = [
    "Maple", "Oak", "Cedar", "Pine", "Elm", "Sunset", "Lakeview", "Hillcrest",
    "Willow", "Birch", "Magnolia", "Aspen", "Juniper", "Brookside", "Highland",
]
_STREET_TYPES = ["St", "Ave", "Dr", "Ln", "Ct", "Blvd", "Way", "Pl"]

_PROPERTY_TYPES = [
    "Single Family",
    "Condo",
    "Townhouse",
    "Multi-Family",
]

_DESCRIPTION_TEMPLATES = [
    "Charming {beds}-bed, {baths}-bath {ptype} in the heart of {city}. "
    "Featuring {sqft} sqft of bright, open living space, a modern kitchen, "
    "and a private backyard. Built in {year}, move-in ready.",
    "Stunning {ptype} offering {beds} bedrooms and {baths} bathrooms across "
    "{sqft} sqft. Located in a sought-after {city} neighborhood with great "
    "schools, walkable amenities, and an easy commute downtown.",
    "Beautifully updated {beds}BR/{baths}BA {ptype} in {city}. {sqft} sqft "
    "of thoughtfully designed space, hardwood floors, energy-efficient "
    "windows, and a chef's kitchen. A rare find at this price.",
    "Spacious {ptype} with {beds} beds and {baths} baths, {sqft} sqft. "
    "Vaulted ceilings, abundant natural light, and a low-maintenance yard. "
    "Close to parks, dining, and transit in {city}.",
]


def _photo_urls(seed: int, count: int = 5) -> list[str]:
    """Deterministic placeholder photo URLs (picsum)."""
    return [f"https://picsum.photos/seed/prop{seed}-{i}/800/600" for i in range(count)]


def _generate_mock_listings() -> list[dict[str, Any]]:
    """Deterministically generate ~30 varied listings."""
    listings: list[dict[str, Any]] = []
    rng = random.Random(20240517)  # fixed seed -> deterministic
    count = 30
    today = date.today()

    for i in range(count):
        city, state, base_zip, base_lat, base_lng = _CITY_ANCHORS[i % len(_CITY_ANCHORS)]

        beds = rng.choice([2, 3, 3, 4, 4, 5])
        bathrooms = rng.choice([1.0, 1.5, 2.0, 2.0, 2.5, 3.0, 3.5])
        sqft = rng.randint(900, 4200)
        lot_size = rng.choice([None, rng.randint(3000, 12000)])
        year_built = rng.randint(1955, 2023)
        property_type = rng.choice(_PROPERTY_TYPES)

        # Price loosely correlated to sqft + beds with regional variance.
        price_per_sqft = rng.uniform(180, 520)
        price = round((sqft * price_per_sqft) / 1000) * 1000

        street_num = rng.randint(100, 9999)
        street = f"{rng.choice(_STREET_NAMES)} {rng.choice(_STREET_TYPES)}"
        address = f"{street_num} {street}"

        lat = round(base_lat + rng.uniform(-0.08, 0.08), 6)
        lng = round(base_lng + rng.uniform(-0.08, 0.08), 6)

        description = rng.choice(_DESCRIPTION_TEMPLATES).format(
            beds=beds,
            baths=(int(bathrooms) if float(bathrooms).is_integer() else bathrooms),
            ptype=property_type,
            sqft=sqft,
            city=city,
            year=year_built,
        )

        listed_date = today - timedelta(days=rng.randint(1, 120))

        external_id = "mock-" + hashlib.sha1(
            f"{address}|{city}|{state}|{i}".encode("utf-8")
        ).hexdigest()[:16]

        listings.append(
            {
                "external_id": external_id,
                "address": address,
                "city": city,
                "state": state,
                "zip": base_zip,
                "price": float(price),
                "beds": int(beds),
                "bathrooms": float(bathrooms),
                "sqft": int(sqft),
                "lot_size": (int(lot_size) if lot_size is not None else None),
                "year_built": int(year_built),
                "property_type": property_type,
                "lat": float(lat),
                "lng": float(lng),
                "description": description,
                "photos": _photo_urls(i),
                "status": "active",
                "listed_date": listed_date.isoformat(),
            }
        )

    return listings


# Computed once at import; deterministic.
MOCK_LISTINGS: list[dict[str, Any]] = _generate_mock_listings()


class RentCastClient:
    """Async client for RentCast listings with deterministic mock fallback."""

    def __init__(self, settings: Optional[Any] = None) -> None:
        self.settings = settings or get_settings()

    @property
    def _use_mock(self) -> bool:
        return bool(self.settings.USE_MOCK_DATA) or not self.settings.RENTCAST_API_KEY

    async def search_listings(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        beds: Optional[int] = None,
        baths: Optional[float] = None,
        min_sqft: Optional[int] = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return normalized listing dicts.

        Real network call when configured; otherwise filtered mock data.
        """
        if self._use_mock:
            return self._search_mock(
                city=city,
                state=state,
                min_price=min_price,
                max_price=max_price,
                beds=beds,
                baths=baths,
                min_sqft=min_sqft,
                limit=limit,
            )

        return await self._search_remote(
            city=city,
            state=state,
            min_price=min_price,
            max_price=max_price,
            beds=beds,
            baths=baths,
            min_sqft=min_sqft,
            limit=limit,
        )

    # ------------------------------------------------------------------
    # Mock path
    # ------------------------------------------------------------------
    def _search_mock(
        self,
        *,
        city: Optional[str],
        state: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
        beds: Optional[int],
        baths: Optional[float],
        min_sqft: Optional[int],
        limit: int,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for listing in MOCK_LISTINGS:
            if city and listing["city"].lower() != city.strip().lower():
                continue
            if state and listing["state"].lower() != state.strip().lower():
                continue
            if min_price is not None and listing["price"] < min_price:
                continue
            if max_price is not None and listing["price"] > max_price:
                continue
            if beds is not None and listing["beds"] < beds:
                continue
            if baths is not None and listing["bathrooms"] < baths:
                continue
            if min_sqft is not None and listing["sqft"] < min_sqft:
                continue
            results.append(dict(listing))
            if len(results) >= max(1, limit):
                break
        return results

    # ------------------------------------------------------------------
    # Remote path
    # ------------------------------------------------------------------
    async def _search_remote(
        self,
        *,
        city: Optional[str],
        state: Optional[str],
        min_price: Optional[float],
        max_price: Optional[float],
        beds: Optional[int],
        baths: Optional[float],
        min_sqft: Optional[int],
        limit: int,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "status": "Active",
            "limit": max(1, min(limit, 500)),
        }
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        if beds is not None:
            params["bedrooms"] = beds
        if baths is not None:
            params["bathrooms"] = baths

        headers = {"X-Api-Key": self.settings.RENTCAST_API_KEY, "Accept": "application/json"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(
                    f"{RENTCAST_BASE_URL}/listings",
                    params=params,
                    headers=headers,
                )
                resp.raise_for_status()
                payload = resp.json()
            except (httpx.HTTPError, ValueError):
                # Network/parse failure -> graceful mock fallback so the app
                # never hard-fails on a flaky upstream.
                return self._search_mock(
                    city=city,
                    state=state,
                    min_price=min_price,
                    max_price=max_price,
                    beds=beds,
                    baths=baths,
                    min_sqft=min_sqft,
                    limit=limit,
                )

        raw_items = payload if isinstance(payload, list) else payload.get("listings", payload.get("data", []))
        normalized = [self._normalize_remote(item) for item in raw_items if isinstance(item, dict)]

        # Apply price/sqft filters not always supported server-side.
        filtered: list[dict[str, Any]] = []
        for item in normalized:
            if min_price is not None and item["price"] is not None and item["price"] < min_price:
                continue
            if max_price is not None and item["price"] is not None and item["price"] > max_price:
                continue
            if min_sqft is not None and item["sqft"] is not None and item["sqft"] < min_sqft:
                continue
            filtered.append(item)
            if len(filtered) >= max(1, limit):
                break
        return filtered

    @staticmethod
    def _normalize_remote(item: dict[str, Any]) -> dict[str, Any]:
        """Map a RentCast listing object to our properties columns."""
        ext_id = (
            item.get("id")
            or item.get("listingId")
            or item.get("formattedAddress")
            or hashlib.sha1(str(item).encode("utf-8")).hexdigest()[:16]
        )

        photos = item.get("photos") or item.get("images") or []
        if isinstance(photos, dict):
            photos = list(photos.values())
        photos = [p for p in photos if isinstance(p, str)]

        listed_date = item.get("listedDate") or item.get("listDate")
        if isinstance(listed_date, str) and len(listed_date) >= 10:
            listed_date = listed_date[:10]
        else:
            listed_date = None

        return {
            "external_id": str(ext_id),
            "address": item.get("formattedAddress") or item.get("addressLine1") or "",
            "city": item.get("city") or "",
            "state": item.get("state") or "",
            "zip": str(item.get("zipCode") or item.get("zip") or ""),
            "price": _to_float(item.get("price") or item.get("listPrice")),
            "beds": _to_int(item.get("bedrooms") or item.get("beds")),
            "bathrooms": _to_float(item.get("bathrooms") or item.get("baths")),
            "sqft": _to_int(item.get("squareFootage") or item.get("sqft")),
            "lot_size": _to_int(item.get("lotSize")),
            "year_built": _to_int(item.get("yearBuilt")),
            "property_type": item.get("propertyType") or "Single Family",
            "lat": _to_float(item.get("latitude") or item.get("lat")),
            "lng": _to_float(item.get("longitude") or item.get("lng") or item.get("lon")),
            "description": item.get("description") or "",
            "photos": photos,
            "status": (item.get("status") or "active").lower(),
            "listed_date": listed_date,
        }


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None

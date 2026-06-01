"""AI service: embeddings, property analysis, and chat.

Uses OpenAI when OPENAI_API_KEY is configured and mock mode is off; otherwise
returns deterministic, plausible results computed from the property numbers.
No network calls are made in mock mode.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from typing import Any, Optional

from app.config import get_settings

EMBEDDING_DIM = 1536


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


class AIService:
    """Embeddings + LLM analysis + chat with deterministic mock fallbacks."""

    def __init__(self, settings: Optional[Any] = None) -> None:
        self.settings = settings or get_settings()

    @property
    def _use_mock(self) -> bool:
        return bool(self.settings.USE_MOCK_DATA) or not self.settings.OPENAI_API_KEY

    def _client(self):
        from openai import AsyncOpenAI

        return AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    async def embed(self, text: str) -> list[float]:
        """Return a 1536-dim embedding vector for `text`."""
        text = (text or "").strip()
        if self._use_mock:
            return self._mock_embed(text)

        try:
            client = self._client()
            resp = await client.embeddings.create(
                model=self.settings.OPENAI_EMBEDDING_MODEL,
                input=text or " ",
            )
            return list(resp.data[0].embedding)
        except Exception:
            return self._mock_embed(text)

    @staticmethod
    def _mock_embed(text: str) -> list[float]:
        """Deterministic pseudo-vector derived from a hash of the text.

        Produces a stable, L2-normalized 1536-float vector. Similar strings
        produce identical vectors and different strings differ, which is enough
        for the mock semantic ordering to be deterministic.
        """
        # Expand a SHA-256 digest into enough bytes via a counter, then unpack
        # into floats and normalize.
        floats: list[float] = []
        counter = 0
        seed = (text or " ").encode("utf-8")
        while len(floats) < EMBEDDING_DIM:
            digest = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
            # 32 bytes -> 8 float32 values
            for i in range(0, 32, 4):
                if len(floats) >= EMBEDDING_DIM:
                    break
                (val,) = struct.unpack(">i", digest[i : i + 4])
                floats.append(val / 2_147_483_648.0)  # -> roughly [-1, 1]
            counter += 1

        norm = math.sqrt(sum(f * f for f in floats)) or 1.0
        return [f / norm for f in floats]

    # ------------------------------------------------------------------
    # Property analysis
    # ------------------------------------------------------------------
    async def analyze_property(
        self,
        property: Any,
        neighborhood: Any = None,
        comparables: Optional[list[Any]] = None,
    ) -> dict[str, Any]:
        """Return a dict matching the `analyses` table columns."""
        comparables = comparables or []
        if self._use_mock:
            return self._mock_analysis(property, neighborhood, comparables)

        try:
            return await self._llm_analysis(property, neighborhood, comparables)
        except Exception:
            return self._mock_analysis(property, neighborhood, comparables)

    async def _llm_analysis(
        self,
        property: Any,
        neighborhood: Any,
        comparables: list[Any],
    ) -> dict[str, Any]:
        client = self._client()
        context = self._analysis_context(property, neighborhood, comparables)

        system = (
            "You are a real-estate investment analyst. Given a subject property, "
            "its neighborhood metrics, and comparable listings, produce a concise "
            "valuation analysis. Respond ONLY with strict JSON having keys: "
            "summary (string), pros (array of strings), cons (array of strings), "
            "investment_score (integer 0-100), risk_score (one of 'low','medium','high'), "
            "buyer_score (integer 0-100), price_evaluation (string), "
            "estimated_value (number)."
        )
        user = json.dumps(context)

        resp = await client.chat.completions.create(
            model=self.settings.OPENAI_CHAT_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        return self._coerce_analysis(data, property, comparables)

    @staticmethod
    def _analysis_context(
        property: Any, neighborhood: Any, comparables: list[Any]
    ) -> dict[str, Any]:
        def comp_view(c: Any) -> dict[str, Any]:
            return {
                "price": _num(_attr(c, "price")),
                "sqft": _attr(c, "sqft"),
                "beds": _attr(c, "beds"),
                "bathrooms": _attr(c, "bathrooms"),
            }

        return {
            "subject": {
                "address": _attr(property, "address"),
                "city": _attr(property, "city"),
                "state": _attr(property, "state"),
                "price": _num(_attr(property, "price")),
                "beds": _attr(property, "beds"),
                "bathrooms": _attr(property, "bathrooms"),
                "sqft": _attr(property, "sqft"),
                "year_built": _attr(property, "year_built"),
                "property_type": _attr(property, "property_type"),
                "description": _attr(property, "description"),
            },
            "neighborhood": {
                "school_score": _attr(neighborhood, "school_score"),
                "restaurants_count": _attr(neighborhood, "restaurants_count"),
                "commute_time": _attr(neighborhood, "commute_time"),
                "walk_score": _attr(neighborhood, "walk_score"),
                "crime_score": _attr(neighborhood, "crime_score"),
            },
            "comparables": [comp_view(c) for c in comparables],
        }

    def _coerce_analysis(
        self, data: dict[str, Any], property: Any, comparables: list[Any]
    ) -> dict[str, Any]:
        fallback = self._mock_analysis(property, None, comparables)
        risk = str(data.get("risk_score", fallback["risk_score"])).lower()
        if risk not in {"low", "medium", "high"}:
            risk = fallback["risk_score"]
        return {
            "summary": str(data.get("summary") or fallback["summary"]),
            "pros": _as_str_list(data.get("pros")) or fallback["pros"],
            "cons": _as_str_list(data.get("cons")) or fallback["cons"],
            "investment_score": _clamp_int(data.get("investment_score"), fallback["investment_score"]),
            "risk_score": risk,
            "buyer_score": _clamp_int(data.get("buyer_score"), fallback["buyer_score"]),
            "price_evaluation": str(data.get("price_evaluation") or fallback["price_evaluation"]),
            "estimated_value": _num(data.get("estimated_value")) or fallback["estimated_value"],
        }

    # ------------------------------------------------------------------
    # Mock analysis (computed from the numbers)
    # ------------------------------------------------------------------
    def _mock_analysis(
        self, property: Any, neighborhood: Any, comparables: list[Any]
    ) -> dict[str, Any]:
        price = _num(_attr(property, "price")) or 0.0
        sqft = _attr(property, "sqft") or 0
        beds = _attr(property, "beds") or 0
        baths = _attr(property, "bathrooms") or 0
        year_built = _attr(property, "year_built")
        city = _attr(property, "city") or "the area"
        ptype = _attr(property, "property_type") or "home"

        subject_ppsf = (price / sqft) if sqft else 0.0

        comp_ppsf_values = []
        comp_prices = []
        for c in comparables:
            cp = _num(_attr(c, "price"))
            cs = _attr(c, "sqft")
            if cp and cs:
                comp_ppsf_values.append(cp / cs)
            if cp:
                comp_prices.append(cp)

        avg_comp_ppsf = (
            sum(comp_ppsf_values) / len(comp_ppsf_values) if comp_ppsf_values else subject_ppsf
        )

        # Estimated value: blend subject sqft * avg comp ppsf with the list price.
        if sqft and avg_comp_ppsf:
            comp_based_value = sqft * avg_comp_ppsf
            estimated_value = round((comp_based_value + price) / 2.0, 0) if price else round(comp_based_value, 0)
        else:
            estimated_value = round(price, 0)

        # Over/under valuation vs comparables.
        if avg_comp_ppsf and subject_ppsf:
            delta_pct = (subject_ppsf - avg_comp_ppsf) / avg_comp_ppsf * 100.0
        else:
            delta_pct = 0.0

        if delta_pct <= -7:
            price_evaluation = (
                f"Priced ~{abs(delta_pct):.0f}% below comparable price-per-sqft - "
                f"appears undervalued for {city}."
            )
            price_factor = 1.0
        elif delta_pct >= 7:
            price_evaluation = (
                f"Priced ~{delta_pct:.0f}% above comparable price-per-sqft - "
                f"appears somewhat overvalued for {city}."
            )
            price_factor = 0.0
        else:
            price_evaluation = (
                f"Priced in line with comparables (within {abs(delta_pct):.0f}% of "
                f"neighborhood price-per-sqft) - fairly valued."
            )
            price_factor = 0.6

        school_score = _attr(neighborhood, "school_score")
        walk_score = _attr(neighborhood, "walk_score")
        crime_score = _attr(neighborhood, "crime_score")
        commute_time = _attr(neighborhood, "commute_time")

        # Investment score: weighted blend of valuation, schools, walkability, safety.
        school_factor = (school_score / 10.0) if isinstance(school_score, (int, float)) else 0.6
        walk_factor = (walk_score / 100.0) if isinstance(walk_score, (int, float)) else 0.6
        safety_factor = (
            (1.0 - (crime_score / 10.0)) if isinstance(crime_score, (int, float)) else 0.6
        )

        investment_raw = (
            0.40 * price_factor
            + 0.20 * school_factor
            + 0.20 * walk_factor
            + 0.20 * safety_factor
        )
        investment_score = _clamp_int(round(investment_raw * 100), 60)

        # Buyer score weights lifestyle (schools, walkability, safety, commute) more.
        commute_factor = (
            max(0.0, 1.0 - ((commute_time - 10) / 50.0))
            if isinstance(commute_time, (int, float))
            else 0.6
        )
        buyer_raw = (
            0.30 * school_factor
            + 0.25 * walk_factor
            + 0.25 * safety_factor
            + 0.20 * commute_factor
        )
        buyer_score = _clamp_int(round(buyer_raw * 100), 65)

        # Risk score from valuation delta + safety.
        risk_points = 0
        if delta_pct >= 7:
            risk_points += 1
        if isinstance(crime_score, (int, float)) and crime_score >= 6:
            risk_points += 1
        if year_built and year_built < 1975:
            risk_points += 1
        risk_score = "low" if risk_points == 0 else ("medium" if risk_points == 1 else "high")

        pros: list[str] = []
        cons: list[str] = []
        if price_factor >= 1.0:
            pros.append("Attractively priced relative to comparable sales")
        elif price_factor <= 0.0:
            cons.append("Priced above comparable price-per-sqft")
        if school_factor >= 0.75:
            pros.append("Strong school ratings nearby")
        elif school_factor < 0.5:
            cons.append("Below-average school ratings in the area")
        if walk_factor >= 0.7:
            pros.append("Highly walkable location")
        elif walk_factor < 0.4:
            cons.append("Car-dependent location with low walkability")
        if safety_factor >= 0.7:
            pros.append("Low crime relative to surrounding areas")
        elif safety_factor < 0.5:
            cons.append("Elevated crime metrics for the area")
        if year_built and year_built >= 2005:
            pros.append("Relatively newer construction")
        elif year_built and year_built < 1975:
            cons.append("Older construction may require updates/maintenance")
        if isinstance(commute_time, (int, float)) and commute_time <= 25:
            pros.append("Short typical commute to the urban core")
        elif isinstance(commute_time, (int, float)) and commute_time >= 45:
            cons.append("Longer commute times")

        if not pros:
            pros.append("Solid fundamentals for the local market")
        if not cons:
            cons.append("Limited downside identified from available metrics")

        summary = (
            f"This {beds}-bed, {baths}-bath {ptype} in {city} is listed at "
            f"${price:,.0f} (~${subject_ppsf:,.0f}/sqft). Based on {len(comparables)} "
            f"comparable listing(s), the estimated market value is "
            f"~${estimated_value:,.0f}. {price_evaluation} Overall investment score "
            f"of {investment_score}/100 with {risk_score} risk."
        )

        return {
            "summary": summary,
            "pros": pros,
            "cons": cons,
            "investment_score": investment_score,
            "risk_score": risk_score,
            "buyer_score": buyer_score,
            "price_evaluation": price_evaluation,
            "estimated_value": float(estimated_value),
        }

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------
    async def chat(self, query: str, retrieved_properties: Optional[list[Any]] = None) -> str:
        """Return a natural-language answer grounded in retrieved properties."""
        retrieved_properties = retrieved_properties or []
        if self._use_mock:
            return self._mock_chat(query, retrieved_properties)

        try:
            client = self._client()
            context_lines = []
            for p in retrieved_properties[:6]:
                context_lines.append(
                    f"- {_attr(p, 'address')}, {_attr(p, 'city')} {_attr(p, 'state')}: "
                    f"${_num(_attr(p, 'price')) or 0:,.0f}, {_attr(p, 'beds')}bd/"
                    f"{_attr(p, 'bathrooms')}ba, {_attr(p, 'sqft')} sqft."
                )
            context = "\n".join(context_lines) or "No matching properties were found."
            system = (
                "You are a helpful real-estate assistant. Answer the user's question "
                "using ONLY the provided property listings as ground truth. Be concise, "
                "specific, and reference relevant listings. If nothing matches, say so."
            )
            resp = await client.chat.completions.create(
                model=self.settings.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Question: {query}\n\nListings:\n{context}"},
                ],
                temperature=0.5,
            )
            return (resp.choices[0].message.content or "").strip() or self._mock_chat(
                query, retrieved_properties
            )
        except Exception:
            return self._mock_chat(query, retrieved_properties)

    @staticmethod
    def _mock_chat(query: str, retrieved_properties: list[Any]) -> str:
        if not retrieved_properties:
            return (
                f"I couldn't find any properties matching \"{query}\" in the current "
                "dataset. Try broadening your criteria (different city, price range, "
                "or number of bedrooms)."
            )

        n = len(retrieved_properties)
        prices = [
            _num(_attr(p, "price")) for p in retrieved_properties if _num(_attr(p, "price"))
        ]
        avg_price = sum(prices) / len(prices) if prices else 0.0

        top = retrieved_properties[0]
        lines = [
            f"Based on your question \"{query}\", I found {n} relevant "
            f"propert{'y' if n == 1 else 'ies'} with an average price of "
            f"${avg_price:,.0f}.",
            "",
            "Top match:",
            f"- {_attr(top, 'address')}, {_attr(top, 'city')} {_attr(top, 'state')} - "
            f"${_num(_attr(top, 'price')) or 0:,.0f}, {_attr(top, 'beds')} bed / "
            f"{_attr(top, 'bathrooms')} bath, {_attr(top, 'sqft')} sqft.",
        ]
        if n > 1:
            lines.append("")
            lines.append("Other options to consider:")
            for p in retrieved_properties[1:4]:
                lines.append(
                    f"- {_attr(p, 'address')}, {_attr(p, 'city')} - "
                    f"${_num(_attr(p, 'price')) or 0:,.0f} "
                    f"({_attr(p, 'beds')}bd/{_attr(p, 'bathrooms')}ba)."
                )
        lines.append("")
        lines.append(
            "Let me know if you'd like a deeper analysis on any of these, or want to "
            "refine by neighborhood, schools, or budget."
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Small coercion helpers
# ---------------------------------------------------------------------------
def _num(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp_int(value: Any, default: int) -> int:
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(0, min(100, n))


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v) for v in value if v is not None]

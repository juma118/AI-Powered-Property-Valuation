"""Small cross-service helpers shared by the AI and enrichment services."""

from __future__ import annotations

from typing import Any


def get_attr(obj: Any, name: str, default: Any = None) -> Any:
    """Read `name` from a dict or an ORM/object instance, with a default."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

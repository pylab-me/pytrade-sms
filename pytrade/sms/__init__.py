"""SMS package public facade."""
from __future__ import annotations

from .public_api import query, SMS
from .version import __VERSION__


__all__ = ["SMS", "query", "__VERSION__"]


def __getattr__(name: str):
    blocked_names = {"SMSMetadataEngine", "SecurityRecord", "AssetType"}
    if name in blocked_names:
        raise AttributeError(
            f"{name} is internal. Use `query(...)` or `SMS().query(...)` instead."
        )
    raise AttributeError(name)

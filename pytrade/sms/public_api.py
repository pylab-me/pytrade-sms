"""Public SMS facade."""
from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from pytrade.sms.engine import serialize_records, SMSMetadataEngine


_ENGINE: Optional[SMSMetadataEngine] = None
_ENGINE_LOCK = RLock()
_PACKAGE_DIR = Path(__file__).resolve().parent
_FULL_FILE = _PACKAGE_DIR / "finance_data.bin"
_INDEX_FILE = _PACKAGE_DIR / "finance_data.index.bin"
_MANIFEST_FILE = _PACKAGE_DIR / "finance_data.manifest.json"


def resolve_engine() -> SMSMetadataEngine:
    """延迟加载默认 engine。"""
    global _ENGINE
    with _ENGINE_LOCK:
        if _ENGINE is not None:
            return _ENGINE

        engine = SMSMetadataEngine()
        engine.load_dual_files(
            _FULL_FILE,
            _INDEX_FILE,
            _MANIFEST_FILE if _MANIFEST_FILE.exists() else None,
        )
        _ENGINE = engine
        return _ENGINE


def query(
    text: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """公开查询接口。

    :param text: optional query text.
    :param filters: optional field filters.
    :param limit: max result size.

    :return: serialized display records.
    """
    engine = resolve_engine()
    return serialize_records(engine.query(text=text, filters=filters, limit=limit))


class SMS:
    def query(
        self,
        text: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """公开查询接口。

        :param text: optional query text.
        :param filters: optional field filters.
        :param limit: max result size.

        :return: serialized display records.
        """
        return query(text=text, filters=filters, limit=limit)

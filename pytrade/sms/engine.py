"""SMS engine facade built on top of `sms_runtime`.

Python 侧仅保留 domain object、query 风格与评分逻辑；
full payload、索引、过滤与快照读写全部下沉到 `sms_runtime`。
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


try:
    import pytrade.sms.sms_runtime as sms_runtime
except ImportError:
    try:
        import sms_runtime
    except ImportError:
        sms_runtime = None


class AssetType(Enum):
    asset_weights = {"stock": 1.0, "index": 0.8, "etf": 0.6, "bond": 0.4}

    STOCK = "stock"  # 直接交易; 股
    ETF = "etf"  # 直接交易; ETF
    INDEX = "index"  # 行情参考，不可直接交易。
    BOND = "bond"  # 国债 / 企债


@dataclass(frozen=True)
class SecurityRecord:
    """证券元数据实体模型.

    example: ```
        {
            # --- 1. 核心索引区 (用于 suggest 和 find 接口) ---
            "code": "600519.SH",                # 唯一标识，严格遵守 [代码].[市场]
            "name": "贵州茅台",                 # 官方中文简称
            "pinyin": "guizhoumaotai|gzmt",      # 复合拼音：全拼|首字母简拼 (关键优化)
            "asset_type": "stock",               # 资产类型枚举: stock, etf, index, bond, option, future
            "market": "SH",                      # 市场枚举: SH, SZ, BJ, HK, NQ, NY, CSI, CNI

            # --- 2. 业务标签区 (放入 categories，利用动态倒排索引 $O(1)$ 过滤) ---
            "categories": {
                "sw_l1": "食品饮料",             # 申万一级
                "sw_l2": "饮料制造",             # 申万二级
                "sw_l3": "白酒III",              # 申万三级
                "wind_l1": "日常消费",           # Wind一级
                "zjh": "C31.酒、饮料和精制茶制造业", # 证监会行业
                "region": "贵州.遵义",           # 地区路径
                "listing_status": "L",           # 上市状态: L(上市), DE(退市), PA(暂停)
                "exchange": "SSE",               # 具体交易所标识: SSE, SZSE, BSE, HKEX
                "board": "Main",                 # 板块: Main(主板), Star(科创), ChiNext(创业)
                "currency": "CNY",               # 交易币种: CNY, HKD, USD
                "tags": "ST|融资融券|沪股通|MSCI中国", # 业务标签集合，支持 .split('|') 后过滤
                "index_constituents": "000300.CSI|000001.SH" # 所属重要指数成份：「指数 (Index)：IDX」；「行业板块 (Block)：BI」；「概念板块 (Block)：CI」；「地域板块 (Block)：RI」
                "held_by_funds": "001903.OF|000001.OF|510300.ETF"
            },

            # --- 3. 扩展属性区 (放入 attributes，存储数值或非搜索类描述数据) ---
            "attributes": {
                "mapping": ["..."]  # 存放不同数据源的映射关系。（如 600519 在 Wind 是 .SH，在 Bloomberg 是 CH，在路透是 .SS）。
                # 上市信息
                "list_date": "2001-08-27",       # 上市日期 (ISO 8601)
                "issue_price": 31.39,            # 发行价

                # 股本结构 (数值型，不参与文本搜索)
                "share_capital": {
                    "total_shares": 125619.78,   # 总股本 (万股)
                    "float_shares": 125619.78,   # 流通股本 (万股)
                    "free_float_shares": 60520.1,# 自由流通股本 (万股)
                    "last_update": "2025-12-31"  # 股本变动日期
                },

                # 公司基本画像
                "company_info": {
                    "full_name": "贵州茅台酒股份有限公司",
                    "en_name": "Kweichow Moutai Co., Ltd.",
                    "legal_repr": "丁雄军",
                    "website": "www.moutaichina.com"
                },

                # 债券/ETF 特有属性 (泛化支持)
                "specific": {
                    "is_convertible": False,     # 是否可转债
                    "underlying_index": "",      # ETF跟踪指数
                    "management_fee": 0.005      # 管理费率
                },

                "fund_holdings": [{
                    "fund_code": "001903.OF",
                    "fund_name": "光大欣鑫混合A",
                    "ratio": 0.095,          // 持有比例 9.5%
                    "hold_shares": 120.5,    // 持股数(万股)
                    "report_date": "2025-12-31"
                }, ]
            }
        } ```
    """

    code: str  # UID: 代码.市场 (600519.SH)
    name: str  # 中文简称
    pinyin: str  # 拼音全拼
    asset_type: str  # stock, etf, index, bond
    market: str  # SH, SZ, HK, NQ...
    region: str  # 地区路径: 广东.深圳
    categories: Dict[str, str] = field(default_factory=dict)  # 多维分类: {"sw": "食品饮料.白酒"}
    attributes: Dict[str, Any] = field(default_factory=dict)  # 扩展属性

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "SecurityRecord":
        """从跨边界 payload 重建 Python 侧对象.

        :param payload: cross-boundary payload.

        :return: SecurityRecord instance.
        """
        return cls(
            code=str(payload.get("code", "")),
            name=str(payload.get("name", "")),
            pinyin=str(payload.get("pinyin", "")),
            asset_type=str(payload.get("asset_type", "")),
            market=str(payload.get("market", "")),
            region=str(payload.get("region", "")),
            categories=dict(payload.get("categories", {}) or {}),
            attributes=dict(payload.get("attributes", {}) or {}),
        )

    def to_payload(self) -> Dict[str, Any]:
        """导出跨边界 payload.

        :return: payload dict.
        """
        return asdict(self)


def serialize_record(record: SecurityRecord) -> Dict[str, Any]:
    """将内部 SecurityRecord 转为可展示字典。"""
    payload = record.to_payload()
    payload["display_name"] = payload["name"]
    payload["display_code"] = payload["code"]
    return payload


to_display_payload = serialize_record


def serialize_records(records: List[SecurityRecord]) -> List[Dict[str, Any]]:
    """批量序列化记录。"""
    return [serialize_record(record) for record in records]


to_display_payloads = serialize_records


class PersistenceMixin:
    """快照文件读写编排。"""

    _rust_core: Any

    @staticmethod
    def _derive_index_file_path(full_file_path: str | Path) -> Path:
        full_path = Path(full_file_path)
        suffix = "".join(full_path.suffixes)
        if suffix:
            base = full_path.name[: -len(suffix)]
        else:
            base = full_path.name
        return full_path.with_name(f"{base}.index.bin")

    @staticmethod
    def _derive_manifest_file_path(full_file_path: str | Path) -> Path:
        full_path = Path(full_file_path)
        suffix = "".join(full_path.suffixes)
        if suffix:
            base = full_path.name[: -len(suffix)]
        else:
            base = full_path.name
        return full_path.with_name(f"{base}.manifest.json")

    def save_to_file(self, file_path: str | Path, records: List[SecurityRecord]):
        """兼容旧接口：保存 full/index/manifest 三件套。"""
        full_path = Path(file_path)
        self.save_dual_files(
            full_path,
            self._derive_index_file_path(full_path),
            self._derive_manifest_file_path(full_path),
            records,
        )

    def save_dual_files(
        self,
        full_file_path: str | Path,
        index_file_path: str | Path,
        manifest_file_path: str | Path,
        records: List[SecurityRecord],
    ):
        core = sms_runtime.MetadataCore()
        for record in records:
            core.add_record_payload(record.to_payload())
        core.build()
        core.save_snapshot(
            str(full_file_path),
            str(index_file_path),
            str(manifest_file_path),
        )
        self._rust_core = core
        self._rebuild_local_views(records)

    def load_from_file(self, file_path: str | Path):
        """兼容旧接口：从 full 文件名推导 companion index/manifest。"""
        full_path = Path(file_path)
        self.load_dual_files(
            full_path,
            self._derive_index_file_path(full_path),
            self._derive_manifest_file_path(full_path),
        )

    def load_dual_files(
        self,
        full_file_path: str | Path,
        index_file_path: str | Path,
        manifest_file_path: Optional[str | Path] = None,
    ):
        full_path = Path(full_file_path)
        index_path = Path(index_file_path)
        if not full_path.exists():
            raise FileNotFoundError(full_path)
        if not index_path.exists():
            raise FileNotFoundError(index_path)

        core = sms_runtime.MetadataCore()
        core.load_snapshot(str(full_path), str(index_path))
        self._rust_core = core

        codes = list(core.filter({}))
        records = self._get_records_by_codes(codes) if codes else []

        if manifest_file_path:
            manifest_path = Path(manifest_file_path)
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                expected_count = int(manifest.get("record_count", len(records)))
                if expected_count != len(records):
                    raise ValueError("Manifest record_count mismatch")

        self._rebuild_local_views(records)


class SMSMetadataEngine(PersistenceMixin):
    """Python query facade backed by `sms_runtime.MetadataCore`."""

    def __init__(self, bin_file_path: Optional[str] = None, *args, **kwargs):
        if sms_runtime is None:
            raise ImportError("sms_runtime is required")
        self._rust_core = sms_runtime.MetadataCore()
        self._records_list: List[SecurityRecord] = []
        self._data: Dict[str, SecurityRecord] = {}
        self._search_cache: List[Tuple[Dict[str, str], int]] = []

        if bin_file_path:
            self.load_from_file(bin_file_path)

    def _rebuild_local_views(self, records: List[SecurityRecord]):
        """基于 Rust full payload 重建 Python query 所需缓存。"""
        self._records_list = records
        self._data = {record.code: record for record in records}
        self._search_cache = []

        for idx, record in enumerate(records):
            cat_str = " ".join(str(value) for value in record.categories.values())
            attr_values: List[str] = []
            for value in record.attributes.values():
                if isinstance(value, (str, int, float)):
                    attr_values.append(str(value))
            blob = {
                "code": record.code.upper(),
                "name": record.name.upper(),
                "pinyin": record.pinyin.upper(),
                "tags": (cat_str + " " + " ".join(attr_values)).upper(),
            }
            self._search_cache.append((blob, idx))

    def _get_records_by_codes(self, codes: List[str]) -> List[SecurityRecord]:
        """按 code 批量取回完整记录。"""
        payloads = self._rust_core.get_many(list(codes))
        return [SecurityRecord.from_payload(dict(payload)) for payload in payloads]

    def query(
        self,
        text: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
    ) -> List[SecurityRecord]:
        """全能检索入口：Rust 召回 + Python 评分。"""
        if filters and len(filters) == 1 and "code" in filters:
            value = filters["code"]
            if isinstance(value, str) and value in self._data:
                return [self._data[value]]

        candidate_codes: Optional[set[str]] = None
        if filters:
            candidate_codes = set(self._rust_core.filter(filters))
            if not candidate_codes:
                return []

        if not text or not text.strip():
            results = []
            for record in self._records_list:
                if candidate_codes is not None and record.code not in candidate_codes:
                    continue
                results.append(record)
                if limit > 0 and len(results) >= limit:
                    break
            return results

        clean_query = text.strip().upper()
        scored_results: List[Tuple[float, SecurityRecord]] = []

        for blob, idx in self._search_cache:
            record = self._records_list[idx]
            if candidate_codes is not None and record.code not in candidate_codes:
                continue

            score = 0.0
            b_code = blob["code"]
            b_name = blob["name"]

            if clean_query == b_code:
                score += 100.0
            elif b_code.startswith(clean_query):
                score += 50.0
            elif clean_query in b_code:
                score += 10.0

            if clean_query == b_name:
                score += 80.0
            elif clean_query in b_name:
                score += 40.0

            if clean_query in blob["pinyin"]:
                score += 20.0
            if clean_query in blob["tags"]:
                score += 5.0

            if score <= 0:
                continue

            asset_weight = AssetType.asset_weights.value.get(record.asset_type, 0.5)
            score *= asset_weight

            total_shares = record.attributes.get("share_capital", {}).get("total_shares", 0)
            if total_shares and total_shares > 0:
                score += math.log10(total_shares) * 2

            scored_results.append((score, record))

        scored_results.sort(key=lambda item: item[0], reverse=True)
        final = [item[1] for item in scored_results]
        return final[:limit] if limit > 0 else final

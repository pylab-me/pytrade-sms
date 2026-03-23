**SMS** 是一套专为量化交易、资产管理系统及行情中心设计的**证券元数据标准协议**。

在金融业务中，证券元数据（如代码、简称、行业分类、股本变动）具有“准静态、高频检索、多维过滤”的特点。本项目定义的 `SecurityRecord` 实体模型，旨在解决跨市场（A股、港股、美股等）、跨数据源（Wind, Bloomberg, Reuters）的元数据统一存储与极速检索问题。

## 🚀 核心架构设计

系统采用**三层数据隔离架构**，兼顾检索性能与扩展性：

1.  **核心索引区 (Core Index)**：
      * **$O(1)$ 精确匹配**：通过 `code` 全局唯一标识。
      * **极速搜索**：内置 `pinyin` 复合索引（全拼|首字母），完美支持终端拼音模糊搜索。
2.  **业务标签区 (Business Categories)**：
      * **动态倒排索引**：针对行业分类（申万、证监会）、上市状态、成份股等字段设计，支持复杂的组合过滤。
      * **多维分层**：支持 L1/L2/L3 级行业透视及地域、板块过滤。
3.  **扩展属性区 (Extended Attributes)**：
      * **泛化存储**：存放股本结构、公司画像、特定资产（如 ETF 跟踪指数、债券费率）等非搜索类数值型数据。
      * **多源映射 (Mapping)**：内置不同金融数据终端的代码转换逻辑。

-----

## 🛠 数据实体定义 (Python `@dataclass`)

系统核心采用 Python 高性能 `dataclass` 定义，支持严格的类型校验与不可变性（Frozen）。

```python
@dataclass(frozen=True)
class SecurityRecord:
    """证券元数据实体模型"""
    
    # [核心索引] 
    code: str            # 600519.SH
    name: str            # 贵州茅台
    pinyin: str          # guizhoumaotai|gzmt
    asset_type: str      # stock, etf, index, bond...
    market: str           # SH, SZ, HK, NY...

    # [业务标签] - 建议存入倒排索引数据库（如 Elasticsearch / Redis Stack）
    categories: dict = {
        "sw_l1": "食品饮料",
        "listing_status": "L",
        "tags": "ST|融资融券|沪股通",
        "index_constituents": "000300.CSI|000001.SH"
    }

    # [扩展属性] - 存储于 Document Store 或列式数据库
    attributes: dict = {
        "share_capital": {"total_shares": 125619.78},
        "mapping": ["Bloomberg: CH", "Reuters: .SS"],
        "specific": {"is_convertible": False}
    }
```

-----

## 使用示例

```
filters: dict[str, Any] = {"market": markets, "asset_type": "stock", }
if exclude_st:
    filters["tags__not"] = "ST"

meta_data = sms_engine.query(filters=filters, limit=-1)

data: dict[str, list[Any]] = {
    "market": [obj.market for obj in meta_data],
    "symbol": [obj.code[:-3] for obj in meta_data],
}
```

-----

## ⚖️ 开源协议

本项目遵循 [Apache-2.0 License](https://www.google.com/search?q=LICENSE) 开源协议。

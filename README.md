# pytrade-sms

### 证券资产管理元数据存储与检索标准协议

> **核心定位**：`pytrade-sms` 是一套专为**证券资产管理**设计的元数据标准化协议。它不仅是金融数据建模的基石，更是构建高性能**量化交易系统**、**行情中心**以及**极速证券搜索服务**的核心组件。

---

## 为什么选择 pytrade-sms？

在处理全球证券数据时，开发者常面临代码不统一、行业分类混乱、检索性能低下等痛点。`pytrade-sms` 通过标准化的实体模型，为你解决以下核心问题：

* **全场景覆盖**：从股票（Stock）、ETF、指数（Index）到债券（Bond）与期货（Future），一套协议打通全资产类别。
* **极速搜索能力**：内置针对金融终端优化的**复合拼音索引**设计，支持“边打边出”的毫秒级 Suggest 接口。
* **多维标签架构**：利用**动态倒排索引**思想，轻松实现申万行业、成分股、地域板块及业务标签（如 ST、融资融券）的复杂交集过滤。
* **跨平台兼容性**：预置 `mapping` 机制，无缝对接 Wind、Bloomberg、Reuters 等主流金融终端数据标识。

## 核心架构设计

系统采用**三层数据隔离架构**，兼顾检索性能与扩展性：

1. **核心索引区 (Core Index)**：
    * **$O(1)$ 精确匹配**：通过 `code` 全局唯一标识。
    * **极速搜索**：内置 `pinyin` 复合索引（全拼|首字母），完美支持终端拼音模糊搜索。
2. **业务标签区 (Business Categories)**：
    * **动态倒排索引**：针对行业分类（申万、证监会）、上市状态、成份股等字段设计，支持复杂的组合过滤。
    * **多维分层**：支持 L1/L2/L3 级行业透视及地域、板块过滤。
3. **扩展属性区 (Extended Attributes)**：
    * **泛化存储**：存放股本结构、公司画像、特定资产（如 ETF 跟踪指数、债券费率）等非搜索类数值型数据。
    * **多源映射 (Mapping)**：内置不同金融数据终端的代码转换逻辑。

-----

## 安装方法

> 数据月更。可自行改动 [Query 函数](https://github.com/pylab-me/pytrade-sms/blob/main/pytrade/sms/engine.py#L287) 做查询重排。
>
> 每日更新：[Tien-Guan](https://github.com/pylab-me/Tien-Guan)

### Install from [Pypi](https://pypi.org/project/pytrade-sms/)

```
pip install -U pytrade-sms
```

## 使用示例

```
from pytrade.sms.public_api import PrivateSMS as SMSMetadataEngine
sms_engine = SMSMetadataEngine()

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

## 数据实体定义 (Python `@dataclass`)

系统核心采用 Python 高性能 `dataclass`
定义，支持严格的类型校验与不可变性（Frozen）。具体的定义见：[engine.py#L35](https://github.com/pylab-me/pytrade-sms/blob/main/pytrade/sms/engine.py#L35)

```python
@dataclass(frozen=True)
class SecurityRecord:
    """证券元数据实体模型"""

    # [核心索引] 
    code: str  # 600519.SH
    name: str  # 贵州茅台
    pinyin: str  # guizhoumaotai|gzmt
    asset_type: str  # stock, etf, index, bond...
    market: str  # SH, SZ, HK, NY...

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

## ⚖️ 开源协议

本项目遵循 [Apache-2.0 License](https://www.google.com/search?q=LICENSE) 开源协议。

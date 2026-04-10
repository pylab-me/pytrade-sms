# pytrade-sms

Rust-backed securities metadata search facade.

This public repository owns the final Python package contract and publishes wheels.
The native runtime is built from the private source repository and repacked into the final public wheel.

Stable public contract:
- `from pytrade.sms import query`
- `from pytrade.sms import SMS`
- `from pytrade.sms.engine import SMSMetadataEngine`

Internal-only API is not part of the compatibility contract:
- `private_api.py`
- `find`-style internal helpers
- private repository source layout

## Installation

Install from the latest GitHub release or Pypi:

```bash
pip install -U pytrade-sms
```

Replace the wheel file name with the platform-specific asset for Linux or macOS.

## Data Files

Wheel assets do not bundle:
- `finance_data.bin`
- `finance_data.index.bin`
- `finance_data.manifest.json`

Place these files under `pytrade/sms/` beside the installed package, or prepare your runtime environment so `SMSMetadataEngine` can load them from the expected package directory.

## Usage

```python
from pytrade.sms import SMS, query

rows = query(text="茅台", filters={"market": "SH"}, limit=10)
print(rows[:2])

engine = SMS()
rows = engine.query(filters={"asset_type": "stock"}, limit=20)
print(len(rows))
```

Advanced users may work directly with the public engine facade:

```python
from pytrade.sms.engine import SMSMetadataEngine

engine = SMSMetadataEngine("finance_data.bin")
rows = engine.query(text="AAPL", limit=5)
print(rows)
```

## Tests

```bash
python -m unittest discover tests
```

## Notes

- Query ranking logic lives in `pytrade/sms/engine.py`.
- Native extension details are intentionally hidden behind the public facade.
- This repository does not publish private Rust source code.

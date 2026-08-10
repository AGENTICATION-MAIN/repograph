# Contributing to Repograph

## Development Setup

```bash
git clone https://github.com/AGENTICATION-MAIN/repograph.git
cd repograph
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## Guidelines
- All parsers must be safe against malformed input and must not execute code.
- Every edge added to the graph must include an `EdgeEvidence` record with source file and method.
- Risk scores must remain 100% deterministic and reproducible.

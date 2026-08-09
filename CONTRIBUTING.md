# Contributing to Pactum

We welcome contributions from systems engineers, distributed systems researchers, and game theorists!

## Quick Setup

```bash
git clone https://github.com/AGENTICATION-MAIN/pactum-kernel.git
cd pactum-kernel
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## Guidelines
- **Sub-Millisecond Budget**: The Nash Bargaining Solver must maintain a P99 execution latency $<1\text{ ms}$.
- **Strict Pareto Efficiency**: All negotiation algorithms must mathematically preserve the Pareto optimality invariant.
- **Zero Currency**: Do not introduce virtual tokens or monetary exchange layers into the core barter engine.

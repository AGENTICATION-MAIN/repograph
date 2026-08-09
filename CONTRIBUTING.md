# Contributing to AegisKernel

Thank you for contributing to AegisKernel! We welcome contributions from engineers, researchers, and security practitioners.

## Development Setup

1. Clone repository:
   ```bash
   git clone https://github.com/AGENTICATION-MAIN/aegis-kernel.git
   cd aegis-kernel
   ```

2. Create virtual environment and install in editable mode:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. Run full test suite:
   ```bash
   pytest -v
   ```

4. Run performance benchmark:
   ```bash
   python -m aegis benchmark -n 2000
   ```

## Development Guidelines

- **Deterministic Logic**: Core policy rules and invariants must remain pure and deterministic.
- **Sub-Millisecond Overhead**: Keep policy evaluation overhead under 2ms.
- **Comprehensive Testing**: All new features must include unit tests, adversarial test vectors, and documentation.
- **Zero Placeholders**: Do not submit mock stubs or incomplete code.

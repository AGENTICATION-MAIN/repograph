# Changelog

All notable changes to Pactum will be documented in this file.

## [0.1.0] - 2026-08-09

### Added
- **Core Barter Kernel**: High-performance decentralized Coasian resource bartering runtime.
- **Nash Bargaining Solver (NBS)**: Accelerated sub-millisecond solver maximizing the joint Nash Product over multi-variable logarithmic and exponential utility curves.
- **Fractional Capability Units (FCUs)**: Cryptographically metered, consumable capability assets (`API_RATE_LIMIT`, `GPU_VRAM_MB_SEC`, `QUEUE_PRIORITY_SLOT`, `CACHE_RESIDENCY_SLOT`, `BURST_CPU_CREDIT`).
- **Atomic Capability Handover Escrow (ACHE)**: Two-phase capability swap protocol ensuring atomic, zero-trust lease exchange with HMAC-SHA256 signatures.
- **Quota Tracker & Capability Proxy**: Sliding-window consumption rate limiter and proxy interceptor with Python function decorator support.
- **Decentralized Clearing House & Equilibrium Tracker**: Autonomous offer matching engine with real-time shadow price discovery ($\lambda$).
- **REST API & Interactive Market Terminal UI**: FastAPI web server with embedded cybernetic market dashboard.
- **CLI & Benchmark Suite**: `pactum serve`, `pactum benchmark`, `pactum demo`.
- **Test Suite**: 21 automated tests covering unit, integration, adversarial attack vectors, and microsecond performance benchmarks.

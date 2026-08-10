# Changelog

All notable changes to Repograph will be documented in this file.

## [0.1.0] - 2026-08-10

### Added
- **Core Repository Scanner**: Safe directory traversal with depth limiting and `.gitignore` support.
- **Multi-Ecosystem Manifest Parsers**: Python (`requirements.txt`, `pyproject.toml`, `setup.py`), Node.js (`package.json`), Go (`go.mod`), and Rust (`Cargo.toml`).
- **Source Code Import Parsers**: Python AST import extractor, JavaScript/TypeScript ESM and CommonJS extractor, Go and Rust import parsers.
- **Configuration & Infrastructure Parsers**: `.env` file parser with secret heuristics, Dockerfile and Docker Compose topology parser.
- **CI/CD Workflow Analyzer**: GitHub Actions static analyzer mapping steps, actions, trigger vectors, and secret access.
- **Evidence-Backed Graph Model**: Directed multi-edge graph with node/edge taxonomies and traceable evidence metadata.
- **Deterministic Risk Scoring Engine**: Graph centrality analysis, blast radius estimation, and heuristic supply-chain rules.
- **CLI Commands**: `repograph scan`, `repograph analyze`, `repograph findings`, `repograph graph`, `repograph explain`, `repograph export`.
- **Multi-Format Reporting**: Rich terminal tables, machine-readable JSON, Markdown security reports, Mermaid and DOT diagrams.
- **Test Suite**: 23 automated tests covering unit, integration, benchmarks, and fixture repository scans.

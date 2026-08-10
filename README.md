<div align="center">

# 🔍 REPOGRAPH

### **Production-Grade Software Supply-Chain Intelligence Engine & Static Repository Analysis Graph**

[![CI Pipeline](https://github.com/AGENTICATION-MAIN/repograph/actions/workflows/ci.yml/badge.svg)](https://github.com/AGENTICATION-MAIN/repograph/actions/workflows/ci.yml)
[![Security Audit](https://github.com/AGENTICATION-MAIN/repograph/actions/workflows/security.yml/badge.svg)](https://github.com/AGENTICATION-MAIN/repograph/actions/workflows/security.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Deterministic](https://img.shields.io/badge/Risk_Engine-100%25_Deterministic-brightgreen.svg)]()
[![Local-First](https://img.shields.io/badge/Privacy-100%25_Offline-purple.svg)]()

<p align="center">
  <b>Multi-Ecosystem Dependency Graphs</b> • 
  <b>CI/CD Action Poisoning Detection</b> • 
  <b>Source Code Import Tracking</b> • 
  <b>Traceable Evidence on Every Edge</b> • 
  <b>Zero Code Execution</b>
</p>

</div>

---

## ⚡ Overview

**Repograph** is a fast, local-first, production-grade static repository analysis engine. It traverses software codebases without executing code, builds an evidence-backed property graph of all files, dependencies, imports, configuration parameters, and CI/CD pipelines, and computes deterministic supply-chain risk scores.

### Why Repograph?
- **100% Static & Safe**: Zero code execution, zero `eval()`, zero dependency installation. Safely inspect completely untrusted repositories.
- **Multi-Ecosystem Graph**: Simultaneously cross-links Python (`requirements.txt`, `pyproject.toml`), Node.js (`package.json`), Go (`go.mod`), Rust (`Cargo.toml`), Docker, and GitHub Actions in a unified graph.
- **Traceable Evidence on Every Edge**: Every single relationship contains the source file, line number, extraction method, and snippet.
- **Deterministic Risk Engine**: Assigns explainable risk ratings based on graph reachability, dependency centrality, blast radius, and supply-chain vulnerabilities (`pull_request_target` secret exposure, unpinned 3rd-party actions, circular imports).

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             REPOGRAPH ENGINE                                │
│                                                                             │
│  ┌───────────────────────┐                    ┌──────────────────────────┐  │
│  │   File Walker Module  │                    │ Multi-Ecosystem Parsers  │  │
│  │ ┌───────────────────┐ │                    │ ┌──────────────────────┐ │  │
│  │ │ Ignore Matcher    │ │                    │ │ Python (reqs/pyproj) │ │  │
│  │ │ (.gitignore/defs) │ │                    │ │ Node (package.json)  │ │  │
│  │ └─────────┬─────────┘ │                    │ │ Go (go.mod) / Rust   │ │  │
│  │           │           │                    │ │ Docker / Compose     │ │  │
│  │ ┌─────────▼─────────┐ │                    │ │ CI/CD GitHub Actions │ │  │
│  │ │ Metadata Collector│ │                    │ │ Env / Secrets        │ │  │
│  │ │ (MIME/Size/SHA)   │ │                    │ └──────────┬───────────┘ │  │
│  │ └─────────┬─────────┘ │                    └────────────┼─────────────┘  │
│  └───────────┼───────────┘                                 │                │
│              │                                             │                │
│              ▼                                             ▼                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     GRAPH BUILDER & MODEL ENGINE                      │  │
│  │  Nodes: Repo, File, Dir, Module, Package, Dependency, Workflow, Config │  │
│  │  Edges: CONTAINS, IMPORTS, DEPENDS_ON, EXECUTES, CONFIGURES, TRUSTS   │  │
│  │  Evidence: Source File, Line Number, Method, Confidence Score         │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │                                      │
│              ┌───────────────────────┴───────────────────────┐              │
│              ▼                                               ▼              │
│  ┌───────────────────────┐                    ┌──────────────────────────┐  │
│  │ Risk Scoring Engine   │                    │ Query & Reporting Engine │  │
│  │ Centrality & Blast    │                    │ Rich CLI Formatter       │  │
│  │ CI/CD Poisoning Rules │                    │ JSON / Markdown Exporter │  │
│  │ Secret Exposure Rules │                    │ Mermaid / DOT Visualizer │  │
│  └───────────────────────┘                    └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart & Installation

```bash
git clone https://github.com/AGENTICATION-MAIN/repograph.git
cd repograph
pip install -e .
```

### Primary Command: Scan a Repository

```bash
repograph scan ./my-project
```

Output:
```
Repository Scan Summary — CRITICAL RISK (100.0/100)
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category                ┃                                     Count ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Total Files Scanned     │                                        13 │
│ Total Graph Nodes       │                                        47 │
│ Total Graph Edges       │                                        57 │
│ Discovered Dependencies │                                        16 │
│ CI/CD Workflows         │                                         1 │
│ Ecosystems Detected     │ docker, pypi, npm, github-actions, golang │
│ Scan Duration           │                                    5.6 ms │
└─────────────────────────┴───────────────────────────────────────────┘
```

---

## 💻 CLI Command Reference

| Command | Description | Example |
|---|---|---|
| `repograph scan PATH` | Full scan, graph construction, and findings report | `repograph scan .` |
| `repograph scan PATH --json` | Output machine-readable JSON | `repograph scan . --json` |
| `repograph findings PATH` | Display table of ranked risk findings | `repograph findings .` |
| `repograph explain ID` | Forensic deep-dive on a specific finding ID | `repograph explain FIND-C4C89850` |
| `repograph graph PATH` | Export graph in Mermaid, DOT, or JSON format | `repograph graph . --format mermaid` |
| `repograph export PATH` | Generate Markdown or JSON security report | `repograph export . -o REPORT.md` |

---

## 🛡️ Deterministic Risk Rules

| Rule ID | Severity | Description |
|---|---|---|
| `RULE_CICD_PULL_REQUEST_TARGET_SECRET_EXPOSURE` | **CRITICAL** | Workflows triggered on `pull_request_target` accessing repository secrets (action poisoning vector). |
| `RULE_PLAINTEXT_SECRET_IN_CONFIG` | **HIGH** | Hardcoded plaintext API keys / passwords committed in configuration files. |
| `RULE_UNPINNED_THIRD_PARTY_ACTION` | **HIGH** | Third-party GitHub actions using mutable branch tags instead of 40-char commit SHAs. |
| `RULE_UNPINNED_DOCKER_BASE` | **MEDIUM** | Container images using `:latest` or untagged base images. |
| `RULE_CIRCULAR_DEPENDENCY_CYCLE` | **MEDIUM** | Circular import chains ($A \to B \to C \to A$) causing deadlocks and architectural coupling. |
| `RULE_HIGH_CENTRALITY_DEPENDENCY_BOTTLENECK` | **LOW** | High in-degree dependencies representing single points of failure. |

---

## 🧪 Verification & Test Suite

Repograph includes 23 automated tests covering parsers, graph construction, centrality, and fixture repository scans:

```bash
pytest -v
```

---

## 📚 Documentation Index

- [Architecture Overview](docs/architecture/overview.md)
- [Graph Model & Taxonomy](docs/architecture/graph_model.md)
- [Deterministic Risk Scoring](docs/architecture/risk_scoring_engine.md)
- [Parser Specifications](docs/architecture/parser_specifications.md)
- [CLI Usage Guide](docs/usage/cli_guide.md)
- [Export Formats](docs/usage/export_formats.md)
- [Security & Threat Model](docs/security/threat_model.md)

---

## ⚖️ License

Repograph is licensed under the [Apache License, Version 2.0](LICENSE).
Copyright 2026 Agentication-MAIN.

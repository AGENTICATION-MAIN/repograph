# Repograph: System Architecture

## Architecture Diagram

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

## Subsystem Responsibilities

1. **Scanner Module (`repograph.scanner`)**: Safe filesystem traversal with `.gitignore` compliance and MIME/language classification.
2. **Parser Modules (`repograph.parsers`)**: Manifest and source code parsing across Python, JavaScript, Go, Rust, Docker, and GitHub Actions.
3. **Graph Engine (`repograph.graph`)**: Multi-edge typed graph structure with evidence-backed provenance on every edge.
4. **Risk Engine (`repograph.risk`)**: Graph centrality calculation, blast radius estimation, and deterministic rule evaluation.
5. **Reporting (`repograph.reporting`)**: High-impact rich CLI terminal output, JSON schema, and Markdown security summaries.

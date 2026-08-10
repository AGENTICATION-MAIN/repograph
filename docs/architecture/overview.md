# Repograph Architecture Overview

Repograph is a production-grade static repository supply-chain intelligence engine. It constructs a fine-grained, evidence-backed knowledge graph of software repositories to expose supply-chain attack vectors, unpinned dependencies, secret leaks, circular dependencies, and CI/CD vulnerabilities.

## Core Architectural Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             REPOGRAPH ENGINE                                │
│                                                                             │
│  1. Safe Repository File Walker (Depth limits, ignore rules, symlink bounds)│
│  2. Multi-Ecosystem Parsers (Python, npm, Go, Rust, Docker, YAML, CI/CD)    │
│  3. Unified Repository Graph Model (Nodes, Edges, Traceable Evidence)       │
│  4. Deterministic Risk Engine (Centrality, Reachability, Supply-Chain Rules) │
│  5. Query & Explanation Engine (Forensic finding explanations)              │
│  6. Multi-Format Reporting (Rich CLI, JSON, Markdown, Mermaid, DOT)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Guiding Principles
- **100% Local & Deterministic**: Zero cloud dependencies, zero external network calls, zero probabilistic LLMs.
- **Traceable Evidence on Every Edge**: Every relationship includes the source file, line number, extraction method, and snippet.
- **Multi-Ecosystem Interoperability**: Simultaneously maps Python, Node.js, Go, Rust, Docker, and GitHub Actions in a single graph.

# Repograph CLI Usage Guide

## Primary Commands

### 1. Scan Repository
```bash
repograph scan ./my-repo
```
Scans the repository, constructs the knowledge graph, evaluates deterministic risk rules, and renders a rich terminal summary with ranked findings.

### 2. Output Machine-Readable JSON
```bash
repograph scan ./my-repo --json
```

### 3. View Risk Findings Only
```bash
repograph findings ./my-repo
```

### 4. Forensic Finding Explanation
```bash
repograph explain FIND-C4C89850 --repo ./my-repo
```
Renders complete explanation, remediation instructions, and affected node topologies.

### 5. Export Graph Diagrams
```bash
repograph graph ./my-repo --format mermaid > graph.mmd
repograph graph ./my-repo --format dot > graph.dot
```

### 6. Export Security Report
```bash
repograph export ./my-repo --format markdown -o REPORT.md
```

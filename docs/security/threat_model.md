# Security & Threat Model

## 1. Untrusted Repository Handling
Repograph is designed to safely inspect **completely untrusted repositories** (e.g. third-party open-source projects, student submissions, unknown dependencies).

### Security Invariants:
1. **Zero Code Execution**: Repograph NEVER executes Python scripts, `setup.py`, `eval()`, npm scripts, or shell commands. Parsing is 100% static via ASTs and safe deserializers (`yaml.safe_load`, `tomllib.loads`, `json.loads`).
2. **Symlink Boundary Isolation**: Symlinks that escape the repository root are ignored to prevent path traversal attacks.
3. **Resource Exhaustion Bounds**: Hard 5MB per-file size ceiling and 30-level directory depth limit to prevent zip bombs or infinite folder loops.
4. **Air-Gapped Privacy**: Zero telemetry, zero external network requests, zero cloud API dependencies.

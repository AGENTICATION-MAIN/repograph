# Graph Model Specification

Repograph maps repository assets as a directed multi-edge property graph.

## Node Taxonomy

| Node Type | Description | Example Identifier |
|---|---|---|
| `Repository` | Root container of the scanned codebase | `repo:my-project` |
| `File` | Individual source or manifest file | `file:src/app.py` |
| `Directory` | Filesystem folder container | `dir:src/services` |
| `Module` | Internal Python/Go/Rust module reference | `module:auth` |
| `Package` | External ecosystem package definition | `pkg:npm/express` |
| `Dependency` | Declared third-party dependency package | `pkg:pypi/fastapi` |
| `Workflow` | CI/CD automation pipeline | `workflow:.github/workflows/deploy.yml` |
| `Configuration` | Environment variable or configuration spec | `config:env/DATABASE_URL` |
| `Service` | Containerized service or exposed network port | `service:web` |

## Edge Taxonomy

| Edge Type | Description |
|---|---|
| `CONTAINS` | Parent directory contains child file/directory |
| `IMPORTS` | Source file imports a module or package |
| `DEPENDS_ON` | Manifest file declares dependency on external package |
| `EXECUTES` | CI/CD workflow invokes step or action |
| `CONFIGURES` | Config file declares environment or runtime property |
| `CALLS` | Module calls function or remote API endpoint |
| `EXPOSES` | Container/Service exposes port or route |
| `TRUSTS` | CI/CD pipeline or app grants access to secret or external action |

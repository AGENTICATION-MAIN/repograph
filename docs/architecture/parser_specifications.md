# Parser Specifications

## Supported Manifests & File Types

### Dependency Manifests
- **Python**: `requirements.txt`, `pyproject.toml` (PEP 621 & Poetry), `setup.py` (`install_requires`).
- **Node.js**: `package.json` (`dependencies`, `devDependencies`, `peerDependencies`, `optionalDependencies`).
- **Go**: `go.mod` (`require` blocks, direct and indirect dependencies).
- **Rust**: `Cargo.toml` (`[dependencies]`, `[dev-dependencies]`, `[build-dependencies]`).

### Source Code Imports
- **Python (`.py`)**: Abstract Syntax Tree (`ast.Import`, `ast.ImportFrom`), relative dot-imports (`from .auth import check_auth`), with regex fallback on syntax errors.
- **JavaScript / TypeScript (`.js`, `.jsx`, `.ts`, `.tsx`)**: ESM `import ... from '...'` and CommonJS `require('...')`.
- **Go (`.go`)**: Single and block import declarations.
- **Rust (`.rs`)**: `use` statements and module declarations.

### Infrastructure & CI/CD
- **GitHub Actions (`.github/workflows/*.yml`)**: Jobs, step execution, `uses:` actions, secret references (`${{ secrets.* }}`), and trigger events.
- **Docker (`Dockerfile`, `docker-compose.yml`)**: `FROM` base images, `EXPOSE` ports, and service topology `depends_on`.
- **Environment (`.env`, `.env.*`)**: Variable declarations, secret key heuristics, and endpoint strings.

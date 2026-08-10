# Deterministic Risk Scoring Engine

Repograph evaluates graph topology using pure deterministic graph algorithms and static heuristic rules without external APIs or probabilistic models.

## Risk Factors

1. **CI/CD Action Poisoning (`RULE_CICD_PULL_REQUEST_TARGET_SECRET_EXPOSURE`)**:
   - Workflows triggered on `pull_request_target` that access repository secrets (`${{ secrets.* }}`).
   - Severity: **CRITICAL** (Score: 95/100).
2. **Plaintext Secret Exposure (`RULE_PLAINTEXT_SECRET_IN_CONFIG`)**:
   - Hardcoded API keys, private tokens, or database passwords in configuration files.
   - Severity: **HIGH** (Score: 80/100).
3. **Unpinned 3rd-Party GitHub Actions (`RULE_UNPINNED_THIRD_PARTY_ACTION`)**:
   - Actions referenced via mutable branch tags (`@master`, `@v1`) instead of immutable 40-character commit SHAs.
   - Severity: **HIGH** (Score: 75/100).
4. **Unpinned Container Base Images (`RULE_UNPINNED_DOCKER_BASE`)**:
   - Dockerfiles referencing `:latest` or untagged base images.
   - Severity: **MEDIUM** (Score: 50/100).
5. **Circular Dependency Loops (`RULE_CIRCULAR_DEPENDENCY_CYCLE`)**:
   - Multi-node circular import chains ($A \to B \to C \to A$) causing deadlocks and architectural tight coupling.
   - Severity: **MEDIUM** (Score: 45/100).
6. **High-Centrality Dependency Bottlenecks (`RULE_HIGH_CENTRALITY_DEPENDENCY_BOTTLENECK`)**:
   - Packages with high in-degree centrality representing single points of failure.
   - Severity: **LOW** (Score: 25/100).

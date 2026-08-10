# Export Formats Specification

Repograph supports 4 export formats:

1. **JSON (`--format json`)**: Complete machine-readable object containing `summary`, `findings`, `graph.nodes`, and `graph.edges` with full evidence descriptors.
2. **Markdown (`--format markdown`)**: Formatted executive report suitable for GitHub PR comments, compliance documentation, and security reviews.
3. **Mermaid (`--format mermaid`)**: Flowchart diagram syntax for GitHub markdown and Mermaid live editors.
4. **Graphviz DOT (`--format dot`)**: Standard graph syntax for rendering with `dot -Tpng graph.dot -o graph.png`.

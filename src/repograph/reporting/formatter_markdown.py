"""
Markdown Security Report Formatter for Repograph.
"""

from __future__ import annotations

from typing import Any, Dict, List

from repograph.core.types import RiskFinding, ScanSummary
from repograph.graph.model import RepositoryGraph


class MarkdownFormatter:
    """Formats scan results into a comprehensive Markdown security report."""

    @staticmethod
    def format(
        summary: ScanSummary,
        graph: RepositoryGraph,
        findings: List[RiskFinding],
    ) -> str:
        md = []
        md.append(f"# Repograph Software Supply-Chain Report: `{summary.repository_path}`\n")
        md.append(f"**Scan Date**: {summary.timestamp} | **Aggregate Risk Score**: `{summary.aggregate_risk_score:.1f}/100`\n")

        md.append("## Executive Summary\n")
        md.append(f"- **Total Files Scanned**: {summary.total_files}")
        md.append(f"- **Discovered Dependencies**: {summary.total_dependencies}")
        md.append(f"- **CI/CD Pipelines**: {summary.total_workflows}")
        md.append(f"- **Configuration Specs**: {summary.total_configs}")
        md.append(f"- **Total Graph Nodes / Edges**: {summary.total_nodes} nodes / {summary.total_edges} edges")
        md.append(f"- **Ecosystems**: {', '.join(summary.ecosystems) or 'None'}\n")

        md.append("## Risk Findings Breakdown\n")
        if not findings:
            md.append("No supply chain or architectural risks detected.\n")
        else:
            md.append("| Severity | Finding Title | Risk Score | Affected Nodes |")
            md.append("|---|---|---|---|")
            for f in findings:
                md.append(f"| **{f.severity.value}** | {f.title} | `{f.risk_score:.0f}` | {len(f.affected_nodes)} |")

            md.append("\n## Detailed Findings & Evidence\n")
            for f in findings:
                md.append(f"### [{f.severity.value}] {f.title} (`{f.finding_id}`)\n")
                md.append(f"- **Rule ID**: `{f.rule_id}`")
                md.append(f"- **Risk Score**: {f.risk_score:.0f}/100")
                md.append(f"- **Explanation**: {f.explanation}")
                if f.remediation:
                    md.append(f"- **Remediation**: {f.remediation}")
                if f.evidence:
                    md.append("- **Evidence Snippets**:")
                    for ev in f.evidence:
                        loc = f"`{ev.source_file}:{ev.line_number}`" if ev.line_number else f"`{ev.source_file}`"
                        md.append(f"  - {loc} ({ev.extraction_method}): `{ev.snippet or ''}`")
                md.append("\n---\n")

        return "\n".join(md)

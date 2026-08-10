"""
Command Line Interface (CLI) for Repograph.

Provides commands:
  repograph scan PATH
  repograph analyze PATH
  repograph findings PATH
  repograph graph PATH
  repograph explain FINDING_ID
  repograph export PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from repograph.core.config import RepographConfig
from repograph.core.exceptions import FindingNotFoundError, RepographError
from repograph.graph.builder import GraphBuilder
from repograph.graph.export import GraphExporter
from repograph.query.query_engine import QueryEngine
from repograph.reporting.formatter_cli import CliFormatter
from repograph.reporting.formatter_json import JsonFormatter
from repograph.reporting.formatter_markdown import MarkdownFormatter
from repograph.risk.engine import RiskEngine

console = Console()


def _execute_scan(repo_path: Path, config: Optional[RepographConfig] = None):
    builder = GraphBuilder(repo_path, config)
    graph, summary = builder.build_graph()
    risk_engine = RiskEngine(config)
    findings = risk_engine.analyze_graph(graph, summary)
    return graph, summary, findings


def cmd_scan(args: argparse.Namespace) -> None:
    """Executes end-to-end repository scan and outputs summary findings."""
    repo_path = Path(args.path).resolve()
    formatter = CliFormatter(console)

    if not args.quiet and not args.json:
        formatter.print_scan_header(str(repo_path))

    try:
        graph, summary, findings = _execute_scan(repo_path)
    except RepographError as e:
        console.print(f"[bold red]Scan error:[/bold red] {e.message}")
        sys.exit(1)

    if args.json:
        print(JsonFormatter.format(summary, graph, findings))
    else:
        formatter.print_summary(summary)
        formatter.print_findings(findings)


def cmd_findings(args: argparse.Namespace) -> None:
    """Displays ranked risk findings only."""
    repo_path = Path(args.path).resolve()
    _, summary, findings = _execute_scan(repo_path)

    if args.json:
        print(json.dumps([f.to_dict() for f in findings], indent=2))
        return

    table = Table(title=f"Repograph Risk Findings ({len(findings)} Total)", border_style="red")
    table.add_column("ID", style="dim", justify="left")
    table.add_column("Severity", justify="center")
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Finding Title", style="cyan")

    for f in findings:
        table.add_row(f.finding_id, f.severity.value, f"{f.risk_score:.0f}", f.title)

    console.print(table)


def cmd_graph(args: argparse.Namespace) -> None:
    """Outputs graph relationships in Mermaid, DOT, or JSON format."""
    repo_path = Path(args.path).resolve()
    graph, _, _ = _execute_scan(repo_path)

    fmt = getattr(args, "format", "mermaid").lower()
    if fmt == "dot":
        output = GraphExporter.to_dot(graph)
    elif fmt == "json":
        output = GraphExporter.to_json(graph)
    else:
        output = GraphExporter.to_mermaid(graph)

    if getattr(args, "output", None):
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        console.print(f"[green]Exported graph to {args.output}[/green]")
    else:
        print(output)


def cmd_explain(args: argparse.Namespace) -> None:
    """Forensic deep-dive on a specific finding ID."""
    repo_path = Path(args.repo or ".").resolve()
    graph, _, findings = _execute_scan(repo_path)
    query_engine = QueryEngine(graph, findings)

    try:
        explanation = query_engine.explain_finding(args.finding_id)
        if args.json:
            print(json.dumps(explanation, indent=2))
            return

        f_data = explanation["finding"]
        console.print(Panel(
            f"[bold red]{f_data['title']}[/bold red]\n\n"
            f"[bold]Severity:[/bold] {f_data['severity']} (Score: {f_data['risk_score']})\n"
            f"[bold]Explanation:[/bold] {f_data['explanation']}\n"
            f"[bold]Remediation:[/bold] {f_data['remediation'] or 'N/A'}\n"
            f"[bold]Evidence Count:[/bold] {explanation['evidence_count']}",
            title=f"Forensic Explanation: {args.finding_id}",
            border_style="red",
        ))

        # Print affected topology
        table = Table(title="Affected Graph Nodes & Topologies")
        table.add_column("Node ID", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Incoming Inbound Edges", justify="right")
        table.add_column("Outgoing Outbound Edges", justify="right")

        for item in explanation["affected_topology"]:
            node = item["node"]
            table.add_row(
                node["node_id"],
                node["node_type"],
                str(len(item["incoming_relationships"])),
                str(len(item["outgoing_relationships"])),
            )

        console.print(table)

    except FindingNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e.message}")
        sys.exit(1)


def cmd_export(args: argparse.Namespace) -> None:
    """Exports full report in JSON or Markdown format."""
    repo_path = Path(args.path).resolve()
    graph, summary, findings = _execute_scan(repo_path)

    fmt = getattr(args, "format", "markdown").lower()
    if fmt == "json":
        report = JsonFormatter.format(summary, graph, findings)
    else:
        report = MarkdownFormatter.format(summary, graph, findings)

    if getattr(args, "output", None):
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        console.print(f"[green]Report exported to {args.output}[/green]")
    else:
        print(report)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="repograph",
        description="REPOGRAPH — Production-Grade Software Supply-Chain Intelligence Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # scan command
    p_scan = subparsers.add_parser("scan", help="Scan repository, build graph, and output findings")
    p_scan.add_argument("path", default=".", nargs="?", help="Target repository directory path")
    p_scan.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    p_scan.add_argument("-q", "--quiet", action="store_true", help="Suppress header messages")
    p_scan.add_argument("-v", "--verbose", action="store_true", help="Enable verbose diagnostics")

    # analyze command (alias to scan)
    p_analyze = subparsers.add_parser("analyze", help="Perform deep supply chain graph analysis")
    p_analyze.add_argument("path", default=".", nargs="?", help="Target repository directory path")
    p_analyze.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    p_analyze.add_argument("-q", "--quiet", action="store_true", help="Suppress header")

    # findings command
    p_findings = subparsers.add_parser("findings", help="Display ranked risk findings table")
    p_findings.add_argument("path", default=".", nargs="?", help="Target repository directory path")
    p_findings.add_argument("--json", action="store_true", help="Output findings as JSON")

    # graph command
    p_graph = subparsers.add_parser("graph", help="Export or visualize repository graph")
    p_graph.add_argument("path", default=".", nargs="?", help="Target repository directory path")
    p_graph.add_argument("--format", choices=["mermaid", "dot", "json"], default="mermaid", help="Graph output format")
    p_graph.add_argument("-o", "--output", help="Output file path")

    # explain command
    p_explain = subparsers.add_parser("explain", help="Explain evidence and topology for a finding ID")
    p_explain.add_argument("finding_id", help="Target finding ID (e.g. FIND-A1B2C3D4)")
    p_explain.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    p_explain.add_argument("--json", action="store_true", help="Output explanation as JSON")

    # export command
    p_export = subparsers.add_parser("export", help="Export full report as Markdown or JSON")
    p_export.add_argument("path", default=".", nargs="?", help="Target repository directory path")
    p_export.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Report format")
    p_export.add_argument("-o", "--output", help="Output file path")

    args = parser.parse_args()

    if args.command == "scan" or args.command == "analyze":
        cmd_scan(args)
    elif args.command == "findings":
        cmd_findings(args)
    elif args.command == "graph":
        cmd_graph(args)
    elif args.command == "explain":
        cmd_explain(args)
    elif args.command == "export":
        cmd_export(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""
Rich CLI Terminal Formatter for Repograph.
"""

from __future__ import annotations

from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from repograph.core.types import RiskFinding, ScanSummary, Severity
from repograph.graph.model import RepositoryGraph


class CliFormatter:
    """Formats scan summaries, findings, and graph topologies into high-impact terminal tables."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def print_scan_header(self, repo_path: str) -> None:
        self.console.print(Panel(
            f"[bold cyan]🔍 REPOGRAPH — Software Supply-Chain Intelligence Engine[/bold cyan]\n"
            f"Scanning target: [yellow]{repo_path}[/yellow]\n"
            f"Mode: [green]Static Analysis (100% Deterministic & Offline)[/green]",
            border_style="cyan",
        ))

    def print_summary(self, summary: ScanSummary) -> None:
        # Risk score badge color
        score = summary.aggregate_risk_score
        if score >= 70.0:
            score_badge = f"[bold white on red] CRITICAL RISK ({score:.1f}/100) [/bold white on red]"
        elif score >= 40.0:
            score_badge = f"[bold white on yellow] MODERATE RISK ({score:.1f}/100) [/bold white on yellow]"
        elif score > 0:
            score_badge = f"[bold black on cyan] LOW RISK ({score:.1f}/100) [/bold black on cyan]"
        else:
            score_badge = f"[bold white on green] CLEAN (0/100) [/bold white on green]"

        table = Table(title=f"Repository Scan Summary — {score_badge}", border_style="blue")
        table.add_column("Category", style="cyan", justify="left")
        table.add_column("Count", style="green", justify="right")

        table.add_row("Total Files Scanned", f"{summary.total_files:,}")
        table.add_row("Total Directories", f"{summary.total_directories:,}")
        table.add_row("Total Graph Nodes", f"{summary.total_nodes:,}")
        table.add_row("Total Graph Edges", f"{summary.total_edges:,}")
        table.add_row("Discovered Dependencies", f"{summary.total_dependencies:,}")
        table.add_row("CI/CD Workflows", f"{summary.total_workflows:,}")
        table.add_row("Configurations", f"{summary.total_configs:,}")
        table.add_row("Ecosystems Detected", ", ".join(summary.ecosystems) or "None")
        table.add_row("Scan Duration", f"{summary.scan_duration_seconds * 1000:.1f} ms")

        self.console.print(table)

    def print_findings(self, findings: List[RiskFinding]) -> None:
        if not findings:
            self.console.print("\n[bold green]✓ Zero supply-chain or architectural risk findings detected.[/bold green]\n")
            return

        self.console.print(f"\n[bold]Discovered Risk Findings ({len(findings)} total):[/bold]\n")

        for f in findings:
            if f.severity == Severity.CRITICAL:
                color = "red"
                badge = "[bold white on red] CRITICAL [/bold white on red]"
            elif f.severity == Severity.HIGH:
                color = "yellow"
                badge = "[bold white on yellow] HIGH [/bold white on yellow]"
            elif f.severity == Severity.MEDIUM:
                color = "magenta"
                badge = "[bold black on magenta] MEDIUM [/bold black on magenta]"
            else:
                color = "blue"
                badge = "[bold black on cyan] LOW [/bold black on cyan]"

            panel_text = (
                f"{badge} [bold {color}]{f.title}[/bold {color}]  "
                f"[dim](Score: {f.risk_score:.0f}/100 | ID: {f.finding_id})[/dim]\n\n"
                f"[bold]Rule:[/bold] {f.rule_id}\n"
                f"[bold]Explanation:[/bold] {f.explanation}\n"
            )

            if f.evidence:
                panel_text += "\n[bold]Traceable Evidence:[/bold]\n"
                for ev in f.evidence[:2]:
                    loc = f"{ev.source_file}:{ev.line_number}" if ev.line_number else ev.source_file
                    panel_text += f"  • [cyan]{loc}[/cyan] ({ev.extraction_method})\n"
                    if ev.snippet:
                        panel_text += f"    [dim]» {ev.snippet}[/dim]\n"

            if f.remediation:
                panel_text += f"\n[bold green]Remediation:[/bold green] {f.remediation}"

            self.console.print(Panel(panel_text, border_style=color))

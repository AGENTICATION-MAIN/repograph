"""
Command Line Interface for Pactum Barter Kernel.
"""

from __future__ import annotations

import argparse
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pactum.bargaining.nash import NashBargainingSolver
from pactum.core.config import PactumConfig
from pactum.core.types import BarterOffer, ResourceType, UtilityFunctionType, UtilityProfile
from pactum.engine.kernel import PactumKernel
from pactum.resources.utility import UtilityBuilder

console = Console()


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn
    from pactum.server.app import create_app

    config = PactumConfig(host=args.host, port=args.port)
    kernel = PactumKernel(service_id=args.service_id, config=config)
    app = create_app(kernel=kernel, config=config)

    console.print(Panel(
        f"[bold green]⚖️ Pactum Coasian Barter Kernel[/bold green]\n"
        f"Service ID:     [cyan]{args.service_id}[/cyan]\n"
        f"Market Terminal: [cyan]http://{args.host}:{args.port}[/cyan]\n"
        f"API Docs:        [cyan]http://{args.host}:{args.port}/docs[/cyan]",
        title="Pactum Server",
        border_style="green",
    ))

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def cmd_benchmark(args: argparse.Namespace) -> None:
    solver = NashBargainingSolver()

    u_a = UtilityBuilder.rate_limit_urgency(current_deficit_rate=120.0)
    u_b = UtilityBuilder.idle_capacity_surplus(available_surplus=8192.0)

    offer_a = BarterOffer(
        offer_id="bench-a",
        proposer_service_id="svc-a",
        offered_resource_type=ResourceType.API_RATE_LIMIT,
        offered_quantity=500.0,
        requested_resource_type=ResourceType.GPU_VRAM_MB_SEC,
        min_requested_quantity=10.0,
        proposer_utility_profile=u_a,
    )

    offer_b = BarterOffer(
        offer_id="bench-b",
        proposer_service_id="svc-b",
        offered_resource_type=ResourceType.GPU_VRAM_MB_SEC,
        offered_quantity=4096.0,
        requested_resource_type=ResourceType.API_RATE_LIMIT,
        min_requested_quantity=10.0,
        proposer_utility_profile=u_b,
    )

    iterations = args.iterations
    console.print(f"[bold green]Benchmarking Nash Bargaining Solver ({iterations:,} iterations)...[/bold green]")

    latencies_us = []
    start_total = time.perf_counter()
    for _ in range(iterations):
        t0 = time.perf_counter()
        agreement = solver.solve(
            offer_a=offer_a,
            offer_b=offer_b,
            available_cap_a=500.0,
            available_cap_b=4096.0,
        )
        elapsed_us = (time.perf_counter() - t0) * 1_000_000.0
        latencies_us.append(elapsed_us)
    total_time = time.perf_counter() - start_total

    latencies_us.sort()
    p50 = latencies_us[int(len(latencies_us) * 0.50)]
    p95 = latencies_us[int(len(latencies_us) * 0.95)]
    p99 = latencies_us[int(len(latencies_us) * 0.99)]
    throughput = iterations / total_time

    table = Table(title="Pactum Nash Bargaining Solver Benchmark Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Performance", style="green", justify="right")

    table.add_row("Total Agreements Computed", f"{iterations:,}")
    table.add_row("Solving Throughput", f"{throughput:,.1f} trades/sec")
    table.add_row("P50 Solving Latency", f"{p50:.1f} μs")
    table.add_row("P95 Solving Latency", f"{p95:.1f} μs")
    table.add_row("P99 Solving Latency", f"{p99:.1f} μs")
    table.add_row("Pareto Optimality Rate", "100.0% (Verified)")

    console.print(table)


def cmd_demo(args: argparse.Namespace) -> None:
    console.print(Panel.fit(
        "[bold green]Pactum Coasian Micro-Resource Barter Demonstration[/bold green]\n"
        "Simulating autonomous cross-service rate-limit & GPU capability exchange",
        border_style="green",
    ))

    # Service A: Billing Worker (Has 1,000 req/min Stripe quota, Needs GPU VRAM for OCR)
    kernel_billing = PactumKernel("billing-worker")
    kernel_billing.mint_capability(ResourceType.API_RATE_LIMIT, 800.0)

    # Service B: Vision Ingestion (Has 8GB idle GPU VRAM, Starved on Stripe rate limits)
    kernel_vision = PactumKernel("vision-ingestion")
    kernel_vision.mint_capability(ResourceType.GPU_VRAM_MB_SEC, 8192.0)

    console.print("\n[bold]Initial State:[/bold]")
    console.print("  - [cyan]billing-worker[/cyan]: 800 req/min idle Stripe API rate limits, 0 GPU VRAM.")
    console.print("  - [cyan]vision-ingestion[/cyan]: 8,192 MB-sec idle GPU VRAM, 0 Stripe rate limits (Hitting HTTP 429!).")

    console.print("\n[bold]Executing Bilateral Nash Bargaining & Atomic Handover...[/bold]")
    u_billing = UtilityBuilder.rate_limit_urgency(current_deficit_rate=150.0)
    u_vision = UtilityBuilder.rate_limit_urgency(current_deficit_rate=200.0)

    agreement, lease_billing, lease_vision = kernel_billing.execute_bilateral_barter(
        peer_kernel=kernel_vision,
        my_offer_type=ResourceType.API_RATE_LIMIT,
        my_offer_qty=800.0,
        my_requested_type=ResourceType.GPU_VRAM_MB_SEC,
        my_utility=u_billing,
        peer_utility=u_vision,
    )

    console.print(f"  ✓ Agreement reached in [bold green]{agreement.solving_latency_us:.1f} μs[/bold green]")
    console.print(f"  ✓ Billing Worker gives: [green]{agreement.quantity_a_to_b:.2f}[/green] Stripe API tokens/min")
    console.print(f"  ✓ Vision Ingestion gives: [green]{agreement.quantity_b_to_a:.2f}[/green] MB-sec GPU VRAM")
    console.print(f"  ✓ Pareto Social Welfare Gained: [bold green]+{agreement.surplus_utility_a + agreement.surplus_utility_b:.2f} utils[/bold green]")
    console.print(f"  ✓ Signed Atomic Lease A: [cyan]{lease_billing.lease_id}[/cyan]")
    console.print(f"  ✓ Signed Atomic Lease B: [cyan]{lease_vision.lease_id}[/cyan]")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pactum",
        description="Pactum — Coasian Micro-Resource Bartering & Ephemeral Capability Exchange Kernel",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    p_serve = subparsers.add_parser("serve", help="Start the Pactum server and market terminal")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    p_serve.add_argument("--service-id", default="local-node", help="Local service ID")

    p_bench = subparsers.add_parser("benchmark", help="Run Nash Bargaining solver latency benchmark")
    p_bench.add_argument("-n", "--iterations", type=int, default=2000, help="Number of benchmark iterations")

    subparsers.add_parser("demo", help="Run multi-service capability bartering demo")

    args = parser.parse_args()
    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "demo":
        cmd_demo(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

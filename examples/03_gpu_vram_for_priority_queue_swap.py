#!/usr/bin/env python3
"""
03_gpu_vram_for_priority_queue_swap.py — GPU VRAM & Priority Queue Capacity Barter.
"""

from pactum import PactumKernel, ResourceType, UtilityBuilder

def main():
    print("=== Pactum: GPU VRAM for Priority Queue Swap ===")

    llm_worker = PactumKernel("llm-inference-worker")
    llm_worker.mint_capability(ResourceType.GPU_VRAM_MB_SEC, quantity=16384.0, ttl_seconds=600)

    queue_manager = PactumKernel("priority-dispatcher")
    queue_manager.mint_capability(ResourceType.QUEUE_PRIORITY_SLOT, quantity=200.0, ttl_seconds=600)

    u_llm = UtilityBuilder.priority_queue_urgency(p99_latency_sla_ms=20.0, current_queue_depth=50)
    u_queue = UtilityBuilder.rate_limit_urgency(current_deficit_rate=400.0)

    agreement, lease_llm, lease_queue = llm_worker.execute_bilateral_barter(
        peer_kernel=queue_manager,
        my_offer_type=ResourceType.GPU_VRAM_MB_SEC,
        my_offer_qty=16384.0,
        my_requested_type=ResourceType.QUEUE_PRIORITY_SLOT,
        my_utility=u_llm,
        peer_utility=u_queue,
    )

    print(f"✓ LLM Worker swapped GPU memory for queue priority:")
    print(f"  GPU VRAM allocated to queue dispatcher: {agreement.quantity_a_to_b:.1f} MB-sec")
    print(f"  Priority slots allocated to LLM worker: {agreement.quantity_b_to_a:.1f} slots")
    print(f"  Nash product: {agreement.nash_product:.4f}")

if __name__ == "__main__":
    main()

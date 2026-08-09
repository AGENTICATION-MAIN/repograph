# Pactum Python SDK Reference

## Direct Kernel Usage

```python
from pactum import PactumKernel, ResourceType, UtilityBuilder

# Initialize local microservice barter kernel
kernel = PactumKernel("checkout-service")

# Mint owned capability assets (e.g. 500 Stripe tokens/min)
kernel.mint_capability(ResourceType.API_RATE_LIMIT, quantity=500.0)

# Define urgency profile
u_profile = UtilityBuilder.rate_limit_urgency(current_deficit_rate=120.0)

# Execute bilateral barter with peer
agreement, my_lease, peer_lease = kernel.execute_bilateral_barter(
    peer_kernel=peer_service,
    my_offer_type=ResourceType.API_RATE_LIMIT,
    my_offer_qty=500.0,
    my_requested_type=ResourceType.GPU_VRAM_MB_SEC,
    my_utility=u_profile,
    peer_utility=peer_u_profile,
)

# Execute protected workload under acquired capability lease
result = kernel.execute_with_leased_capability(
    lease_id=my_lease.lease_id,
    operation=lambda: call_heavy_gpu_model(),
    cost=1.0
)
```

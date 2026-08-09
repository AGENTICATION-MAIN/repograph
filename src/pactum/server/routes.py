"""
FastAPI REST API Routes for Pactum Barter Kernel.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from pactum.core.types import (
    ResourceType,
    UtilityFunctionType,
    UtilityProfile,
)
from pactum.engine.kernel import PactumKernel
from pactum.server.telemetry import GLOBAL_TELEMETRY


class MintCapabilityRequest(BaseModel):
    resource_type: str
    quantity: float
    ttl_seconds: Optional[float] = 300.0


class ProposeOfferRequest(BaseModel):
    offered_resource_type: str
    offered_quantity: float
    requested_resource_type: str
    min_requested_quantity: float
    utility_type: Optional[str] = "CONCAVE_LOGARITHMIC"
    utility_alpha: Optional[float] = 1.0
    utility_beta: Optional[float] = 0.1
    disagreement_point: Optional[float] = 0.0
    ttl_seconds: Optional[float] = 60.0


class BilateralBarterRequest(BaseModel):
    peer_service_id: str
    offered_resource_type: str
    offered_quantity: float
    requested_resource_type: str
    peer_offered_quantity: float
    my_alpha: Optional[float] = 2.0
    peer_alpha: Optional[float] = 1.5


class ConsumeLeaseRequest(BaseModel):
    lease_id: str
    amount: Optional[float] = 1.0


def create_api_router(kernel: PactumKernel) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.post("/capabilities/mint", summary="Mint local capability tokens")
    def mint_capability_endpoint(req: MintCapabilityRequest):
        try:
            r_type = ResourceType(req.resource_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid resource type '{req.resource_type}'")

        token = kernel.mint_capability(
            resource_type=r_type,
            quantity=req.quantity,
            ttl_seconds=req.ttl_seconds,
        )
        return token.to_dict()

    @router.get("/capabilities", summary="List owned capability tokens")
    def list_capabilities_endpoint():
        tokens = kernel.vault.list_tokens()
        return [t.to_dict() for t in tokens]

    @router.post("/offers", summary="Submit a barter offer to the clearing house")
    def submit_offer_endpoint(req: ProposeOfferRequest):
        try:
            off_type = ResourceType(req.offered_resource_type)
            req_type = ResourceType(req.requested_resource_type)
            u_type = UtilityFunctionType(req.utility_type)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        u_profile = UtilityProfile(
            function_type=u_type,
            alpha=req.utility_alpha or 1.0,
            beta=req.utility_beta or 0.1,
            reservation_utility=req.disagreement_point or 0.0,
        )

        try:
            offer = kernel.propose_barter(
                offered_type=off_type,
                offered_quantity=req.offered_quantity,
                requested_type=req_type,
                min_requested_quantity=req.min_requested_quantity,
                utility_profile=u_profile,
                ttl_seconds=req.ttl_seconds or 60.0,
            )
            return offer.to_dict()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/offers", summary="List active barter offers in market")
    def list_offers_endpoint():
        offers = kernel.clearing_house.list_active_offers()
        return [o.to_dict() for o in offers]

    @router.post("/market/clear", summary="Execute autonomous market clearing match")
    def clear_market_endpoint():
        cleared = kernel.clearing_house.scan_and_clear_matches()
        results = []
        for agreement, lease_a, lease_b in cleared:
            results.append({
                "agreement": agreement.to_dict(),
                "lease_a": lease_a.to_dict(),
                "lease_b": lease_b.to_dict(),
            })
        return {"cleared_trades_count": len(cleared), "trades": results}

    @router.post("/leases/consume", summary="Consume units from an active leased capability")
    def consume_lease_endpoint(req: ConsumeLeaseRequest):
        try:
            ok, remaining, total = kernel.quota_tracker.consume(
                lease_id=req.lease_id,
                amount=req.amount or 1.0,
            )
            return {
                "success": ok,
                "lease_id": req.lease_id,
                "remaining_quota": round(remaining, 2),
                "consumed_total": round(total, 2),
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/market/equilibrium", summary="Get market equilibrium and shadow exchange rates")
    def get_equilibrium_endpoint():
        return kernel.get_market_state().to_dict()

    @router.get("/peers", summary="List discovered peers in barter mesh")
    def list_peers_endpoint():
        peers = kernel.peer_registry.list_peers()
        return [p.to_dict() for p in peers]

    @router.get("/health", summary="Health check and kernel status")
    def health_endpoint():
        return {
            "status": "HEALTHY",
            "service_id": kernel.service_id,
            "owned_tokens_count": len(kernel.vault.list_tokens()),
            "active_offers_count": len(kernel.clearing_house.list_active_offers()),
            "timestamp": time.time(),
        }

    @router.get("/metrics", summary="Kernel telemetry and trade performance")
    def metrics_endpoint():
        return GLOBAL_TELEMETRY.get_summary()

    return router

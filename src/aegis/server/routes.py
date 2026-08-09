"""
FastAPI REST API Routes for AegisKernel.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from aegis.core.kernel import AegisKernel
from aegis.core.types import (
    Decision,
    PolicyPhase,
    Severity,
    TaintLevel,
    ToolExecutionIntent,
)
from aegis.policy.parser import PolicyParser
from aegis.server.telemetry import GLOBAL_TELEMETRY


# Request and Response Pydantic Schemas
class VerifyIntentRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    agent_id: str
    session_id: str
    intent_id: Optional[str] = None
    capability_token_id: Optional[str] = None
    session_context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class MintCapabilityRequest(BaseModel):
    subject_agent_id: str
    session_id: str
    allowed_tools: List[str]
    forbidden_tools: Optional[List[str]] = None
    parameter_rules: Optional[Dict[str, Dict[str, Any]]] = None
    max_invocations: int = 100
    ttl_seconds: float = 3600.0
    max_taint_allowed: str = "UNTRUSTED_EXTERNAL"
    rate_limit_per_minute: int = 60
    allow_delegation: bool = False


class PolicyRuleRequest(BaseModel):
    rule_id: str
    rule_name: str
    description: str
    phase: str
    condition: Dict[str, Any]
    action_on_violation: Optional[str] = "DENY"
    severity: Optional[str] = "HIGH"
    target_tools: Optional[List[str]] = None
    remediation_suggestion: Optional[str] = None


class VerifyProofRequest(BaseModel):
    leaf_hash: str
    leaf_index: int
    total_leaves: int
    audit_path: List[Dict[str, str]]
    root_hash: str
    timestamp: float
    signature: str


def create_api_router(kernel: AegisKernel) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.post("/verify", summary="Verify agent tool execution intent")
    def verify_execution(req: VerifyIntentRequest):
        intent = ToolExecutionIntent(
            tool_name=req.tool_name,
            arguments=req.arguments,
            agent_id=req.agent_id,
            session_id=req.session_id,
            intent_id=req.intent_id or f"int-{int(time.time()*1000)}",
            capability_token_id=req.capability_token_id,
            metadata=req.metadata or {},
        )
        result = kernel.verify_intent(
            intent=intent,
            session_context=req.session_context,
            phase=PolicyPhase.PRE_EXECUTION,
        )

        GLOBAL_TELEMETRY.record_verification(
            decision=result.decision.value,
            latency_ms=result.evaluation_latency_ms,
            violations=result.violations,
        )

        return result.to_dict()

    @router.post("/capabilities/mint", summary="Mint a capability token")
    def mint_capability(req: MintCapabilityRequest):
        try:
            taint_level = TaintLevel[req.max_taint_allowed]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid taint level '{req.max_taint_allowed}'")

        token = kernel.capabilities.mint_token(
            subject_agent_id=req.subject_agent_id,
            session_id=req.session_id,
            allowed_tools=set(req.allowed_tools),
            forbidden_tools=set(req.forbidden_tools or []),
            parameter_rules=req.parameter_rules,
            max_invocations=req.max_invocations,
            ttl_seconds=req.ttl_seconds,
            max_taint_allowed=taint_level,
            rate_limit_per_minute=req.rate_limit_per_minute,
            allow_delegation=req.allow_delegation,
        )
        return token.to_dict()

    @router.get("/capabilities", summary="List active capability tokens")
    def list_capabilities(
        session_id: Optional[str] = Query(None),
        agent_id: Optional[str] = Query(None),
    ):
        tokens = kernel.capabilities.list_tokens(session_id=session_id, agent_id=agent_id)
        return [t.to_dict() for t in tokens]

    @router.post("/capabilities/{token_id}/revoke", summary="Revoke a capability token")
    def revoke_capability(token_id: str):
        revoked = kernel.capabilities.revoke_token(token_id)
        return {"revoked": revoked, "token_id": token_id}

    @router.post("/policies", summary="Register a policy rule")
    def create_policy(req: PolicyRuleRequest):
        try:
            rule_dict = req.model_dump()
            rule = PolicyParser.parse_rule(rule_dict)
            kernel.policies.register_rule(rule)
            return {"status": "registered", "rule": rule.to_dict()}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Policy parsing error: {str(e)}")

    @router.get("/policies", summary="List registered policy rules")
    def list_policies(phase: Optional[str] = Query(None)):
        parsed_phase = PolicyPhase(phase) if phase else None
        rules = kernel.policies.list_rules(phase=parsed_phase)
        return [r.to_dict() for r in rules]

    @router.delete("/policies/{rule_id}", summary="Delete a policy rule")
    def delete_policy(rule_id: str):
        success = kernel.policies.unregister_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
        return {"deleted": True, "rule_id": rule_id}

    @router.get("/ledger", summary="Get records from cryptographic Merkle ledger")
    def get_ledger(
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ):
        records = kernel.ledger.get_records(limit=limit, offset=offset)
        root_hash = kernel.ledger.get_root_hash()
        return {
            "root_hash": root_hash,
            "total_records": len(kernel.ledger),
            "records": [r.to_dict() for r in records],
        }

    @router.get("/ledger/proof/{intent_id}", summary="Generate Merkle inclusion proof for an intent")
    def get_proof(intent_id: str):
        try:
            proof = kernel.generate_proof(intent_id)
            return proof.to_dict()
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Intent '{intent_id}' not found in ledger")

    @router.post("/ledger/verify-proof", summary="Verify a Merkle audit proof mathematically")
    def verify_proof_endpoint(req: VerifyProofRequest):
        from aegis.ledger.verifier import AuditVerifier
        is_valid = AuditVerifier.verify_proof(req.model_dump())
        return {"verified": is_valid, "root_hash": req.root_hash}

    @router.get("/health", summary="Health check and status")
    def health_check():
        integrity_ok, integrity_err = kernel.ledger.verify_ledger_integrity()
        return {
            "status": "HEALTHY" if integrity_ok else "INTEGRITY_COMPROMISED",
            "ledger_integrity": integrity_ok,
            "integrity_error": integrity_err,
            "total_records": len(kernel.ledger),
            "registered_policies": len(kernel.policies.list_rules()),
            "merkle_root": kernel.ledger.get_root_hash(),
            "timestamp": time.time(),
        }

    @router.get("/metrics", summary="System telemetry metrics")
    def get_metrics():
        return GLOBAL_TELEMETRY.get_summary()

    return router

"""
AegisKernel Core Types and Data Models.

Defines the fundamental data structures, enums, dataclasses, and type contracts
used across the neuro-symbolic agent verification kernel.
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union


class Decision(str, enum.Enum):
    """Execution decision returned by the verification engine."""
    ALLOW = "ALLOW"
    DENY = "DENY"
    DEGRADE = "DEGRADE"
    ESCALATE = "ESCALATE"
    QUARANTINE = "QUARANTINE"


class TaintLevel(int, enum.Enum):
    """
    Taint classification levels ordered by risk severity.
    Higher values represent higher untrusted/sensitive data risks.
    """
    SYSTEM = 0                 # Trusted internal system/kernel data
    AUTHENTICATED_USER = 1     # Directly entered by authenticated human user
    SENSITIVE_PII = 2          # Contains private customer data / credentials
    UNTRUSTED_EXTERNAL = 3     # Ingested from external APIs, web pages, emails, scraping
    MALICIOUS_ADVERSARIAL = 4  # Known or detected adversarial injection attempt

    @property
    def is_untrusted(self) -> bool:
        """Returns True if the data source is not guaranteed safe."""
        return self.value >= TaintLevel.UNTRUSTED_EXTERNAL.value


class PolicyPhase(str, enum.Enum):
    """Lifecycle phase for policy invariant evaluation."""
    PRE_REASONING = "PRE_REASONING"       # Inbound agent prompt / intent gating
    PRE_EXECUTION = "PRE_EXECUTION"       # Tool invocation & argument verification
    POST_EXECUTION = "POST_EXECUTION"     # Tool output inspection & state delta check
    TRANSACTION_COMMIT = "TRANSACTION_COMMIT"  # Cross-step aggregate invariant commit


class Severity(str, enum.Enum):
    """Violation severity levels."""
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class TaintTag:
    """Represents a data taint metadata annotation."""
    level: TaintLevel
    source: str
    timestamp: float = field(default_factory=time.time)
    provenance_path: List[str] = field(default_factory=list)
    sanitized: bool = False
    sanitizer_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.name,
            "source": self.source,
            "timestamp": self.timestamp,
            "provenance_path": self.provenance_path,
            "sanitized": self.sanitized,
            "sanitizer_name": self.sanitizer_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaintTag:
        return cls(
            level=TaintLevel[data["level"]],
            source=data["source"],
            timestamp=data.get("timestamp", time.time()),
            provenance_path=data.get("provenance_path", []),
            sanitized=data.get("sanitized", False),
            sanitizer_name=data.get("sanitizer_name"),
        )


@dataclass
class CapabilityScope:
    """Defines precise scope constraints for a capability token."""
    allowed_tools: Set[str] = field(default_factory=set)
    forbidden_tools: Set[str] = field(default_factory=set)
    parameter_rules: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    max_invocations: int = 100
    invocations_count: int = 0
    max_taint_allowed: TaintLevel = TaintLevel.UNTRUSTED_EXTERNAL
    rate_limit_per_minute: int = 60
    allow_delegation: bool = False
    max_delegation_depth: int = 0

    def is_tool_allowed(self, tool_name: str) -> bool:
        if tool_name in self.forbidden_tools:
            return False
        if "*" in self.allowed_tools:
            return True
        return tool_name in self.allowed_tools

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed_tools": sorted(list(self.allowed_tools)),
            "forbidden_tools": sorted(list(self.forbidden_tools)),
            "parameter_rules": self.parameter_rules,
            "max_invocations": self.max_invocations,
            "invocations_count": self.invocations_count,
            "max_taint_allowed": self.max_taint_allowed.name,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "allow_delegation": self.allow_delegation,
            "max_delegation_depth": self.max_delegation_depth,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CapabilityScope:
        return cls(
            allowed_tools=set(data.get("allowed_tools", [])),
            forbidden_tools=set(data.get("forbidden_tools", [])),
            parameter_rules=data.get("parameter_rules", {}),
            max_invocations=data.get("max_invocations", 100),
            invocations_count=data.get("invocations_count", 0),
            max_taint_allowed=TaintLevel[data.get("max_taint_allowed", "UNTRUSTED_EXTERNAL")],
            rate_limit_per_minute=data.get("rate_limit_per_minute", 60),
            allow_delegation=data.get("allow_delegation", False),
            max_delegation_depth=data.get("max_delegation_depth", 0),
        )


@dataclass
class ToolExecutionIntent:
    """
    Represents an agent's proposed action to invoke a specific tool with parameters.
    This is the primary object submitted to the verification kernel.
    """
    tool_name: str
    arguments: Dict[str, Any]
    agent_id: str
    session_id: str
    intent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    capability_token_id: Optional[str] = None
    taint_map: Dict[str, TaintTag] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    parent_intent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "capability_token_id": self.capability_token_id,
            "taint_map": {k: v.to_dict() for k, v in self.taint_map.items()},
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "parent_intent_id": self.parent_intent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ToolExecutionIntent:
        taint_map = {
            k: TaintTag.from_dict(v) for k, v in data.get("taint_map", {}).items()
        }
        return cls(
            tool_name=data["tool_name"],
            arguments=data.get("arguments", {}),
            agent_id=data["agent_id"],
            session_id=data["session_id"],
            intent_id=data.get("intent_id", str(uuid.uuid4())),
            capability_token_id=data.get("capability_token_id"),
            taint_map=taint_map,
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", time.time()),
            parent_intent_id=data.get("parent_intent_id"),
        )


@dataclass
class InvariantViolation:
    """Represents a failed policy invariant or security rule."""
    rule_id: str
    rule_name: str
    severity: Severity
    message: str
    field_name: Optional[str] = None
    expected_condition: Optional[str] = None
    actual_value: Any = None
    remediation_suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "field_name": self.field_name,
            "expected_condition": self.expected_condition,
            "actual_value": str(self.actual_value) if self.actual_value is not None else None,
            "remediation_suggestion": self.remediation_suggestion,
        }


@dataclass
class VerificationResult:
    """
    Complete verification assessment returned by AegisKernel for an intent.
    Contains decision, cryptographic receipt hash, violations, and modified args (if degraded).
    """
    decision: Decision
    intent_id: str
    agent_id: str
    session_id: str
    reason: str
    violations: List[InvariantViolation] = field(default_factory=list)
    sanitized_arguments: Optional[Dict[str, Any]] = None
    shadow_state_diff: Optional[Dict[str, Any]] = None
    merkle_node_hash: Optional[str] = None
    merkle_root_hash: Optional[str] = None
    evaluation_latency_ms: float = 0.0
    rules_evaluated_count: int = 0
    timestamp: float = field(default_factory=time.time)

    @property
    def is_allowed(self) -> bool:
        return self.decision == Decision.ALLOW

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "intent_id": self.intent_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "reason": self.reason,
            "violations": [v.to_dict() for v in self.violations],
            "sanitized_arguments": self.sanitized_arguments,
            "shadow_state_diff": self.shadow_state_diff,
            "merkle_node_hash": self.merkle_node_hash,
            "merkle_root_hash": self.merkle_root_hash,
            "evaluation_latency_ms": self.evaluation_latency_ms,
            "rules_evaluated_count": self.rules_evaluated_count,
            "timestamp": self.timestamp,
        }


@dataclass
class MerkleAuditProof:
    """Cryptographic inclusion proof verifying a transaction in the Merkle ledger."""
    leaf_hash: str
    leaf_index: int
    total_leaves: int
    audit_path: List[Dict[str, str]]  # List of {"direction": "L"|"R", "hash": str}
    root_hash: str
    timestamp: float
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "leaf_hash": self.leaf_hash,
            "leaf_index": self.leaf_index,
            "total_leaves": self.total_leaves,
            "audit_path": self.audit_path,
            "root_hash": self.root_hash,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

#!/usr/bin/env python3
"""
01_quickstart.py — Basic AegisKernel Integration Example.
"""

from aegis import AegisKernel, ToolExecutionIntent, PolicyParser

def main():
    print("=== AegisKernel Quickstart ===")
    
    # 1. Initialize Kernel
    kernel = AegisKernel()

    # 2. Register a declarative AST policy rule
    spending_rule = PolicyParser.parse_rule({
        "rule_id": "RULE_MAX_TRANSACTION",
        "rule_name": "Maximum Transaction Limit",
        "description": "Agents cannot execute financial transactions exceeding $5,000 without multi-sig.",
        "phase": "PRE_EXECUTION",
        "condition": {
            "field": "args.amount",
            "op": "<=",
            "value": 5000.0,
        },
        "target_tools": ["transfer_funds", "issue_refund"],
        "remediation_suggestion": "Request human escalation for transactions above $5,000.",
    })
    kernel.policies.register_rule(spending_rule)
    print(f"✓ Registered policy rule: {spending_rule.rule_name}")

    # 3. Test Intent 1: Allowed ($1,200)
    intent_valid = ToolExecutionIntent(
        tool_name="transfer_funds",
        arguments={"recipient": "vendor-42", "amount": 1200.00},
        agent_id="procurement-bot-1",
        session_id="session-9910",
    )
    res_valid = kernel.verify_intent(intent_valid)
    print(f"\nIntent 1 ($1,200) -> Verdict: {res_valid.decision.value} (Latency: {res_valid.evaluation_latency_ms}ms)")
    print(f"  Reason: {res_valid.reason}")
    print(f"  Merkle Leaf Hash: {res_valid.merkle_node_hash}")

    # 4. Test Intent 2: Denied ($15,000)
    intent_denied = ToolExecutionIntent(
        tool_name="transfer_funds",
        arguments={"recipient": "vendor-99", "amount": 15000.00},
        agent_id="procurement-bot-1",
        session_id="session-9910",
    )
    res_denied = kernel.verify_intent(intent_denied)
    print(f"\nIntent 2 ($15,000) -> Verdict: {res_denied.decision.value}")
    print(f"  Reason: {res_denied.reason}")
    for viol in res_denied.violations:
        print(f"  - Invariant Violation: {viol.rule_name} (Severity: {viol.severity.value})")

    # 5. Cryptographic Proof Verification
    proof = kernel.generate_proof(intent_valid.intent_id)
    is_valid = kernel.verify_proof(proof)
    print(f"\n✓ Cryptographic Merkle Proof verified mathematically: {is_valid}")
    print(f"  Root Hash: {proof.root_hash}")

if __name__ == "__main__":
    main()

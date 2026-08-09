#!/usr/bin/env python3
"""
02_financial_agent_guard.py — Advanced Financial Guard with Capability Tokens and Shadow Balance Simulation.
"""

from aegis import AegisKernel, ToolExecutionIntent, CapabilityScope, TaintLevel
from aegis.simulation.invariants import StateInvariant
from aegis.core.types import Severity

def main():
    print("=== AegisKernel Advanced Financial Agent Guard ===")

    # Initialize Kernel with initial bank balance state
    kernel = AegisKernel()
    kernel.sandbox.set_state({
        "accounts": {
            "ACC-CORP-100": {"balance": 10000.00, "owner": "EnterpriseCorp"},
            "ACC-RETAIL-200": {"balance": 500.00, "owner": "AliceSmith"},
        }
    })

    # Mint an ephemeral capability token granting restricted transfer capabilities
    token = kernel.capabilities.mint_token(
        subject_agent_id="finance-autonomous-agent",
        session_id="session-banking-001",
        allowed_tools={"transfer_funds", "check_balance"},
        parameter_rules={
            "transfer_funds": {
                "amount": {"min": 1.0, "max": 2500.0}
            }
        },
        max_invocations=3,
        ttl_seconds=300,
    )
    print(f"✓ Minted capability token '{token.token_id}' with signed HMAC signature.")

    # Define actual tool function to execute
    def execute_bank_transfer(account_id: str, amount: float, recipient: str):
        print(f"  [EXECUTION] Transferred ${amount:.2f} from {account_id} to {recipient}")
        return {"status": "SUCCESS", "tx_id": "TX-998822", "amount": amount}

    # Attempt 1: Valid transfer within capability token constraints ($800)
    intent1 = ToolExecutionIntent(
        tool_name="transfer_funds",
        arguments={"account_id": "ACC-CORP-100", "amount": 800.0, "recipient": "vendor-A"},
        agent_id="finance-autonomous-agent",
        session_id="session-banking-001",
        capability_token_id=token.token_id,
    )
    result1, output1 = kernel.execute_guarded(intent1, lambda **kw: execute_bank_transfer(**kw))
    print(f"\nAttempt 1 -> Decision: {result1.decision.value}, Output: {output1}")

    # Attempt 2: Exceeding capability parameter limit ($4,000 > max $2,500)
    intent2 = ToolExecutionIntent(
        tool_name="transfer_funds",
        arguments={"account_id": "ACC-CORP-100", "amount": 4000.0, "recipient": "vendor-B"},
        agent_id="finance-autonomous-agent",
        session_id="session-banking-001",
        capability_token_id=token.token_id,
    )
    result2, output2 = kernel.execute_guarded(intent2, lambda **kw: execute_bank_transfer(**kw))
    print(f"\nAttempt 2 -> Decision: {result2.decision.value}, Reason: {result2.reason}")

    # Attempt 3: Unauthorized tool invocation ('delete_database_records')
    intent3 = ToolExecutionIntent(
        tool_name="delete_database_records",
        arguments={"table": "transactions"},
        agent_id="finance-autonomous-agent",
        session_id="session-banking-001",
        capability_token_id=token.token_id,
    )
    result3, output3 = kernel.execute_guarded(intent3, lambda **kw: execute_bank_transfer(**kw))
    print(f"\nAttempt 3 -> Decision: {result3.decision.value}, Reason: {result3.reason}")

    print("\n✓ Financial Guard demonstration completed successfully.")

if __name__ == "__main__":
    main()

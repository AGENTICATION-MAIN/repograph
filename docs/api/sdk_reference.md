# Aegis Python SDK Reference

The `aegis` library provides high-level SDK wrappers and decorators.

## Direct Python Usage

```python
from aegis import AegisKernel, ToolExecutionIntent, PolicyParser

kernel = AegisKernel()

intent = ToolExecutionIntent(
    tool_name="update_user_role",
    arguments={"user_id": "usr_42", "new_role": "admin"},
    agent_id="support-agent",
    session_id="session-1",
)

result = kernel.verify_intent(intent)
if result.is_allowed:
    print("Action approved:", result.merkle_node_hash)
```

## Function Guard Decorator

```python
from aegis import AegisKernel
from aegis.adapters import aegis_guard

kernel = AegisKernel()

@aegis_guard(kernel=kernel, tool_name="transfer_funds")
def transfer_funds(recipient: str, amount: float):
    # This code only executes if AegisKernel allows the intent
    return f"Transferred ${amount} to {recipient}"
```

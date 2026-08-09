# Aegis Policy DSL Specification

Aegis Policy DSL allows declarative expression of safety invariants evaluated before, during, or after agent execution.

## Syntax & JSON Structure

```json
{
  "rule_id": "UNIQUE_IDENTIFIER",
  "rule_name": "Human Readable Rule Name",
  "description": "Explains the invariant logic",
  "phase": "PRE_EXECUTION",
  "condition": {
    "and": [
      { "field": "args.amount", "op": "<=", "value": 5000 },
      { "field": "session.user_role", "op": "==", "value": "finance_admin" }
    ]
  },
  "target_tools": ["transfer_funds"],
  "action_on_violation": "DENY",
  "severity": "HIGH",
  "remediation_suggestion": "Decrease amount or request supervisor escalation."
}
```

## Supported Operators
- **Comparison**: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `contains`, `matches`, `starts_with`, `ends_with`
- **Logical**: `and`, `or`, `not`
- **Built-in Functions**: `len()`, `lower()`, `upper()`, `is_valid_email()`, `is_valid_ip()`, `ip_in_cidr()`, `has_pii()`, `clamp()`, `abs()`
- **Phases**: `PRE_REASONING`, `PRE_EXECUTION`, `POST_EXECUTION`, `TRANSACTION_COMMIT`

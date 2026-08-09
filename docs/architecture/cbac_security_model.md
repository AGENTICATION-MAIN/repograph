# Capability-Based Access Control (CBAC) Security Model

Traditional Role-Based Access Control (RBAC) fails in multi-agent environments where agents dynamically delegate sub-tasks to downstream specialized workers.

## Capability Token Lifecycle

1. **Minting**: Kernel mints a `CapabilityToken` signed with an HMAC-SHA256 secret.
2. **Attenuation**: When delegating work to a sub-agent, the parent agent calls `.attenuate()`. The child token can only have equal or narrower tool permissions, fewer remaining invocations, a shorter TTL, and a more restrictive taint ceiling.
3. **Execution Verification**: Prior to tool execution, the token signature, expiration timestamp, invocation count, tool allowance, parameter constraints, and taint ceiling are validated in $<0.2\text{ ms}$.
4. **Revocation**: Revoking any token immediately invalidates its entire descendant tree.

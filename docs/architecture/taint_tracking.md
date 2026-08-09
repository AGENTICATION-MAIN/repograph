# Dynamic Taint Tracking & Information Flow Control

A major vulnerability in autonomous agent architectures is **Indirect Prompt Injection**: an agent ingests untrusted text from the web, and the text instructs the agent to execute privileged actions (e.g. `execute_bash` or `transfer_funds`).

## Taint Levels
- `SYSTEM` (0): Trusted kernel/platform internal state.
- `AUTHENTICATED_USER` (1): Directly provided by verified human user.
- `SENSITIVE_PII` (2): Contains private customer data or tokens.
- `UNTRUSTED_EXTERNAL` (3): Web pages, scraped text, external emails, untrusted APIs.
- `MALICIOUS_ADVERSARIAL` (4): Identified prompt injection or exploit pattern.

## Sink Enforcement
Protected sinks specify the maximum allowed taint level. For instance, `execute_sql` requires `AUTHENTICATED_USER` or passing through an approved AST sanitizer. Any attempt to supply `UNTRUSTED_EXTERNAL` data without sanitization results in an automatic `DENY`.

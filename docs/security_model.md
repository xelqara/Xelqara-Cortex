# BidCore Security Model

## Trust boundary

BidCore treats imported documents as untrusted data. It does not execute macros, embedded scripts, external links, or instructions found in a document. The local model receives only the selected evidence context and the question; it is not allowed to call tools or submit forms.

## Main threats and controls

| Threat | Control |
| --- | --- |
| Prompt injection in a document | Injection detection, evidence warning, and no tool execution |
| Unsupported claim | Gap-first drafting, low confidence, human approval |
| Stale policy or report | Evidence owner, approval state, review due date, and expiry registry |
| Wrong scope match | Exact question identity, source locations, and reviewer inspection |
| Data leakage | Local-first storage, no API requirement, no customer files in public Git |
| Unauthorized review | Workspace roles and review transition checks |
| Untraceable submission | Audit events and JSON export package |
| Malicious file | File-size limits, format allowlist, no macro execution, isolated parsing |

## Production hardening still required

Before a real deployment, the customer must provide authentication, TLS/reverse proxy configuration, host patching, encrypted storage, backup and restore tests, log retention, secure deletion, dependency scanning, and a formal privacy/security review. The open-source repository is not a certification and does not itself establish compliance with SOC 2, ISO 27001, GDPR, HIPAA, or any other framework.

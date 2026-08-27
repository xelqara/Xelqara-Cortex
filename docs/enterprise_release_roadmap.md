# BidCore Enterprise Release Roadmap

BidCore is a local-first RFP and security-questionnaire response workspace. It imports customer formats, retrieves approved evidence, drafts conservative answers, routes uncertainty to owners, preserves source locations, and exports reviewable artifacts with an audit trail.

| Area | Current release | Deferred intentionally |
| --- | --- | --- |
| Evidence | Source IDs, locations, freshness registry, approvals, checksums | Dense embeddings and cross-encoder reranking until a local model is selected |
| Intake | TXT, Markdown, CSV/TSV, XLSX, DOCX, text-based PDF | Browser portals and macro execution |
| Drafting | Deterministic evidence drafts plus optional loopback local model | Autonomous submission |
| Review | Roles, state transitions, notes, audit events | Full collaborative web UI |
| Export | CSV and auditable JSON | Pixel-perfect reproduction of every proprietary workbook |
| Evaluation | 100 synthetic retrieval trials plus red-team tests | Production accuracy claims before customer-authorized data |
| Deployment | CLI, Colab, Docker, local model adapters | Managed SaaS hosting and paid connectors |

A feature is accepted only when it has a deterministic test, does not require an API key, does not execute document macros or remote instructions, and does not turn unsupported evidence into a confident answer. Production claims require a customer-authorized benchmark and a reproducible before/after measurement.

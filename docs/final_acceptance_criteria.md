# BidCore Final Acceptance Criteria

The release is accepted only when the following behavior is testable locally and in Colab.

| Area | Acceptance condition |
| --- | --- |
| Intake | TXT, Markdown, CSV/TSV, XLSX, DOCX, and text PDF import without executing macros, scripts, or external links. |
| Structure | Source file, sheet/row, paragraph, or page location remains attached to retrieved evidence. |
| Question extraction | JSON and tabular inputs preserve question IDs and ignore header rows. |
| Evidence | Each material draft exposes sources, confidence, warning state, owner/approval metadata, and freshness status where registered. |
| Safety | Prompt-like text inside documents is treated as data; unsupported questions remain low-confidence and require human input. |
| Review | Roles, review transitions, notes, reviewer identity, and audit events are persisted locally. |
| Export | CSV is usable for spreadsheet review; JSON contains provenance and audit data. |
| Local model | Ollama or an explicit local command is optional, loopback/local only, and never bypasses evidence policy or human approval. |
| Deployment | CLI, Colab, and Docker instructions work without an API key. |
| Quality | All automated tests pass; benchmark results are labeled synthetic and are not presented as production accuracy. |

This release does not claim autonomous submission, legal/compliance approval, customer data rights, or superiority over every competitor without a customer-authorized benchmark.

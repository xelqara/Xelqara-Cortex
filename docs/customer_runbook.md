# BidCore Customer Runbook

## Deployment

Run BidCore on a customer-controlled Linux host or internal workstation. Keep `.cortex/` on an encrypted disk, restrict filesystem access to the service account, and back it up according to the customer's retention policy. Do not expose the Flask interface beyond localhost without authentication, TLS, a reverse proxy, and the customer's network controls.

## First setup

Install the base package, then add spreadsheet or web extras only when needed. Create a workspace and project, ingest approved evidence, register its owner and review date, then import a customer questionnaire. Generate drafts and keep every item pending review until the accountable owner approves it.

## Data handling

Customer questionnaires, policies, audit reports, and proposals are customer-controlled confidential data. They must not be committed to GitHub, uploaded to a public notebook, or sent to a remote model. A local model adapter may be enabled only after the customer confirms the model runtime, storage, logging, and retention behavior.

## Review policy

Security, privacy, legal, product, commercial, and implementation claims must be routed to the appropriate reviewer. The system must not be used as evidence that a certification, SLA, control, or contractual promise exists. Unsupported questions must remain visible in the gap list.

## Backup and deletion

Back up the database and approved evidence according to the customer's policy. When a project ends, export the audit package, document the retention decision, and delete the working directory using the customer's approved secure deletion process.

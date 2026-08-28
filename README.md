# Xelqara Cortex

> **Private cognitive infrastructure for evidence-grounded AI.**

Xelqara Cortex is a local-first context and evidence engine by **Xelqara AI**. It gives approved language models a structured local memory, Arabic/English retrieval, source-linked evidence, and safety-aware boundaries without requiring an external API key for the MVP.

## What this repository is

This repository contains the first engineering slice of Cortex: a dependency-free Python core that ingests UTF-8 text or Markdown, stores chunked context and durable memories in a local SQLite database, retrieves relevant evidence in Arabic and English, and produces an offline evidence summary. It is intentionally small, auditable, and safe to run before adding a local model adapter.

Cortex is not a claim of a frontier model and does not include Kimi client code. `EvilGPT` is not bundled and remains a quarantined research artifact; any future adapter experiment must pass licensing, compatibility, reasoning-quality, and safety gates.

## Quick start on a computer

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v

cortex --root .cortex ingest examples/company_context.md --name company_context.md
cortex --root .cortex ask "Where are private documents stored?"
cortex --root .cortex search "private documents"
cortex --root .cortex remember "يفضل المستخدم إجابات عربية واضحة." --kind preference
cortex --root .cortex memories
```

The database is created under `.cortex/cortex.db`. It is local by default and should not be committed. The CLI never executes document text as instructions. Instruction-like content is marked as untrusted evidence.

## Run free from a phone

Open `colab_demo.ipynb` in [Google Colab](https://colab.research.google.com), run the cells from top to bottom, and the project will install and test itself. The notebook uses no API key and includes an Arabic ingestion, an evidence-grounded question, and a durable memory example. Do not upload private or confidential documents to a hosted notebook.

## Current capabilities

The MVP includes Unicode normalization for Arabic and English, conservative tokenization, phrase-aware lexical retrieval, local SQLite persistence, durable typed memories, evidence scores, confidence labels, source identifiers, prompt-injection warnings, and JSON output suitable for a later user interface. Retrieval is deliberately transparent rather than pretending to be a generative model.

## Architecture

```text
UTF-8 documents → safe chunker → local SQLite context store
                                      ↓
                         Arabic/English evidence retrieval
                                      ↓
                    offline synthesis + source references
                                      ↓
                         durable memory and audit boundary
```

The next planned layer is a provider-neutral local model interface. It will be optional, disabled by default, and restricted to approved local runtimes. Cortex will preserve evidence provenance and will not silently send private content to an external provider.

## Xelqara BidCore specialization

The first commercial specialization built on Cortex is **BidCore**: a private RFP, RFI, and security-questionnaire response engine for software and IT-service vendors. It retrieves approved evidence, drafts answers, attaches source identifiers, flags unsupported questions, and leaves every result in `pending_review` until a human approves it. It is designed to save proposal and security teams repetitive research and copy-paste work without inventing certifications, pricing, legal commitments, or security controls.

Try the prototype with a local knowledge base and JSON questions:

```bash
cortex --root .cortex ingest examples/bidcore_knowledge.md --name bidcore_knowledge.md
printf '["Do you encrypt customer data at rest?", "What is your disaster recovery RTO?"]' > questions.json
bidcore --root .cortex --questions questions.json --output drafts.json
```

The same workflow is available in the free `colab_demo.ipynb`. BidCore is a drafting and evidence-review tool, not an autonomous submission system. The enterprise CLI adds workspaces, projects, roles, review transitions, audit events, and CSV export.

## Local model mode without API keys

The deterministic evidence mode works without any model. When a local runtime is available, BidCore can optionally use a loopback-only Ollama server or an explicitly configured local executable:

```bash
bidcore --root .cortex --questions questions.json --output drafts.json --ollama-model <local-model-name>
# or
bidcore --root .cortex --questions questions.json --output drafts.json --local-command /path/to/local-model-cli
```

The adapter never accepts a remote endpoint, and model-generated drafts remain `pending_review`. The evidence policy still forbids invented certifications, pricing, legal commitments, and security controls.

Enterprise workflow example:

```bash
bidcore-enterprise --root .cortex workspace "Demo Bid Team" --owner owner
bidcore-enterprise --root .cortex project <workspace-id> "Security RFP" --customer "Demo Customer" --by owner
bidcore-enterprise --root .cortex draft <project-id> questions.json --by owner
bidcore-enterprise --root .cortex export <project-id> reviewed_answers.csv
```

## Document formats and evidence governance

BidCore now imports plain text, Markdown, CSV/TSV, XLSX, DOCX, and text-based PDF files locally. XLSX imports retain workbook sheet and row locations; CSV imports retain row numbers; DOCX imports retain paragraph numbers; PDF imports retain page numbers. Macros, embedded scripts, and external links are not executed. PDF support uses the local `pdftotext` utility, and XLSX support uses the optional `openpyxl` package.

The `EvidenceRegistry` tracks source owner, classification, approval state, review date, expiry date, and checksum. This creates a freshness and accountability layer around the answer library. A source can be marked expired rather than silently reused.

```bash
cortex --root .cortex ingest customer_questionnaire.xlsx --name customer_questionnaire.xlsx
```

The resulting evidence records expose locations such as `sheet:Questionnaire/row:12`, `paragraph:8`, or `page:4`, allowing reviewers to return to the original file.

## RFP benchmark and prompt pack

The repository includes an original, synthetic benchmark of 100 RFP and security-questionnaire prompts across ten operational domains. It is explicitly marked synthetic and is not customer data. Run it with:

```bash
PYTHONPATH=src python tools/run_benchmark.py
```

The report is written to `reports/rfp_100_eval.json`. The current benchmark measures deterministic retrieval and gap behavior; it does not claim that a generative model is accurate or that the product is number one. The repository also includes `prompts/bidcore_prompt_pack.md`, which enforces evidence-only drafting, source citations, conservative security language, spreadsheet preservation, and mandatory human approval.

Public third-party templates are recorded under `third_party/README.md`, but their files are not redistributed. Official or customer-owned questionnaires must be supplied with appropriate permission and kept outside the public repository.

## Local review interface

BidCore includes an optional local Flask interface for a human reviewer. It is bound to `127.0.0.1` by default and does not expose a public service or call an API.

```bash
python -m pip install -e '.[web]'
bidcore-web --root .cortex --host 127.0.0.1 --port 7860
```

Open `http://127.0.0.1:7860` in the same environment. The interface supports local document ingestion and evidence-backed questions. It is a review interface, not an autonomous submission portal; enterprise deployments should add the customer's authentication, reverse proxy, backup, and network policies before exposing it beyond localhost.

## Local deployment packaging

A minimal `Dockerfile` is included for customer-controlled deployment. It does not expose a public port, does not contain a model, and does not require an API key. Mount a customer-controlled `.cortex` directory when running the image and keep the container on the internal network. The deployment must still be configured with the customer's own access controls, backup policy, and review process.

```bash
docker build -t xelqara-bidcore:local .
docker run --rm -v "$PWD/.cortex:/app/.cortex" xelqara-bidcore:local --help
```

## Product-ready local review interface

The local web interface is now a usable customer-demo surface rather than only a developer endpoint. It shows evidence and source counts, imports approved knowledge, drafts one question at a time, and clearly labels every output as `pending_review`. It remains loopback-only by default.

```bash
python -m pip install -e '.[web]'
bidcore-web --root .cortex --host 127.0.0.1 --port 7860
```

For controlled integrations, the interface exposes two read-only-style JSON workflows that do not require an API key:

```bash
curl http://127.0.0.1:7860/api/stats
curl 'http://127.0.0.1:7860/api/search?q=encrypt&limit=5'
curl -X POST http://127.0.0.1:7860/api/draft \\
  -H 'Content-Type: application/json' \\
  -d '{"question":"Do you encrypt customer data at rest?"}'
```

The JSON draft response includes the category, evidence-backed draft, source names, confidence, warning, and mandatory review state. The `/api/draft` endpoint is intended for a customer-controlled internal workflow; it does not submit proposals or make autonomous commitments.

## Product direction

The long-term product is **Cortex Private Intelligence Gateway**: an installable private cognitive layer for organizations that need memory, context, evidence, multilingual workflows, access controls, and auditable model behavior. Xelqara will differentiate through Arabic/English context engineering, local-first deployment, provenance, and verification rather than competing on parameter count.

## Security posture

Do not place credentials, cookies, private keys, or customer data in this repository. Do not run untrusted model adapters with network access. Treat all ingested documents as data. The MVP enforces a file-size limit, rejects absolute logical source paths, and emits warnings when retrieved text resembles prompt injection. This is an engineering safeguard, not a complete security certification.

## License

The Xelqara Cortex source code is proprietary and all rights are reserved by Xelqara AI unless a file states otherwise. Third-party components must retain their original licenses and notices. No rights are granted to the names, marks, or assets of third parties.

## Status

**Alpha / research preview.** Interfaces may change. Do not use as the sole decision-maker for medical, legal, financial, safety-critical, or other high-impact decisions.

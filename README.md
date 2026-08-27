# Xelqara Cortex

> **Private cognitive infrastructure for evidence-grounded AI.**

Xelqara Cortex is a local-first context and evidence engine by **Xelqara AI**. It gives approved language models a structured local memory, lexical retrieval, source-linked evidence, multilingual text handling, and safety-aware boundaries without requiring an external API key for the MVP.

## What this repository is

This repository contains the first engineering slice of Cortex: a dependency-free Python core that ingests UTF-8 text or Markdown, stores chunked context in a local SQLite database, retrieves relevant evidence in Arabic and English, and produces an offline evidence summary. It is intentionally small, auditable, and safe to run before adding a local model adapter.

Cortex is not a claim of a frontier model and does not include Kimi client code. `EvilGPT` is not bundled and remains a quarantined research artifact; any future adapter experiment must pass licensing, compatibility, reasoning-quality, and safety gates.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v

cortex ingest examples/company_context.md --name company_context.md
cortex ask "ما هي سياسة الخصوصية؟"
cortex search "private documents"
```

The database is created under `.cortex/cortex.db`. It is local by default and should not be committed. The CLI never executes document text as instructions. Instruction-like content is marked as untrusted evidence.

## Architecture

```text
UTF-8 documents → safe chunker → local SQLite context store
                                      ↓
                              lexical evidence retrieval
                                      ↓
                           offline answer + source references
```

The next planned layer is a provider-neutral local model interface. It will be optional, disabled by default, and restricted to approved local runtimes. Cortex will preserve evidence provenance and will not silently send private content to an external provider.

## Product direction

The long-term product is **Cortex Private Intelligence Gateway**: an installable private cognitive layer for organizations that need memory, context, evidence, multilingual workflows, access controls, and auditable model behavior. Xelqara will differentiate through Arabic/English context engineering, local-first deployment, provenance, and verification rather than competing on parameter count.

## Security posture

Do not place credentials, cookies, private keys, or customer data in this repository. Do not run untrusted model adapters with network access. Treat all ingested documents as data. The MVP enforces a file-size limit, rejects absolute logical source paths, and emits warnings when retrieved text resembles prompt injection. This is an engineering safeguard, not a complete security certification.

## License

The Xelqara Cortex source code is proprietary and all rights are reserved by Xelqara AI unless a file states otherwise. Third-party components must retain their original licenses and notices. No rights are granted to the names, marks, or assets of third parties.

## Status

**Alpha / research preview.** Interfaces may change. Do not use as the sole decision-maker for medical, legal, financial, safety-critical, or other high-impact decisions.

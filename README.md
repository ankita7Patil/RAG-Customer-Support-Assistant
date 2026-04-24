# RAG-Based Customer Support Assistant

This project implements a customer support assistant that uses retrieval-augmented generation, a graph-style control flow, intent-based routing, and human-in-the-loop escalation.

## Features

- PDF ingestion with chunking and metadata enrichment
- Retrieval over a customer support knowledge base
- Conditional routing for `faq`, `refund`, `technical_issue`, and `human_request`
- Graph-based workflow with clear state transitions
- HITL escalation when confidence is low, context is missing, or the query is complex
- Submission-ready HLD, LLD, and technical documentation in both Markdown and PDF

## Project Structure

```text
assets/                         Sample knowledge-base PDF
data/                           Runtime vector-store directory
docs/                           HLD, LLD, technical documentation
scripts/                        PDF generation utilities
src/support_rag/                Application source code
```

## Quick Start

1. Create a virtual environment with Python 3.11+.
2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your API key if you want LLM-backed generation.
4. Build the sample PDFs:

```powershell
python scripts/build_submission_assets.py
```

5. Ingest the sample knowledge base:

```powershell
python -m src.support_rag.main ingest --pdf assets/customer_support_kb.pdf
```

6. Start the assistant:

```powershell
python -m src.support_rag.main chat
```

## Demo Flow

The assistant follows a graph-style lifecycle:

1. Input node accepts the customer query.
2. Process node classifies intent and retrieves context.
3. Output node either returns an answer or escalates to a human agent.

## Notes

- The code is written to prefer LangGraph and ChromaDB when installed.
- A lightweight local fallback is included so the project structure remains understandable even without those libraries.
- The generated PDFs are stored in `docs/pdf/`.

# High-Level Design (HLD)

## 1. System Overview

### Problem Definition
Customer support teams need a fast way to answer policy, account, delivery, and troubleshooting questions from a large knowledge base. Traditional chatbots fail when they do not have relevant context or when the request is too sensitive to automate.

### Scope
The system accepts customer questions, retrieves relevant context from a PDF knowledge base, generates or assembles a grounded answer, and escalates selected requests to a human support agent.

## 2. Architecture Diagram

```text
+------------------+      +----------------------+      +-------------------+
| User Interface   | ---> | LangGraph Workflow   | ---> | Output / HITL     |
| CLI or Web UI    |      | Input-Process-Output |      | Final Answer      |
+------------------+      +----------+-----------+      +---------+---------+
                                      |                            |
                                      v                            v
                           +----------------------+      +-------------------+
                           | Retrieval Layer      | ---> | Human Agent Queue |
                           | Top-K Context        |      | Escalation        |
                           +----------+-----------+      +-------------------+
                                      |
                                      v
                           +----------------------+
                           | ChromaDB Vector DB   |
                           | Embedded PDF Chunks  |
                           +----------+-----------+
                                      ^
                                      |
                           +----------+-----------+
                           | Ingestion Pipeline   |
                           | PDF -> Chunk -> Embed|
                           +----------------------+
```

## 3. Component Description

### User Interface
The initial submission uses a CLI interface for fast demonstration. A web UI can be added later without changing the retrieval and workflow layers.

### Document Loader
Reads the PDF knowledge base and extracts page-wise text using `pypdf`.

### Chunking Strategy
Uses fixed-size overlapping chunks to balance retrieval precision and context continuity.

### Embedding Model
Sentence-transformer embeddings are recommended for local semantic search because they provide good quality at low cost.

### Vector Store
ChromaDB is selected because it is lightweight, developer friendly, and easy to use for local RAG applications.

### Retriever
The retriever performs top-k similarity search over stored chunk embeddings and returns the most relevant context windows.

### LLM
An LLM is used to ground the final answer in retrieved context. The default design assumes a cost-efficient model such as `gpt-4o-mini`.

### Graph Workflow Engine
LangGraph orchestrates the query lifecycle, state transitions, and conditional routing.

### Routing Layer
The routing logic classifies intent, checks retrieval confidence, and decides whether the system should answer or escalate.

### HITL Module
The HITL module hands off complex or low-confidence queries to a human support agent and stores the escalation reason.

## 4. Data Flow

1. PDF knowledge base is loaded.
2. Text is split into chunks with overlap.
3. Chunks are embedded and stored in ChromaDB.
4. Customer query enters the system.
5. Workflow classifies intent and retrieves top-k chunks.
6. LLM composes a grounded answer from retrieved context.
7. Routing logic returns the answer or escalates to HITL.

## 5. Technology Choices

- ChromaDB: Simple local vector store with persistent collections
- LangGraph: Explicit stateful workflow for node-based routing
- `pypdf`: Reliable PDF text extraction
- Sentence Transformers: Practical embedding generation
- Python CLI: Fastest way to demonstrate the system in a review setting

## 6. Scalability Considerations

### Large Documents
Multiple PDFs can be ingested by storing document metadata and creating document-aware retrieval filters.

### Increasing Query Load
The retriever and LLM layers can be separated into independent services and cached for frequent queries.

### Latency
Latency can be reduced through smaller embeddings, retriever caching, and asynchronous HITL handoff.

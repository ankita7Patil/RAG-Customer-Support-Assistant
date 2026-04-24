# Technical Documentation

## 1. Introduction

Retrieval-Augmented Generation (RAG) is a design pattern where an LLM retrieves external knowledge at query time before producing an answer. This improves factual grounding, reduces hallucination, and makes customer support responses traceable to a source document.

This project applies RAG to a customer support assistant that reads a PDF knowledge base, stores chunk embeddings, retrieves relevant context, routes queries through a workflow, and escalates difficult cases to a human agent.

## 2. System Architecture Explanation

The system has two main phases:

1. Offline ingestion
2. Online question answering

During ingestion, the PDF is parsed, split into chunks, embedded, and stored in the vector database. During question answering, the query is classified, the retriever fetches the most relevant chunks, and the workflow decides whether to answer automatically or escalate.

## 3. Design Decisions

### Chunk Size
The design uses roughly 700-character chunks with overlap. This is small enough for retrieval precision while still preserving the meaning of policy sections and troubleshooting steps.

### Embedding Strategy
A local sentence-transformer is recommended because it balances semantic quality, privacy, and cost.

### Retrieval Approach
Top-k semantic search is sufficient for the internship use case. Metadata-aware filtering can be added later for multi-document deployments.

### Prompt Design Logic
The prompt should instruct the LLM to:
- use only retrieved context
- cite the source when possible
- avoid inventing unsupported policy details
- escalate when the answer is unclear

## 4. Workflow Explanation

LangGraph is used because the application is not a simple linear chain. The system needs explicit state, branching decisions, and future extensibility.

### Node Responsibilities
- Input node: receives the raw customer message
- Process node: detects intent, retrieves context, scores confidence, drafts answer
- Output node: returns a final response or routes to HITL

### State Transitions
The state carries the query, intent, retrieved chunks, answer, confidence, and route decision.

## 5. Conditional Logic

Intent detection is a lightweight first-pass classifier that recognizes refund, FAQ, technical issue, and human-request patterns.

Routing decisions are based on:
- confidence score
- presence of relevant context
- complexity of the issue
- explicit user request for a human

## 6. HITL Implementation

Human intervention is an important reliability control. It prevents unsafe auto-replies in situations such as billing disputes, unresolved technical issues, or ambiguous policy questions.

### Benefits
- improves trust
- reduces incorrect automated resolutions
- gives a safe path for exception handling

### Limitations
- increases response time
- requires agent availability
- needs a queueing or ticket system in production

## 7. Challenges & Trade-offs

### Retrieval Accuracy vs Speed
Larger embedding models improve semantic quality but increase indexing and query latency.

### Chunk Size vs Context Quality
Large chunks preserve context but may reduce precision. Smaller chunks improve targeting but can lose policy continuity.

### Cost vs Performance
Higher-end LLMs provide stronger reasoning, but cost more per query. A support bot often benefits from a smaller default model with escalation for difficult cases.

## 8. Testing Strategy

### Test Approach
- test ingestion with a known PDF
- validate chunk counts
- run sample queries for each intent
- verify that low-confidence queries escalate

### Sample Queries
- "How long do refunds take?"
- "My login keeps failing after password reset."
- "I want to speak to a human agent."
- "Do you offer express delivery?"

## 9. Future Enhancements

- multi-document collections
- conversation memory
- feedback loop for answer quality
- admin dashboard for escalations
- deployment as a web service with authentication

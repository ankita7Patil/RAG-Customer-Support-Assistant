# Low-Level Design (LLD)

## 1. Module-Level Design

### Document Processing Module
Reads the PDF, extracts text page by page, and forwards raw text for chunking.

### Chunking Module
Applies fixed-size chunking with overlap. Each chunk stores:
- `chunk_id`
- `source`
- `page_number`
- `text`

### Embedding Module
Transforms chunk text into vector embeddings. In the target design, sentence-transformer embeddings are written into ChromaDB.

### Vector Storage Module
Stores vectors and chunk metadata. Supports `add()` and `search()` operations.

### Retrieval Module
Receives the user query, searches the vector store, and returns ranked chunks with scores.

### Query Processing Module
Detects intent, formats prompt inputs, estimates confidence, and prepares the final answer.

### Graph Execution Module
Maintains the state object and routes execution through input, process, and output nodes.

### HITL Module
Triggers escalation and formats the handoff payload for a human support agent.

## 2. Data Structures

### Document Representation

```json
{
  "document_id": "customer_support_kb",
  "source": "customer_support_kb.pdf",
  "pages": 6
}
```

### Chunk Format

```json
{
  "chunk_id": "customer_support_kb-p2-c3",
  "source": "customer_support_kb.pdf",
  "page_number": 2,
  "text": "Refunds are processed within 5-7 business days..."
}
```

### Embedding Structure

```json
{
  "chunk_id": "customer_support_kb-p2-c3",
  "vector": [0.018, -0.093, 0.211]
}
```

### Query-Response Schema

```json
{
  "query": "How long do refunds take?",
  "intent": "refund",
  "confidence": 0.82,
  "route": "answer",
  "answer": "Refunds are processed within 5-7 business days."
}
```

### Graph State Object

```json
{
  "query": "",
  "intent": "unknown",
  "retrieved_chunks": [],
  "answer": "",
  "confidence": 0.0,
  "route": "answer",
  "escalated": false,
  "escalation_reason": ""
}
```

## 3. Workflow Design (LangGraph)

### Nodes
- `input_node`: accepts the raw user query
- `process_node`: classifies intent, retrieves context, builds answer, computes confidence
- `output_node`: returns final answer or HITL escalation payload

### Edges
- `START -> input_node`
- `input_node -> process_node`
- `process_node -> output_node`

### Conditional Routing
The `process_node` sets `route` to either `answer` or `escalate` before execution reaches the output node.

## 4. Conditional Routing Logic

Answer when:
- relevant chunks exist
- confidence is above threshold
- query is low risk

Escalate when:
- confidence is below threshold
- no useful chunks are found
- user explicitly asks for a human
- query is complex or account sensitive

## 5. HITL Design

### Trigger
The system raises escalation for low confidence, ambiguous intent, sensitive queries, or explicit human requests.

### Post-Escalation Flow
The escalation payload includes the user query, detected intent, retrieved context, confidence score, and escalation reason.

### Human Integration
The support agent reviews the payload and responds through the same ticket or conversation channel.

## 6. API / Interface Design

### Input

```json
{
  "query": "My payment failed twice. Can someone help?"
}
```

### Output

```json
{
  "intent": "technical_issue",
  "route": "escalate",
  "message": "This query has been escalated to a human support agent."
}
```

## 7. Error Handling

- Missing PDF: reject ingestion and log a file error
- Empty pages: skip silently and continue
- No relevant chunks: return fallback response and escalate
- LLM failure: degrade to retrieval-only answer or escalate

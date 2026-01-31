# EXP-005 Results: Vector Embeddings vs. Graph Store

## Experiment Goal
Compare the effectiveness of Vector Embeddings (semantic search) against a Property Graph for retrieving context for open-ended user queries.

## Setup
- **Query**: "How has my mood changed since I started my job?"
- **Data**: A user profile with job info ("Engineer") and mood ("Happy"), plus journal-like entries.
- **Methods**:
    1.  **Vector Store**: Mock embeddings (cosine similarity) on text chunks.
    2.  **Graph Store**: Directed property graph (nodes/edges).

## Results

### Graph Store
*   **Input**: Extracted entities `["User", "Mood", "Job"]`.
*   **Output**:
    *   `User HAS_JOB Engineer`
    *   `User HAS_MOOD Happy`
*   **Observation**: The graph returned explicit facts connected to the user. It failed to capture the *narrative* of change or the causal link between the job and mood found in the text. It requires strict ontology matching.

### Vector Store
*   **Input**: Raw query string.
*   **Output**:
    1.  "I feel really happy about the work environment."
    2.  "My mood has improved since starting work."
    3.  "I started my new job as an Engineer last month."
*   **Observation**: Vector search successfully retrieved relevant unstructured context based on semantic overlap (mood, job, work, happy). It surfaced the "improvement" which was not an explicit node in the graph.

## Conclusion
Vector embeddings are superior for **fuzzy, narrative, or unstructured retrieval tasks** where the relationship isn't a strict edge type. Graph stores are better for precise fact lookups, but rigid for broad "how/why" questions without highly sophisticated extraction logic.

Future work should explore **Hybrid Search** (Graph for entities + Vector for context).

# Omniscient - Risk Assessment & Mitigation Strategy

**Status**: Reviewed & Updated with User Feedback
**Related Roadmap**: [Milestones & Issues](milestones_and_issues.md)

## 1. Temporal Relevance & Stale Data
*   **Risk Level**: Medium
*   **The Problem**: Facts change (e.g., "User is in NY" vs "User is in London"). Graph retains old info.
*   **User Feedback**: "For now we are aiming for eventual consistency not consistency."
*   **Mitigation Strategy**:
    *   Accept eventual consistency.
    *   **Experiment**: [EXP-002] Implement a simple "latest write wins" or timestamp-based valid_at field, but do not block reads for strict consistency.

## 2. Concurrency & Write Scalability
*   **Risk Level**: Medium
*   **The Problem**:
    1.  Expensive updates (Read-Traverse-Write).
    2.  **Stalemate**: Two agents updating the same nodes simultaneously.
*   **User Feedback**: "There are 2 problems... expensive updates and... stale mate." "We are experimenting and we are going to update this in future."
*   **Mitigation Strategy**:
    *   **Experiment**: [EXP-003] Run stress tests with concurrent agents to quantify how often "Stalemates" actually occur in our specific use case. If rare, optimistic locking is sufficient.

## 3. Schema Evolution vs. Data Structure
*   **Risk Level**: High
*   **The Problem**: Fixed graph schemas can be rigid. Migrations are painful.
*   **User Feedback**: "We want to structure data as much as possible. If that is problem we can re-think... maybe graph is not a correct way to store data on a person."
*   **Mitigation Strategy**:
    *   **CRITICAL EXPERIMENT**: [EXP-001] Compare Graph DB vs. Structured Document Store for "Person Context".
    *   *Hypothesis*: A hybrid approach might be best (Graph for loose connections, Doc Store for rigid "Profile" data).

## 4. Entity Resolution (Identity Management)
*   **Risk Level**: High
*   **The Problem**: Duplicating nodes (Apple fruit vs Apple company).
*   **User Feedback**: "Agent updates the memory after responding to user so it has understanding of context... bigger llm can easily fix this problem."
*   **Mitigation Strategy**:
    *   **Shift Responsibility**: Move resolution "left" to the Agent/Ingestion time.
    *   **Experiment**: [EXP-004] Test if a "Bigger LLM" (e.g., Gemini 1.5 Pro) can accurately canonicalize entities given the full conversation context *before* the graph update request is even formed.

## 5. Privacy & Security (Prompt Injection)
*   **Risk Level**: Critical (Accepted for MVP)
*   **The Problem**: Malicious instructions stored in memory.
*   **User Feedback**: "For now we take that as a risk and hope that LLM prompt injection will be solved in future agents."
*   **Mitigation Strategy**:
    *   **Accept Risk**: Acknowledge this is a known vulnerability.
    *   **Monitor**: [SEC-001] Keep a watch on industry solutions for output sanitization.

## 6. Graph Pollution (Hallucinations)
*   **Risk Level**: Critical
*   **The Problem**: Bad data in = Bad memory forever.
*   **Mitigation Strategy**:
    *   Trust Scores: Each node has a `confidence` metadata field.

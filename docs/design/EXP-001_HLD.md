# EXP-001 High-Level Design: Graph vs. Document Store

## 1. Objective
Determine the optimal data structure for storing "User Context" (facts, relationships, history) to support an LLM Agent.
*   **Hypothesis**: A Document Store (JSON) is sufficient for 90% of queries and faster/cheaper to maintain. A Graph is only needed if "Multi-hop" discovery (e.g., "How is Sam connected to the CEO of Amazon?") is a core requirement.

## 2. The Contenders

### Candidate A: Document Store (The Baseline)
*   **Technology**: SQLite (using JSONB) or a simple JSON file system.
*   **Structure**:
    ```json
    {
      "entity": "Sam",
      "attributes": {
        "location": "Seattle",
        "job": { "role": "SDE", "company": "Amazon" }
      },
      "relationships": [
        { "type": "friend_of", "target": "Alice" }
      ]
    }
    ```
*   **Pros**: Fast writes, human-readable, simple schema evolution.
*   **Cons**: "Find friends of friends" requires loading/scanning everything.

### Candidate B: Graph Store (The Challenger)
*   **Technology**: NetworkX (Python in-memory graph) for prototyping. (Proxies Neo4j).
*   **Structure**:
    *   Nodes: `[Sam]`, `[Seattle]`, `[Amazon]`, `[SDE]`.
    *   Edges: `(Sam)-[:LIVES_IN]->(Seattle)`, `(Sam)-[:WORKS_AT]->(Amazon)`.
*   **Pros**: Explicit relationships, powerful traversal queries.
*   **Cons**: Complex write logic (must update edges & nodes), higher overhead.

## 3. The Experiment Plan

We will build a Python test harness (`tests/exp001/benchmark.py`) that implements a common Interface `ContextStore` for both backends.

### Test Case 1: The "Life Update" (Write)
*   **Scenario**: User says "I moved from Seattle to NYC."
*   **Doc**: Update `user.attributes.location` = "NYC". (O(1))
*   **Graph**: Delete `[:LIVES_IN]` edge to `[Seattle]`. Create/Find `[NYC]` node. Create `[:LIVES_IN]` edge to `[NYC]`.
*   **Metric**: Lines of Code (LOC) complexity + Execution Time.

### Test Case 2: The "Context Dump" (Read for LLM)
*   **Scenario**: User asks "Where do I work?"
*   **Doc**: Fetch user JSON. Dump `job` object.
*   **Graph**: Query neighbors of `[Sam]` with edge `[:WORKS_AT]`.
*   **Metric**: Latency + Token Count of serialization (Which format is denser?).

### Test Case 3: The "Discovery" (Multi-hop)
*   **Scenario**: "Do I know anyone living in the same city as my brother?"
*   **Doc**:
    1. Fetch Brother.
    2. Get Brother's City.
    3. Scan ALL users to find match on City.
*   **Graph**: `(Me)-[:BROTHER]->(Bro)-[:LIVES_IN]->(City)<-[:LIVES_IN]-(Friend)`.
*   **Metric**: Query Latency (expecting Graph to win massive here).

## 4. Success Criteria
*   If **Doc** handles Test 1 & 2 significantly better/easier, and Test 3 is deemed "Rare", we choose **Doc**.
*   If **Graph** is required for Test 3 to even be *possible* at scale, we choose **Graph**.

## 5. Refined Tasks
1.  **Scaffold**: Create `ContextStore` ABC (Abstract Base Class).
2.  **Impl**: Build `JsonStore` and `NetworkXStore`.
3.  **Bench**: Run the 3 Test Cases with a synthetic dataset (1k users).
4.  **Report**: Markdown table comparing results.

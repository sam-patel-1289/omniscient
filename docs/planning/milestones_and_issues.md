# Omniscient - Experiments Roadmap

This document structures our Risk Mitigation strategy into specific **GitHub Milestones** (Experiments). Each Milestone contains a list of **Issues** (Tasks) required to execute the experiment, along with a concrete **Scenario** to test.

---

## Milestone: [EXP-001] Data Structure Battle: Graph vs. Document
**Goal**: Determine if a Graph DB is necessary for "Person Context" or if a structured Document store (JSON) is more efficient/flexible.

**Scenario / Test Case**:
> User says: "I moved to **Seattle** last month because I joined **Amazon** as a **SDE**."
> Later: "I hate my commute to **SLU**."

*   **Graph Approach**:
    *   Nodes: `(Person:Sam)`, `(City:Seattle)`, `(Company:Amazon)`, `(Job:SDE)`, `(Location:SLU)`.
    *   Edges: `[:LIVES_IN]`, `[:WORKS_AT]`, `[:HAS_ROLE]`, `[:COMMUTES_TO]`.
*   **Document Approach**:
    *   JSON: `{ "location": "Seattle", "employer": "Amazon", "job_title": "SDE", "commute_destination": "SLU" }`.

**Issues to Close**:
- [ ] **Issue #1**: Implement `GraphProfileStore` prototype using Neo4j/NetworkX.
- [ ] **Issue #2**: Implement `DocProfileStore` prototype using MongoDB/PostgresJSON.
- [ ] **Issue #3**: Run "Schema Evolution" test. Add a new field "Remote Status" to existing 10k records in both. Measure time/effort.
- [ ] **Issue #4**: Run "Complex Query" test. "Find all users who are SDEs living in Seattle working for Amazon". Measure query latency.

---

## Milestone: [EXP-002] Eventual Consistency Pipeline
**Goal**: Verify that a high-latency, asynchronous "Queue-based" architecture is acceptable for user memory.

**Scenario / Test Case**:
> **T+0s**: Agent A sends update: "User is **Happy**".
> **T+1s**: Agent B sends query: "What is user's mood?" (Should get "Unknown" or "Old State", not fail).
> **T+5s**: Queue processes update.
> **T+6s**: Agent C sends query: "What is user's mood?" (Should get "Happy").

**Issues to Close**:
- [ ] **Issue #5**: Setup Message Queue (RabbitMQ/Redis) and Worker service stub.
- [ ] **Issue #6**: Implement "Shadow Update" mechanism. (Agent continues working immediately after sending update, without waiting for DB confirmation).
- [ ] **Issue #7**: Measure "Consistency Lag". How many seconds between "Event Happened" and "Memory Updated" under load?

---

## Milestone: [EXP-003] The "Stalemate" Concurrency Stress Test
**Goal**: Ensure data isn't corrupted when multiple agents write to the same node simultaneously.

**Scenario / Test Case**:
> **Context**: 5 separate Agents all observe the user visiting a website and try to update the `visit_count` property on the `(User)` node simultaneously.
> **Expected**: `visit_count` increases by 5.
> **Failure Mode**: `visit_count` increases by 1 (Lost Updates) or DB locks up.

**Issues to Close**:
- [ ] **Issue #8**: Create `SpamAgent` script that fires 100 concurrent updates to a single Node ID.
- [ ] **Issue #9**: Implement Optimistic Locking (version numbers on nodes).
- [ ] **Issue #10**: Implement "Retry with Backoff" logic in the Worker service for `VersionConflict` errors.

---

## Milestone: [EXP-004] Entity Resolution "Shift Left"
**Goal**: Test if using the Agent's context window for entity resolution is better than a backend graph algorithm.

**Scenario / Test Case**:
> **Conversation 1**: "I love **Jaguar** (the car)." -> Agent Context knows it's a car.
> **Conversation 2**: "I saw a **Jaguar** (the animal) at the zoo." -> Agent Context knows it's an animal.
> **Backend**: Without context, the DB sees two "Jaguar" labels and might merge them if not careful.

**Issues to Close**:
- [ ] **Issue #11**: Create a dataset of ambiguity (Apple co vs fruit, Jaguar car vs animal, Python code vs snake).
- [ ] **Issue #12**: Implement "Pre-computation" Prompt. Agent outputs: `Entity{id="jaguar_car_v1", type="Car", name="Jaguar"}` vs `Entity{id="jaguar_animal_v1", type="Animal", name="Jaguar"}`.
- [ ] **Issue #13**: Compare accuracy of "Pre-computed IDs" vs "Backend Fuzzy Matching".

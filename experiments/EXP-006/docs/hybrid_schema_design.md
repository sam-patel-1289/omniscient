# EXP-006: Hybrid Schema Design

## Overview
This experiment compares two hybrid architectures for storing complex human context:

1. **Graph + Vector DB** (Approach A)
2. **Graph + Document DB** (Approach B)

Both approaches use a Graph DB as the "source of truth" for structured relationships, paired with a secondary store for different purposes.

---

## The Problem

Storing human context is challenging because:
- **Complexity**: Humans have identity, emotions, values, goals, relationships — all interconnected
- **Evolution**: Context changes constantly (mood, location, goals)
- **Retrieval Needs**: Sometimes we need exact lookups, sometimes semantic similarity

No single database excels at all of these.

---

## Approach A: Graph + Vector DB

### Philosophy
- **Graph**: Stores structured facts, relationships, and current state ("The Truth")
- **Vector**: Stores unstructured content, embeddings for semantic search ("The Evidence")

### Data Flow
```
Raw Input → Vector DB (store chunk + embedding)
         → LLM Extractor → Graph DB (extract entities/relationships)
```

### When to Use Each
| Query Type | Store | Example |
|------------|-------|---------|
| "Who is Sam's boss?" | Graph | Traverse relationship |
| "What was Sam frustrated about last week?" | Vector | Semantic search |
| "Does Sam value minimalism?" | Graph | Node property lookup |
| "Find similar conversations to this one" | Vector | Embedding similarity |

### Conflict Resolution
**Rule**: If Vector and Graph contradict, **Graph wins**.

Graph is the "Driver's License" (current facts), Vector is the "Journal" (historical evidence).

---

## Approach B: Graph + Document DB

### Philosophy
- **Graph**: Stores relationships and entity connections
- **Document DB**: Stores rich entity profiles as JSON documents

### Data Flow
```
Raw Input → LLM Extractor → Graph DB (relationships only)
                         → Document DB (entity profiles/attributes)
```

### When to Use Each
| Query Type | Store | Example |
|------------|-------|---------|
| "Who is Sam's boss?" | Graph | Traverse relationship |
| "What are all of Sam's preferences?" | Document | Fetch profile doc |
| "Find people who work at Amazon" | Graph | Node query |
| "Get Sam's complete context" | Document | Single doc fetch |

### Conflict Resolution
Document DB is the single source for entity attributes. Graph only stores edges.

---

## Unified Schema

Both approaches share a common Graph schema:

### Graph Nodes (Both Approaches)
```
Person { id, name }
Organization { id, name }
Goal { id, title, status }
Value { id, name }
Event { id, timestamp, type }
Topic { id, name }
Emotion { id, name, intensity }
```

### Graph Edges (Both Approaches)
```
(Person)-[:WORKS_AT]->(Organization)
(Person)-[:REPORTS_TO]->(Person)
(Person)-[:HAS_GOAL]->(Goal)
(Person)-[:HOLDS_VALUE]->(Value)
(Person)-[:PARTICIPATED_IN]->(Event)
(Person)-[:KNOWS_ABOUT]->(Topic)
(Person)-[:FEELS]->(Emotion) // timestamped
(Goal)-[:BLOCKED_BY]->(Goal)
(Event)-[:RELATED_TO]->(Goal)
```

### Secondary Store Schemas

#### Approach A: Vector Store (ChromaDB)
```json
{
  "id": "chunk_uuid",
  "content": "Raw text or summary",
  "embedding": [float...],
  "metadata": {
    "timestamp": "ISO8601",
    "source": "slack|email|voice",
    "entity_ids": ["person_1", "goal_2"],
    "dimension": "episodic|communication|psychographic"
  }
}
```

#### Approach B: Document Store (MongoDB/PostgreSQL JSONB)
```json
{
  "entity_id": "person_sam",
  "type": "Person",
  "profile": {
    "identity": {
      "name": "Sam",
      "role": "Architect",
      "location": "NYC"
    },
    "values": ["minimalism", "speed"],
    "preferences": {
      "communication": "async",
      "design_style": "dark_mode"
    },
    "current_state": {
      "energy": "low",
      "mood": "focused",
      "updated_at": "ISO8601"
    }
  },
  "history": [
    {"field": "location", "old": "SF", "new": "NYC", "at": "ISO8601"}
  ]
}
```

---

## Comparison Criteria

| Criterion | Description | Weight |
|-----------|-------------|--------|
| **Write Latency** | Time to persist new context | Medium |
| **Query Flexibility** | Ability to answer diverse questions | High |
| **Semantic Search** | Finding "similar" or "related" content | High |
| **Schema Evolution** | Ease of adding new fields/relationships | High |
| **Consistency** | Keeping data in sync across stores | Medium |
| **Complexity** | Implementation & maintenance burden | Medium |

---

## Test Scenarios

### Scenario 1: The Value Inference
> User says: "I hate this cluttered design"
> 
> **Task**: AI should infer this relates to "minimalism" value

- **A (Vector)**: Semantic search for "cluttered" → finds similar chunks → LLM infers value
- **B (Document)**: Must have explicit mapping in profile

### Scenario 2: The State Change
> User moved from SF to NYC

- **A (Vector)**: Append new chunk, Graph update
- **B (Document)**: Update document profile, add to history array

### Scenario 3: The Relationship Query
> "Who does Sam report to, and is that person happy?"

- **A**: Graph traversal → get boss → Vector search for boss's mood
- **B**: Graph traversal → get boss → Document lookup for boss's current_state

### Scenario 4: The Fuzzy Search
> "What was Sam working on around October?"

- **A (Vector)**: Natural fit — semantic search with date filter
- **B (Document)**: Must query history arrays or separate events collection

---

## Hypothesis

**Approach A (Graph + Vector)** will excel at:
- Semantic/fuzzy queries
- Handling unstructured input
- Time-range searches

**Approach B (Graph + Document)** will excel at:
- Fast profile lookups
- Structured attribute updates
- Simpler consistency model

**Expected Winner**: Approach A for "personal intelligence" use case, because human context is inherently messy and benefits from semantic search.

---

## Next Steps
1. Implement `HybridStoreA` (Graph + Vector) prototype
2. Implement `HybridStoreB` (Graph + Document) prototype
3. Run benchmark suite against test scenarios
4. Document results

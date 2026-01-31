# EXP-001 Findings: Graph vs Doc Store

## Strategy: User Perspective
We compared a simple JSON List Store (Documents) vs. a custom Graph Store (Nodes/Edges) on a 3-sentence story.

## Experiment
- **Story**: 
  1. "My sister lives in Austin."
  2. "I'm visiting the capital of Texas."
  3. "I bought coffee at Starbucks."
- **Query 1 (Recall)**: "Where did I get coffee?"
- **Query 2 (Inference)**: "Who am I visiting in Texas?"

## Results

| Feature | JSON Store (Doc) | Graph Store (Network) |
| :--- | :--- | :--- |
| **Recall (Coffee)** | ✅ **Clean**: "I bought coffee at Starbucks." | ⚠️ **Noisy**: Returned "Starbucks" but also "visiting Austin" (due to 'Me' node). |
| **Inference (Visiting)** | ❌ **Limited**: "I'm visiting the capital of Texas." (Missed 'Sister' context). | ⚠️ **Promising but Shallow**: Retrieved "Austin" (via Texas). Missed 'Sister' in 1-hop, but reachable in 2-hop. |
| **Noise Level** | Low (Exact keyword match) | High (Hub nodes like 'Me' pull in unrelated facts) |

## Analysis
1.  **Hub Node Problem**: The Graph Store suffered from the "Super Node" issue. Querying "Me" retrieved every action I took, making the result noisy for specific questions.
2.  **Inference Gap**: The JSON store failed to connect "Texas" -> "Austin" -> "Sister". The Graph store successfully connected "Texas" -> "Austin", creating the *possibility* of finding "Sister" with a 2-hop traversal.
3.  **Readability**: JSON returns full sentences (easier for LLM to parse). Graph returns triples (fragmented).

## Recommendation
**Hybrid Approach Required.**
- Pure Graph is too noisy without advanced ranking (PageRank/Degree normalization).
- Pure Doc Store misses connections.
- **Proposed Architecture**: Use Graph for *Navigation/Entity Resolution* (Texas -> Austin), then use Doc Store for *Content Retrieval*.

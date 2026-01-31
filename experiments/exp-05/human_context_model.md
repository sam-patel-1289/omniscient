# Human Context Data Model: The "Idea Machine"

## Overview
To assist a human ("Idea Machine") effectively, the AI ("Implementation Machine") must bridge the gap created by low-bandwidth language. It needs to understand the human's *implicit* context, values, and state, not just their *explicit* commands.

This document defines the dimensions of human context we will simulate and store in Experiment 05.

## 1. The Dimensions of Context

We classify context into 6 distinct layers (Dimensions):

### D1: The Identity Layer (Static)
*   **Definition**: Who the user is. Rare updates.
*   **Attributes**: Name, Role, Location, Demographics.
*   **Example**: `{"name": "Sam", "role": "Architect", "location": "NYC"}`

### D2: The Episodic Layer (Time-Series)
*   **Definition**: What the user *did* or *experienced*. Strictly chronological.
*   **Attributes**: Event Type, Timestamp, Participants, Location.
*   **Example**: `{"timestamp": "2023-10-27T14:00:00", "event": "Meeting", "participants": ["Bob", "Alice"]}`

### D3: The Communication Layer (Interface)
*   **Definition**: The raw inputs/outputs. The "Surface" data.
*   **Attributes**: Channel (Email/Slack/Voice), Content, Sender/Receiver.
*   **Example**: `{"channel": "Slack", "message": "I hate this design, it's too cluttery.", "from": "Sam"}`

### D4: The Psychographic Layer (Internal State)
*   **Definition**: The hidden variables driving behavior.
*   **Attributes**:
    *   **Emotions**: Joy, Frustration, Anxiety (Transient).
    *   **Values**: Frugality, Aesthetics, Speed, Privacy (Persistent).
    *   **Energy**: High/Low (Physiological).
*   **Example**: `{"current_mood": "Frustrated", "value_violated": "Minimalism"}`

### D5: The Semantic Layer (Knowledge Graph)
*   **Definition**: The user's specific worldview and facts.
*   **Attributes**: Entity Relationships, Opinions, Preferences.
*   **Example**: `(Sam)-[:PREFERS]->(Dark Mode)`, `(Sam)-[:KNOWS]->(Python)`

### D6: The Intent Layer (The "Idea")
*   **Definition**: Active goals and projects. The "Why".
*   **Attributes**: Project Name, Status, Goal Description, Constraints.
*   **Example**: `{"goal": "Redesign Homepage", "constraint": "Must load in <1s", "status": "In Progress"}`

---

## 2. Schema Designs

### A. Vector Document Schema (JSON)
For the Vector Store, we will flatten these dimensions into rich text "chunks" with metadata.

```json
{
  "id": "uuid",
  "content": "Sent a Slack message to Bob: 'I hate this design, it's too cluttery.'",
  "metadata": {
    "timestamp": "2023-10-27T14:00:00",
    "type": "Communication",
    "sentiment": "Negative",
    "entities": ["Bob", "Design"],
    "implied_value": "Minimalism",
    "related_goal": "Redesign Homepage"
  },
  "embedding": [0.12, -0.45, ...]
}
```

### B. Graph Schema (Nodes & Edges)
For the Graph Store, we explicate the relationships.

**Nodes**:
*   `Person` (Sam)
*   `Event` (Meeting_1027)
*   `Message` (Msg_55)
*   `Value` (Minimalism)
*   `Goal` (Homepage_Redesign)
*   `Emotion` (Frustration)
*   `Topic` (Design)

**Edges**:
*   `(Person)-[:SENT]->(Message)`
*   `(Message)-[:MENTIONED]->(Topic)`
*   `(Message)-[:EXPRESSES]->(Emotion)`
*   `(Person)-[:HOLDS_VALUE]->(Value)`
*   `(Message)-[:IMPLIES_VALUE]->(Value)`
*   `(Event)-[:RELATED_TO]->(Goal)`
*   `(Person)-[:PARTICIPATED_IN]->(Event)`

## 3. The "Gap" Test
To test the "Idea Machine" theory, our synthetic data will generate scenarios where:
1.  **Implicit Constraint**: User has a value "Minimalism".
2.  **Explicit Action**: User critiques a design without saying "make it minimal".
3.  **Task**: AI must retrieve the `Value` node/vector to understand *why* the user critiqued it.

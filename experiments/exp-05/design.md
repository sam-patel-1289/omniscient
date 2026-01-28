# EXP-05: Vector Embeddings for Emotions & Life Context - Design Doc

## 1. Introduction
The goal of this experiment is to design a datastore for collecting complex human context (emails, messages, conversations, emotions) to help AI agents understand users better. This document outlines what needs to be recorded, the recommended technology stack, and the strategy for ensuring eventual consistency.

## 2. What to Record (Data Schema)
To capture a "complex human being," we need to store various types of unstructured interaction data. We propose a unified **Context Event** schema.

### Core Fields
*   **`id`**: Unique identifier (UUID).
*   **`user_id`**: The human user this data belongs to.
*   **`timestamp`**: UTC timestamp of the event.
*   **`type`**: The category of data.
    *   `email`: Email content and headers.
    *   `message`: Chat messages (Slack, SMS, Discord).
    *   `conversation`: Transcribed audio from meetings or voice notes.
    *   `emotion`: Detected emotional state (e.g., "Frustrated", "Joyful") derived from other content or sensors.
    *   `observation`: Agent observations (e.g., "User is working late").
*   **`content`**: The raw text content.
*   **`metadata`**: JSON object for type-specific details.
    *   *Email*: `subject`, `sender`, `recipients`.
    *   *Message*: `platform`, `channel_id`.
    *   *Emotion*: `confidence_score`, `trigger_event_id`.
*   **`embedding`**: Vector representation (float array) of the `content` + relevant `metadata`.

## 3. Technology Selection: Vector DB vs. Graph DB

### Comparison
| Feature | Graph Database (Neo4j) | Vector Database (Chroma/Pinecone) |
| :--- | :--- | :--- |
| **Data Structure** | Nodes & Edges (Structured) | High-dimensional Vectors (Unstructured) |
| **Query Style** | Exact relationships ("Who is Sam's boss?") | Semantic similarity ("How was Sam feeling yesterday?") |
| **Setup Effort** | High (Requires schema & ontology design) | Low (Chunk text -> Embed -> Store) |
| **Nuance Capture**| Low (Must discretize emotions to nodes) | High (Captures subtle semantic differences) |

### Recommendation
For the purpose of "collecting complex human being... anything from email, message to listen to conversation and emotions," a **Vector Database** is significantly better.
*   **Why?**: Human communication is messy and unstructured. Defining a strict graph ontology for every possible emotion or conversation topic is brittle. Vector embeddings naturally capture the semantic meaning of text, allowing the AI to retrieve relevant context based on *meaning* rather than exact keyword matches.
*   **Tools**:
    *   **ChromaDB**: Excellent for local development and embedded python apps.
    *   **Pinecone/Milvus**: Good for managed cloud scale.
    *   **Weaviate**: Offers hybrid search (Vector + Keyword), which is a strong plus.

*Recommendation for Experiment:* **ChromaDB** (or a local simulation) for simplicity and python integration.

## 4. Eventual Consistency Strategy

To ensure system reliability and responsiveness, we should not block the user interface while calculating embeddings (which can be slow) or writing to the database. We adopt an **Eventual Consistency** model using an asynchronous ingestion pipeline.

### Architecture
1.  **Client/Agent**: Captures data (e.g., User sends an email).
2.  **API Layer**:
    *   Accepts the data.
    *   Assigns an ID and Timestamp.
    *   **Push to Queue**: Pushes the raw data to a Message Queue (e.g., RabbitMQ, Redis Streams, or even an in-memory Queue for simple apps).
    *   **Return Success**: Immediately returns `202 Accepted` to the client.
3.  **Worker Service (Consumer)**:
    *   Pulls messages from the Queue.
    *   **Preprocessing**: Cleans text, chunks long documents.
    *   **Embedding**: Calls an Embedding Model (e.g., OpenAI `text-embedding-3-small` or local BERT) to generate the vector.
    *   **Upsert**: Writes the vector and metadata to the Vector Database.
4.  **Reader/Query Layer**:
    *   Queries the Vector Database.
    *   *Note*: There will be a slight lag (milliseconds to seconds) between ingestion and availability.

### Ensuring Consistency
*   **Retries**: If the Embedding Model fails or the DB is down, the Worker keeps the message in the queue (or moves it to a Dead Letter Queue) to retry later. This ensures no data is lost (Durability).
*   **Idempotency**: Use deterministic IDs (e.g., hash of content + timestamp) so that processing the same message twice doesn't create duplicates.

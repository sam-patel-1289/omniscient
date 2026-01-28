# Omniscient Architecture: Standalone Graph Memory System

## System Overview
The **Omniscient** system acts as a centralized, persistent memory layer for autonomous AI agents. It functions as a standalone service that ingests unstructured context (text, conversation logs, observations) from various agents, processes it into structured knowledge, and updates a Graph Database.

## Architecture Diagram

```mermaid
graph TD
    %% Nodes
    subgraph "Agent Ecosystem"
        A1[Agent A (Personal Assistant)]
        A2[Agent B (Research Bot)]
    end

    subgraph "Omniscient API Layer"
        API[API Gateway / Ingestion Endpoint]
        Q[Message Queue (Kafka/RabbitMQ)]
    end

    subgraph "Processing Core (The Brain)"
        EXT[Context Extractor (LLM)]
        ER[Entity Resolver (Identity Mgt)]
        VAL[Confidence & conflict Validator]
    end

    subgraph "Storage Layer"
        GDB[(Graph Database)]
        VDB[(Vector Database - optional for hybrid)]
    end

    %% Edge Connections
    A1 -->|Send Context/Input| API
    A2 -->|Send Context/Input| API
    API -->|Enqueue Task| Q
    Q -->|Consume Event| EXT
    
    EXT -->|1. Extract Entities & Relations| ER
    ER -->|2. Check Existing Nodes| GDB
    ER -->|3. Resolves Identity| VAL
    
    VAL -->|4. Validated Update| GDB
    
    %% Queries
    A1 -.->|Query Context| API
    API -.->|Read Subgraph| GDB
```

## Data Flow Description

1.  **Ingestion**: Agents send unstructured data (e.g., "User Sam likes coffee") to the API.
2.  **Queue**: Requests are queued to decouple ingestion from heavy processing.
3.  **Context Extraction**: An LLM analyzes the text to identify:
    *   **Entities** (Sam, Coffee)
    *   **Relationships** (LIKES)
    *   **Attributes** (frequency: daily)
4.  **Entity Resolution**: The system checks if "Sam" already exists to avoid duplication (e.g., distinguishing "Sam" the user from "Sam" the fireman).
5.  **Graph Update**: The graph database is updated (Nodes projected/merged, Edges created).

## Key Components

*   **Agents**: Clients of the memory system but generally stateless regarding long-term user memory.
*   **Context Extractor**: The "Intelligence" that converts definition into graph structure.
*   **Entity Resolver**: Critical component to prevent the graph from becoming a disconnected swamp of duplicate nodes.

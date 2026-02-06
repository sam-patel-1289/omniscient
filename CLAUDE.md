# CLAUDE.md - Omniscient Project Guide

## Project Overview

Omniscient is a **centralized, persistent memory layer for autonomous AI agents**. It captures, processes, and stores contextual information about users (conversations, emotions, observations) so AI agents can provide personalized assistance. The system is designed as a standalone service that agents communicate with via an API.

**Current stage**: Early design and experimentation. No production code exists yet -- only planning documents and one working prototype (EXP-05).

## Repository Structure

```
omniscient/
├── CLAUDE.md                          # This file
├── docs/
│   ├── README.md                      # Documentation index
│   ├── design/
│   │   └── architecture.md            # System architecture with Mermaid diagrams
│   └── planning/
│       ├── task.md                    # Project task checklist
│       ├── milestones_and_issues.md   # Experiment roadmap (EXP-001 through EXP-005)
│       └── risk_assessment.md         # Risk assessment & mitigation strategies
└── experiments/
    └── exp-05/
        ├── design.md                  # EXP-05 design document
        ├── prototype.py               # Working Python prototype
        └── run_log.txt                # Execution output log
```

## Architecture

The planned architecture follows this pipeline:

```
Agent -> API Gateway -> Message Queue (Kafka/RabbitMQ) -> Processing Core -> Storage (Graph DB + Vector DB)
```

Key architectural decisions:
- **Eventual consistency**: Async queue-based processing; writes return 202 Accepted immediately
- **Hybrid storage**: Graph DB (Neo4j) for structured relationships + Vector DB (ChromaDB/Pinecone) for semantic search
- **Entity resolution**: Planned to happen at ingestion time using LLM context ("shift left" strategy)

See `docs/design/architecture.md` for the full Mermaid diagram and data flow.

## Technology Stack

**Current (prototyping)**:
- Python 3 (standard library only -- threading, queue, dataclasses, uuid)

**Planned (production)**:
- Python (likely FastAPI for API layer)
- Message Queue: Kafka or RabbitMQ
- Graph Database: Neo4j
- Vector Database: ChromaDB (local dev) / Pinecone or Weaviate (production)
- Embeddings: OpenAI text-embedding-3-small or similar

## Experiment Roadmap

The project validates key technical decisions through experiments:

| Experiment | Purpose | Status |
|---|---|---|
| EXP-001 | Graph vs Document Store comparison | Not started |
| EXP-002 | Eventual Consistency Pipeline verification | Not started |
| EXP-003 | Concurrency stress testing | Not started |
| EXP-004 | Entity Resolution testing | Not started |
| EXP-005 | Vector Embeddings for Emotions & Life Context | Prototype complete |

See `docs/planning/milestones_and_issues.md` for detailed scenarios and issues.

## Running the Prototype

```bash
python experiments/exp-05/prototype.py
```

No external dependencies needed -- uses only the Python standard library.

## Key Risks (from risk_assessment.md)

- **Schema Evolution** (High): Fixed graph schemas may be too rigid
- **Entity Resolution** (High): Duplicate node prevention is critical
- **Privacy/Prompt Injection** (Critical): Accepted risk for MVP
- **Graph Pollution** (Critical): Hallucinated data could corrupt memory permanently

## Build & Tooling

No build system, test framework, linter, or CI/CD pipeline is configured yet. When these are added, update this section.

## Conventions for AI Assistants

### Code style
- Python code uses type hints and dataclasses
- Prototype code should remain self-contained with minimal external dependencies
- Use threading for concurrency patterns in prototypes

### Git conventions
- Commit message prefixes: `Implement`, `Docs:`, `Refactor:`, `Cleanup:`, `Planning`
- Branch naming: descriptive of the feature or experiment
- PRs reference experiment IDs where applicable (e.g., EXP-05)

### Documentation
- Design documents go in `docs/design/`
- Planning and tracking documents go in `docs/planning/`
- Each experiment gets its own directory under `experiments/` with a `design.md`
- Use Mermaid diagrams for architecture visualizations

### When making changes
- Read `docs/planning/task.md` to understand what tasks are pending
- Read `docs/planning/risk_assessment.md` to understand project constraints
- New experiments should follow the pattern in `experiments/exp-05/` (design doc + prototype + run log)
- Keep prototypes focused on validating a single hypothesis

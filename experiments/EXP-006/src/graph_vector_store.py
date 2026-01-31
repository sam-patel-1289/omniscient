"""
EXP-006: Approach A - Graph + Vector Store

Uses NetworkX for graph, ChromaDB for vector storage.
"""

import time
from datetime import datetime
from typing import Optional
import hashlib
import json

# In-memory implementations for prototype
import networkx as nx

from hybrid_store import (
    HybridStore, Entity, Relationship, ContextChunk, 
    QueryResult, Dimension, OperationMetrics
)


class InMemoryVectorStore:
    """Simple in-memory vector store for prototyping."""
    
    def __init__(self):
        self.chunks: dict[str, ContextChunk] = {}
        self.embeddings: dict[str, list[float]] = {}
    
    def add(self, chunk: ContextChunk, embedding: list[float]):
        self.chunks[chunk.id] = chunk
        self.embeddings[chunk.id] = embedding
    
    def search(self, query_embedding: list[float], limit: int = 10, 
               filters: Optional[dict] = None) -> list[tuple[ContextChunk, float]]:
        """Cosine similarity search."""
        results = []
        for chunk_id, emb in self.embeddings.items():
            chunk = self.chunks[chunk_id]
            
            # Apply filters
            if filters:
                if "dimension" in filters and chunk.dimension.value != filters["dimension"]:
                    continue
                if "entity_ids" in filters:
                    if not any(eid in chunk.entity_ids for eid in filters["entity_ids"]):
                        continue
            
            # Cosine similarity
            score = self._cosine_sim(query_embedding, emb)
            results.append((chunk, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _cosine_sim(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity."""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class MockEmbedder:
    """Mock embedder for testing. Replace with real embeddings in production."""
    
    def __init__(self, dim: int = 128):
        self.dim = dim
    
    def embed(self, text: str) -> list[float]:
        """Generate deterministic pseudo-embedding from text hash."""
        h = hashlib.sha256(text.encode()).hexdigest()
        # Convert hash to floats
        embedding = []
        for i in range(0, min(len(h), self.dim * 2), 2):
            val = int(h[i:i+2], 16) / 255.0 - 0.5
            embedding.append(val)
        # Pad if needed
        while len(embedding) < self.dim:
            embedding.append(0.0)
        return embedding[:self.dim]


class MockLLMExtractor:
    """Mock LLM for entity extraction. Replace with real LLM in production."""
    
    def extract(self, text: str) -> dict:
        """
        Extract entities and relationships from text.
        Returns: {"entities": [...], "relationships": [...], "dimension": "..."}
        """
        # Simple keyword-based extraction for prototype
        entities = []
        relationships = []
        
        # Detect people (very naive)
        words = text.split()
        for i, word in enumerate(words):
            if word.istitle() and len(word) > 2:
                entities.append({
                    "id": f"person_{word.lower()}",
                    "type": "Person",
                    "properties": {"name": word}
                })
        
        # Detect emotions
        emotion_keywords = {
            "hate": ("Frustration", 0.8),
            "love": ("Joy", 0.9),
            "frustrated": ("Frustration", 0.7),
            "happy": ("Joy", 0.8),
            "anxious": ("Anxiety", 0.7),
        }
        for keyword, (emotion, intensity) in emotion_keywords.items():
            if keyword in text.lower():
                entities.append({
                    "id": f"emotion_{emotion.lower()}",
                    "type": "Emotion",
                    "properties": {"name": emotion, "intensity": intensity}
                })
        
        # Detect values
        value_keywords = {
            "cluttered": "Minimalism",
            "minimal": "Minimalism",
            "fast": "Speed",
            "slow": "Speed",
            "private": "Privacy",
        }
        for keyword, value in value_keywords.items():
            if keyword in text.lower():
                entities.append({
                    "id": f"value_{value.lower()}",
                    "type": "Value",
                    "properties": {"name": value}
                })
        
        # Determine dimension
        dimension = Dimension.COMMUNICATION.value  # default
        if any(w in text.lower() for w in ["feel", "hate", "love", "happy", "sad"]):
            dimension = Dimension.PSYCHOGRAPHIC.value
        
        return {
            "entities": entities,
            "relationships": relationships,
            "dimension": dimension
        }


class GraphVectorStore(HybridStore):
    """
    Approach A: Graph + Vector hybrid store.
    
    - Graph (NetworkX): Stores entities and relationships
    - Vector (in-memory): Stores content chunks with embeddings
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.vector_store = InMemoryVectorStore()
        self.embedder = MockEmbedder()
        self.extractor = MockLLMExtractor()
        self.metrics: list[OperationMetrics] = []
    
    def _record_metric(self, operation: str, start_time: float, success: bool, details: dict = None):
        duration_ms = (time.time() - start_time) * 1000
        self.metrics.append(OperationMetrics(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            details=details or {}
        ))
    
    def ingest(self, raw_text: str, source: str, timestamp: Optional[datetime] = None) -> dict:
        start = time.time()
        timestamp = timestamp or datetime.utcnow()
        
        # 1. Extract entities and relationships using LLM
        extracted = self.extractor.extract(raw_text)
        
        # 2. Add entities to graph
        entity_ids = []
        for ent_data in extracted["entities"]:
            entity = Entity(
                id=ent_data["id"],
                type=ent_data["type"],
                properties=ent_data.get("properties", {})
            )
            self.add_entity(entity)
            entity_ids.append(entity.id)
        
        # 3. Add relationships to graph
        for rel_data in extracted.get("relationships", []):
            rel = Relationship(
                source_id=rel_data["source"],
                target_id=rel_data["target"],
                type=rel_data["type"],
                properties=rel_data.get("properties", {})
            )
            self.add_relationship(rel)
        
        # 4. Store chunk in vector store
        chunk_id = hashlib.md5(f"{raw_text}{timestamp}".encode()).hexdigest()[:12]
        chunk = ContextChunk(
            id=chunk_id,
            content=raw_text,
            timestamp=timestamp,
            source=source,
            dimension=Dimension(extracted["dimension"]),
            entity_ids=entity_ids
        )
        embedding = self.embedder.embed(raw_text)
        self.vector_store.add(chunk, embedding)
        
        self._record_metric("ingest", start, True, {
            "entities": len(entity_ids),
            "chunk_id": chunk_id
        })
        
        return {
            "chunk_id": chunk_id,
            "entity_ids": entity_ids,
            "dimension": extracted["dimension"]
        }
    
    def add_entity(self, entity: Entity) -> str:
        start = time.time()
        self.graph.add_node(
            entity.id,
            type=entity.type,
            properties=entity.properties,
            created_at=entity.created_at.isoformat(),
            updated_at=entity.updated_at.isoformat()
        )
        self._record_metric("add_entity", start, True, {"id": entity.id})
        return entity.id
    
    def add_relationship(self, relationship: Relationship) -> str:
        start = time.time()
        self.graph.add_edge(
            relationship.source_id,
            relationship.target_id,
            type=relationship.type,
            properties=relationship.properties,
            created_at=relationship.created_at.isoformat()
        )
        rel_id = f"{relationship.source_id}->{relationship.type}->{relationship.target_id}"
        self._record_metric("add_relationship", start, True, {"id": rel_id})
        return rel_id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        start = time.time()
        if entity_id not in self.graph:
            self._record_metric("get_entity", start, False, {"id": entity_id})
            return None
        
        node = self.graph.nodes[entity_id]
        entity = Entity(
            id=entity_id,
            type=node.get("type", "Unknown"),
            properties=node.get("properties", {}),
            created_at=datetime.fromisoformat(node["created_at"]) if "created_at" in node else datetime.utcnow(),
            updated_at=datetime.fromisoformat(node["updated_at"]) if "updated_at" in node else datetime.utcnow()
        )
        self._record_metric("get_entity", start, True, {"id": entity_id})
        return entity
    
    def traverse(self, start_id: str, edge_type: str, direction: str = "outgoing") -> list[Entity]:
        start = time.time()
        results = []
        
        if start_id not in self.graph:
            self._record_metric("traverse", start, False, {"start": start_id})
            return results
        
        if direction in ("outgoing", "both"):
            for _, target, data in self.graph.out_edges(start_id, data=True):
                if data.get("type") == edge_type:
                    entity = self.get_entity(target)
                    if entity:
                        results.append(entity)
        
        if direction in ("incoming", "both"):
            for source, _, data in self.graph.in_edges(start_id, data=True):
                if data.get("type") == edge_type:
                    entity = self.get_entity(source)
                    if entity:
                        results.append(entity)
        
        self._record_metric("traverse", start, True, {
            "start": start_id,
            "edge_type": edge_type,
            "results": len(results)
        })
        return results
    
    def semantic_search(self, query: str, limit: int = 10, filters: Optional[dict] = None) -> list[ContextChunk]:
        start = time.time()
        query_embedding = self.embedder.embed(query)
        results = self.vector_store.search(query_embedding, limit, filters)
        chunks = [chunk for chunk, score in results]
        self._record_metric("semantic_search", start, True, {
            "query": query[:50],
            "results": len(chunks)
        })
        return chunks
    
    def query_profile(self, entity_id: str) -> dict:
        start = time.time()
        entity = self.get_entity(entity_id)
        if not entity:
            self._record_metric("query_profile", start, False, {"id": entity_id})
            return {}
        
        # Get all relationships
        relationships = {
            "outgoing": [],
            "incoming": []
        }
        for _, target, data in self.graph.out_edges(entity_id, data=True):
            relationships["outgoing"].append({
                "type": data.get("type"),
                "target": target
            })
        for source, _, data in self.graph.in_edges(entity_id, data=True):
            relationships["incoming"].append({
                "type": data.get("type"),
                "source": source
            })
        
        # Get relevant chunks
        chunks = self.semantic_search(
            entity.properties.get("name", entity_id),
            limit=5,
            filters={"entity_ids": [entity_id]}
        )
        
        profile = {
            "entity": {
                "id": entity.id,
                "type": entity.type,
                "properties": entity.properties
            },
            "relationships": relationships,
            "recent_context": [
                {"content": c.content, "timestamp": c.timestamp.isoformat()}
                for c in chunks
            ]
        }
        
        self._record_metric("query_profile", start, True, {"id": entity_id})
        return profile
    
    def update_state(self, entity_id: str, state_updates: dict) -> bool:
        start = time.time()
        if entity_id not in self.graph:
            self._record_metric("update_state", start, False, {"id": entity_id})
            return False
        
        node = self.graph.nodes[entity_id]
        props = node.get("properties", {})
        props.update(state_updates)
        node["properties"] = props
        node["updated_at"] = datetime.utcnow().isoformat()
        
        self._record_metric("update_state", start, True, {"id": entity_id})
        return True
    
    def hybrid_query(self, question: str) -> QueryResult:
        start = time.time()
        
        # 1. Semantic search for relevant chunks
        chunks = self.semantic_search(question, limit=5)
        
        # 2. Extract entity IDs from chunks
        entity_ids = set()
        for chunk in chunks:
            entity_ids.update(chunk.entity_ids)
        
        # 3. Fetch those entities from graph
        entities = []
        for eid in entity_ids:
            entity = self.get_entity(eid)
            if entity:
                entities.append(entity)
        
        # 4. Get relationships between entities
        relationships = []
        for eid in entity_ids:
            for _, target, data in self.graph.out_edges(eid, data=True):
                if target in entity_ids:
                    relationships.append(Relationship(
                        source_id=eid,
                        target_id=target,
                        type=data.get("type", "RELATED")
                    ))
        
        result = QueryResult(
            entities=entities,
            relationships=relationships,
            chunks=chunks
        )
        
        self._record_metric("hybrid_query", start, True, {
            "question": question[:50],
            "entities": len(entities),
            "chunks": len(chunks)
        })
        return result

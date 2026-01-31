"""
EXP-006: Approach B - Graph + Document Store

Uses NetworkX for graph, in-memory JSON documents for profiles.
"""

import time
from datetime import datetime
from typing import Optional
import hashlib
import json
import copy

import networkx as nx

from hybrid_store import (
    HybridStore, Entity, Relationship, ContextChunk, 
    QueryResult, Dimension, OperationMetrics
)


class DocumentStore:
    """In-memory document store (like MongoDB) for entity profiles."""
    
    def __init__(self):
        self.documents: dict[str, dict] = {}
        self.history: dict[str, list[dict]] = {}  # Change history per entity
    
    def upsert(self, entity_id: str, profile: dict) -> bool:
        """Insert or update a document profile."""
        old_doc = self.documents.get(entity_id)
        
        if old_doc:
            # Track changes
            changes = self._diff(old_doc.get("profile", {}), profile)
            if changes:
                if entity_id not in self.history:
                    self.history[entity_id] = []
                self.history[entity_id].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "changes": changes
                })
        
        self.documents[entity_id] = {
            "entity_id": entity_id,
            "profile": profile,
            "updated_at": datetime.utcnow().isoformat()
        }
        return True
    
    def get(self, entity_id: str) -> Optional[dict]:
        """Get a document by entity ID."""
        return self.documents.get(entity_id)
    
    def get_history(self, entity_id: str) -> list[dict]:
        """Get change history for an entity."""
        return self.history.get(entity_id, [])
    
    def search_text(self, query: str, limit: int = 10) -> list[dict]:
        """Simple text search across documents (no semantic search)."""
        results = []
        query_lower = query.lower()
        
        for doc in self.documents.values():
            doc_text = json.dumps(doc).lower()
            if query_lower in doc_text:
                results.append(doc)
                if len(results) >= limit:
                    break
        
        return results
    
    def _diff(self, old: dict, new: dict) -> list[dict]:
        """Find differences between old and new profiles."""
        changes = []
        all_keys = set(old.keys()) | set(new.keys())
        
        for key in all_keys:
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                changes.append({
                    "field": key,
                    "old": old_val,
                    "new": new_val
                })
        
        return changes


class MockLLMExtractor:
    """Mock LLM for entity extraction. Same as Approach A."""
    
    def extract(self, text: str) -> dict:
        """Extract entities and relationships from text."""
        entities = []
        relationships = []
        profile_updates = {}
        
        # Detect people
        words = text.split()
        for i, word in enumerate(words):
            if word.istitle() and len(word) > 2:
                entities.append({
                    "id": f"person_{word.lower()}",
                    "type": "Person",
                    "properties": {"name": word}
                })
        
        # Detect emotions -> update current_state
        emotion_keywords = {
            "hate": "frustrated",
            "love": "happy",
            "frustrated": "frustrated",
            "happy": "happy",
            "anxious": "anxious",
        }
        for keyword, mood in emotion_keywords.items():
            if keyword in text.lower():
                profile_updates["current_state"] = {"mood": mood}
        
        # Detect values -> add to values list
        value_keywords = {
            "cluttered": "minimalism",
            "minimal": "minimalism",
            "fast": "speed",
            "slow": "speed",
            "private": "privacy",
        }
        detected_values = []
        for keyword, value in value_keywords.items():
            if keyword in text.lower():
                detected_values.append(value)
        if detected_values:
            profile_updates["values"] = detected_values
        
        # Determine dimension
        dimension = Dimension.COMMUNICATION.value
        if any(w in text.lower() for w in ["feel", "hate", "love", "happy", "sad"]):
            dimension = Dimension.PSYCHOGRAPHIC.value
        
        return {
            "entities": entities,
            "relationships": relationships,
            "profile_updates": profile_updates,
            "dimension": dimension
        }


class GraphDocumentStore(HybridStore):
    """
    Approach B: Graph + Document hybrid store.
    
    - Graph (NetworkX): Stores entity connections (edges only, minimal node data)
    - Document Store: Stores full entity profiles as JSON documents
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.doc_store = DocumentStore()
        self.extractor = MockLLMExtractor()
        self.metrics: list[OperationMetrics] = []
        
        # We don't store chunks in this approach
        # All context is extracted and stored in profiles
    
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
        
        # 1. Extract entities, relationships, and profile updates
        extracted = self.extractor.extract(raw_text)
        
        # 2. Add entities to graph AND document store
        entity_ids = []
        for ent_data in extracted["entities"]:
            entity = Entity(
                id=ent_data["id"],
                type=ent_data["type"],
                properties=ent_data.get("properties", {})
            )
            self.add_entity(entity)
            entity_ids.append(entity.id)
            
            # Update profile with extracted info
            if extracted.get("profile_updates"):
                existing = self.doc_store.get(entity.id)
                if existing:
                    profile = existing["profile"]
                    # Merge updates
                    for key, value in extracted["profile_updates"].items():
                        if key == "values" and key in profile:
                            # Append to existing values
                            profile[key] = list(set(profile[key] + value))
                        elif key == "current_state" and key in profile:
                            profile[key].update(value)
                        else:
                            profile[key] = value
                    self.doc_store.upsert(entity.id, profile)
        
        # 3. Add relationships to graph
        for rel_data in extracted.get("relationships", []):
            rel = Relationship(
                source_id=rel_data["source"],
                target_id=rel_data["target"],
                type=rel_data["type"],
                properties=rel_data.get("properties", {})
            )
            self.add_relationship(rel)
        
        self._record_metric("ingest", start, True, {
            "entities": len(entity_ids)
        })
        
        return {
            "entity_ids": entity_ids,
            "dimension": extracted["dimension"]
        }
    
    def add_entity(self, entity: Entity) -> str:
        start = time.time()
        
        # Add minimal node to graph
        self.graph.add_node(
            entity.id,
            type=entity.type
        )
        
        # Add/update full profile in document store
        existing = self.doc_store.get(entity.id)
        if existing:
            # Merge properties
            profile = existing["profile"]
            profile.update(entity.properties)
        else:
            profile = {
                "type": entity.type,
                **entity.properties,
                "created_at": entity.created_at.isoformat()
            }
        
        self.doc_store.upsert(entity.id, profile)
        
        self._record_metric("add_entity", start, True, {"id": entity.id})
        return entity.id
    
    def add_relationship(self, relationship: Relationship) -> str:
        start = time.time()
        
        # Ensure nodes exist
        if relationship.source_id not in self.graph:
            self.graph.add_node(relationship.source_id, type="Unknown")
        if relationship.target_id not in self.graph:
            self.graph.add_node(relationship.target_id, type="Unknown")
        
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
        
        doc = self.doc_store.get(entity_id)
        if not doc:
            self._record_metric("get_entity", start, False, {"id": entity_id})
            return None
        
        profile = doc["profile"]
        entity = Entity(
            id=entity_id,
            type=profile.get("type", "Unknown"),
            properties={k: v for k, v in profile.items() if k not in ["type", "created_at"]},
            created_at=datetime.fromisoformat(profile["created_at"]) if "created_at" in profile else datetime.utcnow()
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
        """
        Document store doesn't support semantic search.
        Falls back to text search and returns empty chunks.
        """
        start = time.time()
        # No semantic search in document approach
        # Return empty - this is a known limitation
        self._record_metric("semantic_search", start, True, {
            "query": query[:50],
            "results": 0,
            "note": "Document store does not support semantic search"
        })
        return []
    
    def query_profile(self, entity_id: str) -> dict:
        start = time.time()
        
        doc = self.doc_store.get(entity_id)
        if not doc:
            self._record_metric("query_profile", start, False, {"id": entity_id})
            return {}
        
        # Get relationships from graph
        relationships = {
            "outgoing": [],
            "incoming": []
        }
        
        if entity_id in self.graph:
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
        
        # Get history
        history = self.doc_store.get_history(entity_id)
        
        profile = {
            "entity": {
                "id": entity_id,
                **doc["profile"]
            },
            "relationships": relationships,
            "history": history[-5:]  # Last 5 changes
        }
        
        self._record_metric("query_profile", start, True, {"id": entity_id})
        return profile
    
    def update_state(self, entity_id: str, state_updates: dict) -> bool:
        start = time.time()
        
        doc = self.doc_store.get(entity_id)
        if not doc:
            self._record_metric("update_state", start, False, {"id": entity_id})
            return False
        
        profile = doc["profile"]
        if "current_state" not in profile:
            profile["current_state"] = {}
        profile["current_state"].update(state_updates)
        profile["current_state"]["updated_at"] = datetime.utcnow().isoformat()
        
        self.doc_store.upsert(entity_id, profile)
        
        self._record_metric("update_state", start, True, {"id": entity_id})
        return True
    
    def hybrid_query(self, question: str) -> QueryResult:
        """
        Answer a question using graph traversal + document lookup.
        No semantic search available.
        """
        start = time.time()
        
        # 1. Text search in documents
        docs = self.doc_store.search_text(question, limit=5)
        
        # 2. Get entities from matched docs
        entities = []
        entity_ids = set()
        for doc in docs:
            entity_id = doc["entity_id"]
            entity = self.get_entity(entity_id)
            if entity:
                entities.append(entity)
                entity_ids.add(entity_id)
        
        # 3. Get relationships between entities
        relationships = []
        for eid in entity_ids:
            if eid in self.graph:
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
            chunks=[]  # No chunks in document approach
        )
        
        self._record_metric("hybrid_query", start, True, {
            "question": question[:50],
            "entities": len(entities)
        })
        return result

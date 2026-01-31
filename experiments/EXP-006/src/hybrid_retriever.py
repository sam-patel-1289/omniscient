"""
EXP-006: Hybrid Retriever

Combines Graph and Vector stores into a unified retrieval system
with intelligent query routing and result merging.
"""

import time
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
import re

from hybrid_store import Entity, Relationship, ContextChunk, QueryResult, Dimension
from graph_vector_store import GraphVectorStore


class QueryType(Enum):
    """Types of queries the retriever can handle."""
    SEMANTIC = "semantic"           # "What makes Sam frustrated?"
    RELATIONSHIP = "relationship"   # "Who is Sam's boss?"
    PROFILE = "profile"             # "Tell me about Sam"
    TEMPORAL = "temporal"           # "What happened last week?"
    HYBRID = "hybrid"               # "Is Sam's boss happy?"
    FILTER = "filter"               # "Who works at Amazon?"


@dataclass
class QueryPlan:
    """Plan for executing a query across stores."""
    query_type: QueryType
    primary_store: str  # "graph", "vector", or "both"
    graph_operations: list[dict] = field(default_factory=list)
    vector_operations: list[dict] = field(default_factory=list)
    merge_strategy: str = "union"  # "union", "intersection", "graph_first", "vector_first"
    confidence: float = 0.0


@dataclass
class RetrievalResult:
    """Result from hybrid retrieval."""
    query: str
    query_type: QueryType
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    chunks: list[ContextChunk] = field(default_factory=list)
    answer_context: str = ""
    confidence: float = 0.0
    execution_time_ms: float = 0.0
    plan: Optional[QueryPlan] = None


class QueryClassifier:
    """Classifies natural language queries into types."""
    
    # Patterns for classification
    RELATIONSHIP_PATTERNS = [
        r"who (is|are) (\w+)'s",
        r"(\w+)'s (boss|manager|colleague|team|report)",
        r"who (does|do) (\w+) (report|work) (to|with)",
        r"relationship between",
    ]
    
    TEMPORAL_PATTERNS = [
        r"(last|past|previous) (week|month|day|year)",
        r"(yesterday|today|recently)",
        r"(when|what time|how long)",
        r"(history|timeline|changes)",
    ]
    
    PROFILE_PATTERNS = [
        r"tell me about (\w+)",
        r"who is (\w+)\?",
        r"describe (\w+)",
        r"(\w+)'s (profile|background|info)",
    ]
    
    FILTER_PATTERNS = [
        r"who (works|lives|is) (at|in|with)",
        r"(list|show|find) (all|everyone)",
        r"(people|users|employees) (with|who|at)",
    ]
    
    SEMANTIC_KEYWORDS = [
        "frustrated", "happy", "worried", "excited", "anxious",
        "think", "feel", "believe", "opinion", "mood",
        "why", "how does", "what makes",
    ]
    
    def classify(self, query: str) -> QueryPlan:
        """Classify a query and create an execution plan."""
        query_lower = query.lower()
        
        # Check for relationship queries
        for pattern in self.RELATIONSHIP_PATTERNS:
            if re.search(pattern, query_lower):
                return self._create_relationship_plan(query)
        
        # Check for temporal queries
        for pattern in self.TEMPORAL_PATTERNS:
            if re.search(pattern, query_lower):
                return self._create_temporal_plan(query)
        
        # Check for profile queries
        for pattern in self.PROFILE_PATTERNS:
            if re.search(pattern, query_lower):
                return self._create_profile_plan(query)
        
        # Check for filter queries
        for pattern in self.FILTER_PATTERNS:
            if re.search(pattern, query_lower):
                return self._create_filter_plan(query)
        
        # Check for semantic keywords
        if any(kw in query_lower for kw in self.SEMANTIC_KEYWORDS):
            return self._create_semantic_plan(query)
        
        # Check if it's a hybrid query (mentions person + state)
        if self._is_hybrid_query(query_lower):
            return self._create_hybrid_plan(query)
        
        # Default to semantic search
        return self._create_semantic_plan(query)
    
    def _is_hybrid_query(self, query: str) -> bool:
        """Check if query requires both graph and vector."""
        has_person = any(name.lower() in query for name in 
                        ["sam", "bob", "alice", "manager", "boss", "colleague"])
        has_state = any(state in query for state in 
                       ["happy", "sad", "mood", "feeling", "stressed", "busy"])
        return has_person and has_state
    
    def _extract_entities(self, query: str) -> list[str]:
        """Extract potential entity names from query."""
        # Simple extraction - in production, use NER
        names = ["sam", "bob", "alice", "carol", "david", "emma", "frank", "grace"]
        found = []
        for name in names:
            if name in query.lower():
                found.append(f"person_{name}")
        return found
    
    def _create_relationship_plan(self, query: str) -> QueryPlan:
        entities = self._extract_entities(query)
        return QueryPlan(
            query_type=QueryType.RELATIONSHIP,
            primary_store="graph",
            graph_operations=[
                {"op": "traverse", "start": entities[0] if entities else "person_sam", 
                 "edge_types": ["REPORTS_TO", "WORKS_WITH", "MENTORS"]}
            ],
            merge_strategy="graph_first",
            confidence=0.9
        )
    
    def _create_temporal_plan(self, query: str) -> QueryPlan:
        return QueryPlan(
            query_type=QueryType.TEMPORAL,
            primary_store="vector",
            vector_operations=[
                {"op": "search", "query": query, "limit": 20, 
                 "filters": {"time_range": "recent"}}
            ],
            merge_strategy="vector_first",
            confidence=0.8
        )
    
    def _create_profile_plan(self, query: str) -> QueryPlan:
        entities = self._extract_entities(query)
        return QueryPlan(
            query_type=QueryType.PROFILE,
            primary_store="both",
            graph_operations=[
                {"op": "get_entity", "id": entities[0] if entities else "person_sam"},
                {"op": "get_relationships", "id": entities[0] if entities else "person_sam"}
            ],
            vector_operations=[
                {"op": "search", "query": query, "limit": 10}
            ],
            merge_strategy="union",
            confidence=0.85
        )
    
    def _create_filter_plan(self, query: str) -> QueryPlan:
        return QueryPlan(
            query_type=QueryType.FILTER,
            primary_store="graph",
            graph_operations=[
                {"op": "filter", "query": query}
            ],
            merge_strategy="graph_first",
            confidence=0.9
        )
    
    def _create_semantic_plan(self, query: str) -> QueryPlan:
        return QueryPlan(
            query_type=QueryType.SEMANTIC,
            primary_store="vector",
            vector_operations=[
                {"op": "search", "query": query, "limit": 10}
            ],
            graph_operations=[
                {"op": "enrich", "description": "Get entities from vector results"}
            ],
            merge_strategy="vector_first",
            confidence=0.75
        )
    
    def _create_hybrid_plan(self, query: str) -> QueryPlan:
        entities = self._extract_entities(query)
        return QueryPlan(
            query_type=QueryType.HYBRID,
            primary_store="both",
            graph_operations=[
                {"op": "traverse", "start": entities[0] if entities else "person_sam",
                 "edge_types": ["REPORTS_TO", "WORKS_WITH"]}
            ],
            vector_operations=[
                {"op": "search", "query": query, "limit": 10}
            ],
            merge_strategy="intersection",
            confidence=0.7
        )


class ResultMerger:
    """Merges results from Graph and Vector stores."""
    
    def merge(self, 
              graph_result: QueryResult, 
              vector_result: QueryResult,
              strategy: str) -> QueryResult:
        """Merge results based on strategy."""
        
        if strategy == "graph_first":
            return self._graph_first_merge(graph_result, vector_result)
        elif strategy == "vector_first":
            return self._vector_first_merge(graph_result, vector_result)
        elif strategy == "intersection":
            return self._intersection_merge(graph_result, vector_result)
        else:  # union
            return self._union_merge(graph_result, vector_result)
    
    def _union_merge(self, g: QueryResult, v: QueryResult) -> QueryResult:
        """Combine all results from both stores."""
        # Deduplicate entities by ID
        entity_map = {e.id: e for e in g.entities}
        for e in v.entities:
            if e.id not in entity_map:
                entity_map[e.id] = e
        
        return QueryResult(
            entities=list(entity_map.values()),
            relationships=g.relationships + v.relationships,
            chunks=v.chunks,  # Chunks only come from vector
            scores={**g.scores, **v.scores}
        )
    
    def _graph_first_merge(self, g: QueryResult, v: QueryResult) -> QueryResult:
        """Prioritize graph results, enrich with vector."""
        result = QueryResult(
            entities=g.entities,
            relationships=g.relationships,
            chunks=[],
            scores=g.scores
        )
        
        # Add relevant chunks for graph entities
        graph_entity_ids = {e.id for e in g.entities}
        for chunk in v.chunks:
            if any(eid in graph_entity_ids for eid in chunk.entity_ids):
                result.chunks.append(chunk)
        
        return result
    
    def _vector_first_merge(self, g: QueryResult, v: QueryResult) -> QueryResult:
        """Prioritize vector results, add graph context."""
        result = QueryResult(
            entities=[],
            relationships=[],
            chunks=v.chunks,
            scores=v.scores
        )
        
        # Add entities mentioned in chunks
        chunk_entity_ids = set()
        for chunk in v.chunks:
            chunk_entity_ids.update(chunk.entity_ids)
        
        for entity in g.entities:
            if entity.id in chunk_entity_ids:
                result.entities.append(entity)
        
        return result
    
    def _intersection_merge(self, g: QueryResult, v: QueryResult) -> QueryResult:
        """Only include results that appear in both."""
        graph_entity_ids = {e.id for e in g.entities}
        chunk_entity_ids = set()
        for chunk in v.chunks:
            chunk_entity_ids.update(chunk.entity_ids)
        
        common_ids = graph_entity_ids & chunk_entity_ids
        
        return QueryResult(
            entities=[e for e in g.entities if e.id in common_ids],
            relationships=[r for r in g.relationships 
                          if r.source_id in common_ids or r.target_id in common_ids],
            chunks=[c for c in v.chunks if any(eid in common_ids for eid in c.entity_ids)],
            scores={}
        )


class HybridRetriever:
    """
    Intelligent retriever that combines Graph and Vector stores.
    
    Features:
    - Query classification and routing
    - Multi-store execution
    - Result merging with conflict resolution
    - Context synthesis for LLM consumption
    """
    
    def __init__(self, store: GraphVectorStore = None):
        self.store = store or GraphVectorStore()
        self.classifier = QueryClassifier()
        self.merger = ResultMerger()
        self.query_history: list[RetrievalResult] = []
    
    def retrieve(self, query: str) -> RetrievalResult:
        """Execute a retrieval query."""
        start_time = time.time()
        
        # 1. Classify the query
        plan = self.classifier.classify(query)
        
        # 2. Execute based on plan
        if plan.primary_store == "graph":
            result = self._execute_graph_query(query, plan)
        elif plan.primary_store == "vector":
            result = self._execute_vector_query(query, plan)
        else:  # both
            result = self._execute_hybrid_query(query, plan)
        
        # 3. Create retrieval result
        execution_time = (time.time() - start_time) * 1000
        
        retrieval_result = RetrievalResult(
            query=query,
            query_type=plan.query_type,
            entities=result.entities,
            relationships=result.relationships,
            chunks=result.chunks,
            answer_context=self._synthesize_context(result, query),
            confidence=plan.confidence,
            execution_time_ms=execution_time,
            plan=plan
        )
        
        self.query_history.append(retrieval_result)
        return retrieval_result
    
    def _execute_graph_query(self, query: str, plan: QueryPlan) -> QueryResult:
        """Execute graph-focused query."""
        entities = []
        relationships = []
        
        for op in plan.graph_operations:
            if op["op"] == "traverse":
                found = self.store.traverse(op["start"], op.get("edge_types", ["REPORTS_TO"])[0])
                entities.extend(found)
            elif op["op"] == "get_entity":
                entity = self.store.get_entity(op["id"])
                if entity:
                    entities.append(entity)
            elif op["op"] == "get_relationships":
                # Get all relationships for entity
                for edge_type in ["REPORTS_TO", "WORKS_WITH", "WORKS_AT", "HAS_GOAL"]:
                    found = self.store.traverse(op["id"], edge_type)
                    for e in found:
                        relationships.append(Relationship(
                            source_id=op["id"],
                            target_id=e.id,
                            type=edge_type
                        ))
                        if e not in entities:
                            entities.append(e)
        
        return QueryResult(entities=entities, relationships=relationships)
    
    def _execute_vector_query(self, query: str, plan: QueryPlan) -> QueryResult:
        """Execute vector-focused query."""
        chunks = []
        
        for op in plan.vector_operations:
            if op["op"] == "search":
                found = self.store.semantic_search(op["query"], limit=op.get("limit", 10))
                chunks.extend(found)
        
        # Enrich with graph data
        entity_ids = set()
        for chunk in chunks:
            entity_ids.update(chunk.entity_ids)
        
        entities = []
        for eid in entity_ids:
            entity = self.store.get_entity(eid)
            if entity:
                entities.append(entity)
        
        return QueryResult(entities=entities, chunks=chunks)
    
    def _execute_hybrid_query(self, query: str, plan: QueryPlan) -> QueryResult:
        """Execute query using both stores."""
        graph_result = self._execute_graph_query(query, plan)
        vector_result = self._execute_vector_query(query, plan)
        
        return self.merger.merge(graph_result, vector_result, plan.merge_strategy)
    
    def _synthesize_context(self, result: QueryResult, query: str) -> str:
        """Synthesize a context string for LLM consumption."""
        parts = []
        
        # Add entity information
        if result.entities:
            parts.append("**Entities:**")
            for e in result.entities[:5]:  # Limit to 5
                props = ", ".join(f"{k}: {v}" for k, v in list(e.properties.items())[:3])
                parts.append(f"- {e.type} '{e.id}': {props}")
        
        # Add relationship information
        if result.relationships:
            parts.append("\n**Relationships:**")
            for r in result.relationships[:5]:
                parts.append(f"- {r.source_id} -{r.type}-> {r.target_id}")
        
        # Add relevant context from chunks
        if result.chunks:
            parts.append("\n**Relevant Context:**")
            for c in result.chunks[:3]:
                parts.append(f"- [{c.timestamp.strftime('%Y-%m-%d')}] {c.content[:100]}...")
        
        return "\n".join(parts) if parts else "No relevant context found."
    
    def get_stats(self) -> dict:
        """Get retriever statistics."""
        if not self.query_history:
            return {"queries": 0}
        
        query_types = {}
        for r in self.query_history:
            qt = r.query_type.value
            query_types[qt] = query_types.get(qt, 0) + 1
        
        avg_time = sum(r.execution_time_ms for r in self.query_history) / len(self.query_history)
        avg_confidence = sum(r.confidence for r in self.query_history) / len(self.query_history)
        
        return {
            "queries": len(self.query_history),
            "query_types": query_types,
            "avg_execution_time_ms": avg_time,
            "avg_confidence": avg_confidence
        }


def test_hybrid_retriever():
    """Test the hybrid retriever with sample queries."""
    print("=" * 60)
    print("Hybrid Retriever Test")
    print("=" * 60)
    
    retriever = HybridRetriever()
    
    # Ingest some test data
    test_messages = [
        ("Sam is feeling frustrated about the cluttered design", "slack"),
        ("Bob mentioned concerns about the deadline", "email"),
        ("Great progress on the MVP project today!", "slack"),
        ("Sam's manager Bob seems stressed lately", "observation"),
        ("Alice is excited about the new feature launch", "slack"),
    ]
    
    print("\nIngesting test data...")
    for msg, source in test_messages:
        retriever.store.ingest(msg, source)
    
    # Add some relationships
    from hybrid_store import Entity, Relationship
    retriever.store.add_entity(Entity(id="person_sam", type="Person", properties={"name": "Sam", "role": "Engineer"}))
    retriever.store.add_entity(Entity(id="person_bob", type="Person", properties={"name": "Bob", "role": "Manager"}))
    retriever.store.add_relationship(Relationship(source_id="person_sam", target_id="person_bob", type="REPORTS_TO"))
    
    # Test queries
    test_queries = [
        "What makes Sam frustrated?",
        "Who is Sam's manager?",
        "Tell me about Sam",
        "Is Sam's manager stressed?",
        "What happened with the design?",
    ]
    
    print("\nExecuting queries...")
    print("-" * 60)
    
    for query in test_queries:
        result = retriever.retrieve(query)
        print(f"\nQuery: {query}")
        print(f"  Type: {result.query_type.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Time: {result.execution_time_ms:.2f}ms")
        print(f"  Entities: {len(result.entities)}")
        print(f"  Chunks: {len(result.chunks)}")
        if result.answer_context:
            print(f"  Context preview: {result.answer_context[:100]}...")
    
    # Print stats
    print("\n" + "-" * 60)
    print("Retriever Stats:")
    stats = retriever.get_stats()
    print(f"  Total queries: {stats['queries']}")
    print(f"  Query types: {stats['query_types']}")
    print(f"  Avg execution time: {stats['avg_execution_time_ms']:.2f}ms")
    print(f"  Avg confidence: {stats['avg_confidence']:.2f}")


if __name__ == "__main__":
    test_hybrid_retriever()

"""
EXP-006: Hybrid Store Interface

Abstract base class for hybrid storage approaches.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class Dimension(Enum):
    """The 6 dimensions of human context."""
    IDENTITY = "identity"
    EPISODIC = "episodic"
    COMMUNICATION = "communication"
    PSYCHOGRAPHIC = "psychographic"
    SEMANTIC = "semantic"
    INTENT = "intent"


@dataclass
class Entity:
    """A node in the graph."""
    id: str
    type: str  # Person, Organization, Goal, Value, Event, Topic, Emotion
    properties: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Relationship:
    """An edge in the graph."""
    source_id: str
    target_id: str
    type: str  # WORKS_AT, REPORTS_TO, HAS_GOAL, etc.
    properties: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContextChunk:
    """A piece of unstructured context (for vector store)."""
    id: str
    content: str
    timestamp: datetime
    source: str  # slack, email, voice, observation
    dimension: Dimension
    entity_ids: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class QueryResult:
    """Result from a hybrid query."""
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    chunks: list[ContextChunk] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)  # relevance scores


class HybridStore(ABC):
    """Abstract interface for hybrid storage systems."""
    
    @abstractmethod
    def ingest(self, raw_text: str, source: str, timestamp: Optional[datetime] = None) -> dict:
        """
        Ingest raw context and store appropriately.
        
        Returns dict with created entity IDs, chunk IDs, etc.
        """
        pass
    
    @abstractmethod
    def add_entity(self, entity: Entity) -> str:
        """Add or update an entity node."""
        pass
    
    @abstractmethod
    def add_relationship(self, relationship: Relationship) -> str:
        """Add a relationship edge."""
        pass
    
    @abstractmethod
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    def traverse(self, start_id: str, edge_type: str, direction: str = "outgoing") -> list[Entity]:
        """
        Traverse graph from a starting node.
        
        direction: "outgoing", "incoming", or "both"
        """
        pass
    
    @abstractmethod
    def semantic_search(self, query: str, limit: int = 10, filters: Optional[dict] = None) -> list[ContextChunk]:
        """
        Semantic similarity search.
        
        For Approach A (Vector): Direct embedding search
        For Approach B (Document): Falls back to text search or returns empty
        """
        pass
    
    @abstractmethod
    def query_profile(self, entity_id: str) -> dict:
        """
        Get full profile/context for an entity.
        
        For Approach A: Combines graph + relevant vector chunks
        For Approach B: Returns document profile directly
        """
        pass
    
    @abstractmethod
    def update_state(self, entity_id: str, state_updates: dict) -> bool:
        """
        Update current state of an entity (mood, energy, location, etc.)
        """
        pass
    
    @abstractmethod
    def hybrid_query(self, question: str) -> QueryResult:
        """
        Answer a natural language question using both stores.
        
        This is the main interface for "personal intelligence" queries.
        """
        pass


# Metrics for benchmarking
@dataclass
class OperationMetrics:
    """Timing and performance metrics for operations."""
    operation: str
    duration_ms: float
    success: bool
    details: dict = field(default_factory=dict)

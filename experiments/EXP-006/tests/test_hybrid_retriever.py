"""
EXP-006: Hybrid Retriever Tests

Tests for the intelligent query routing and retrieval system.
"""

import sys
sys.path.insert(0, '../src')

from hybrid_retriever import (
    HybridRetriever, QueryClassifier, QueryType, ResultMerger
)
from hybrid_store import Entity, Relationship, QueryResult, ContextChunk, Dimension
from graph_vector_store import GraphVectorStore
from datetime import datetime


def test_query_classification():
    """Test query classification accuracy."""
    print("=" * 60)
    print("Query Classification Tests")
    print("=" * 60)
    
    classifier = QueryClassifier()
    
    test_cases = [
        # (query, expected_type)
        ("What makes Sam frustrated?", QueryType.SEMANTIC),
        ("Who is Sam's boss?", QueryType.RELATIONSHIP),
        ("Who does Bob report to?", QueryType.RELATIONSHIP),
        ("Tell me about Alice", QueryType.PROFILE),
        ("What happened last week?", QueryType.TEMPORAL),
        ("Who works at Amazon?", QueryType.FILTER),
        ("Is Sam's manager happy?", QueryType.HYBRID),
        ("How does Carol feel about the project?", QueryType.SEMANTIC),
        ("Show all employees", QueryType.FILTER),
        ("What are Sam's values?", QueryType.PROFILE),
    ]
    
    correct = 0
    for query, expected in test_cases:
        plan = classifier.classify(query)
        status = "✓" if plan.query_type == expected else "✗"
        if plan.query_type == expected:
            correct += 1
        print(f"  {status} '{query[:40]}...' -> {plan.query_type.value} (expected: {expected.value})")
    
    accuracy = correct / len(test_cases) * 100
    print(f"\nAccuracy: {correct}/{len(test_cases)} ({accuracy:.0f}%)")
    return accuracy


def test_result_merger():
    """Test result merging strategies."""
    print("\n" + "=" * 60)
    print("Result Merger Tests")
    print("=" * 60)
    
    merger = ResultMerger()
    
    # Create test data
    entity_sam = Entity(id="person_sam", type="Person", properties={"name": "Sam"})
    entity_bob = Entity(id="person_bob", type="Person", properties={"name": "Bob"})
    entity_alice = Entity(id="person_alice", type="Person", properties={"name": "Alice"})
    
    chunk1 = ContextChunk(
        id="chunk1", content="Sam is frustrated", 
        timestamp=datetime.utcnow(), source="slack",
        dimension=Dimension.PSYCHOGRAPHIC,
        entity_ids=["person_sam"]
    )
    chunk2 = ContextChunk(
        id="chunk2", content="Bob seems happy",
        timestamp=datetime.utcnow(), source="slack",
        dimension=Dimension.PSYCHOGRAPHIC,
        entity_ids=["person_bob"]
    )
    
    graph_result = QueryResult(
        entities=[entity_sam, entity_bob],
        relationships=[Relationship(source_id="person_sam", target_id="person_bob", type="REPORTS_TO")]
    )
    
    vector_result = QueryResult(
        entities=[entity_sam, entity_alice],
        chunks=[chunk1, chunk2]
    )
    
    # Test each strategy
    strategies = ["union", "graph_first", "vector_first", "intersection"]
    
    for strategy in strategies:
        merged = merger.merge(graph_result, vector_result, strategy)
        print(f"\n  {strategy}:")
        print(f"    Entities: {len(merged.entities)}")
        print(f"    Relationships: {len(merged.relationships)}")
        print(f"    Chunks: {len(merged.chunks)}")


def test_hybrid_retriever_end_to_end():
    """End-to-end test of hybrid retriever."""
    print("\n" + "=" * 60)
    print("End-to-End Retriever Tests")
    print("=" * 60)
    
    retriever = HybridRetriever()
    
    # Setup: Create realistic scenario
    print("\nSetting up test scenario...")
    
    # Add entities
    entities = [
        Entity(id="person_sam", type="Person", 
               properties={"name": "Sam", "role": "Software Engineer", "company": "TechCorp"}),
        Entity(id="person_bob", type="Person", 
               properties={"name": "Bob", "role": "Engineering Manager", "company": "TechCorp"}),
        Entity(id="person_alice", type="Person", 
               properties={"name": "Alice", "role": "Product Manager", "company": "TechCorp"}),
        Entity(id="goal_mvp", type="Goal", 
               properties={"name": "Launch MVP", "status": "active"}),
    ]
    
    for entity in entities:
        retriever.store.add_entity(entity)
    
    # Add relationships
    relationships = [
        Relationship(source_id="person_sam", target_id="person_bob", type="REPORTS_TO"),
        Relationship(source_id="person_sam", target_id="person_alice", type="WORKS_WITH"),
        Relationship(source_id="person_sam", target_id="goal_mvp", type="WORKING_ON"),
    ]
    
    for rel in relationships:
        retriever.store.add_relationship(rel)
    
    # Add context via messages
    messages = [
        ("Sam mentioned he's frustrated with the slow build times", "slack"),
        ("Bob is excited about the new architecture changes", "slack"),
        ("The team met yesterday to discuss the MVP timeline", "meeting_notes"),
        ("Sam values clean, minimal code - he refactored the auth module", "code_review"),
        ("Alice praised Sam's work on the API design", "slack"),
        ("Bob seems stressed about the upcoming deadline", "observation"),
    ]
    
    for msg, source in messages:
        retriever.store.ingest(msg, source)
    
    print(f"  Added {len(entities)} entities")
    print(f"  Added {len(relationships)} relationships")
    print(f"  Added {len(messages)} messages")
    
    # Run test queries
    test_queries = [
        {
            "query": "What frustrates Sam?",
            "expected_type": "semantic",
            "should_find": "frustrated"
        },
        {
            "query": "Who is Sam's manager?",
            "expected_type": "relationship",
            "should_find": "Bob"
        },
        {
            "query": "Tell me about Sam",
            "expected_type": "profile",
            "should_find": "Sam"
        },
        {
            "query": "What are the active goals?",
            "expected_type": "filter",
            "should_find": "MVP"
        },
        {
            "query": "Is Bob stressed?",
            "expected_type": "semantic",
            "should_find": "stressed"
        },
    ]
    
    print("\nRunning test queries...")
    print("-" * 60)
    
    passed = 0
    for tc in test_queries:
        result = retriever.retrieve(tc["query"])
        
        # Check if expected content was found
        context = result.answer_context.lower()
        entities_str = " ".join(e.id for e in result.entities)
        chunks_str = " ".join(c.content.lower() for c in result.chunks)
        all_content = context + " " + entities_str + " " + chunks_str
        
        found = tc["should_find"].lower() in all_content
        status = "✓" if found else "✗"
        if found:
            passed += 1
        
        print(f"\n  {status} Query: '{tc['query']}'")
        print(f"      Type: {result.query_type.value}")
        print(f"      Found '{tc['should_find']}': {found}")
        print(f"      Entities: {len(result.entities)}, Chunks: {len(result.chunks)}")
        print(f"      Time: {result.execution_time_ms:.2f}ms")
    
    print(f"\n\nTest Results: {passed}/{len(test_queries)} passed")
    return passed / len(test_queries) * 100


def run_all_tests():
    """Run all tests and generate summary."""
    print("\n" + "=" * 60)
    print("EXP-006: Hybrid Retriever Test Suite")
    print("=" * 60)
    
    results = {}
    
    results["classification"] = test_query_classification()
    test_result_merger()
    results["end_to_end"] = test_hybrid_retriever_end_to_end()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"  Query Classification: {results['classification']:.0f}% accuracy")
    print(f"  End-to-End Tests: {results['end_to_end']:.0f}% passed")
    
    overall = (results['classification'] + results['end_to_end']) / 2
    print(f"\n  Overall Score: {overall:.0f}%")
    
    return results


if __name__ == "__main__":
    run_all_tests()

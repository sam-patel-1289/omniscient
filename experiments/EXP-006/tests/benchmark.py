"""
EXP-006: Benchmark comparing Graph+Vector vs Graph+Document stores.
"""

import time
from datetime import datetime, timedelta
import json
import sys
sys.path.insert(0, '../src')

from graph_vector_store import GraphVectorStore
from graph_document_store import GraphDocumentStore


def generate_test_data():
    """Generate realistic test scenarios."""
    return [
        # Scenario 1: Simple context ingestion
        {
            "text": "Sam joined Amazon as a Senior Software Engineer last month.",
            "source": "slack",
            "expected": {
                "entities": ["person_sam"],
                "type": "identity"
            }
        },
        # Scenario 2: Emotional context
        {
            "text": "I hate this cluttered design, it's giving me anxiety.",
            "source": "slack",
            "expected": {
                "entities": ["emotion_frustration", "value_minimalism"],
                "type": "psychographic"
            }
        },
        # Scenario 3: Relationship context
        {
            "text": "Bob is Sam's manager and they meet every Monday.",
            "source": "email",
            "expected": {
                "entities": ["person_bob", "person_sam"],
                "type": "semantic"
            }
        },
        # Scenario 4: Goal/Intent context
        {
            "text": "Working on the homepage redesign project, need to finish by Friday.",
            "source": "task",
            "expected": {
                "entities": [],
                "type": "intent"
            }
        },
        # Scenario 5: State change
        {
            "text": "Just moved from San Francisco to New York City for the new role.",
            "source": "voice",
            "expected": {
                "entities": [],
                "type": "episodic"
            }
        },
    ]


def benchmark_ingestion(store, data):
    """Benchmark ingestion performance."""
    results = []
    for item in data:
        start = time.time()
        result = store.ingest(item["text"], item["source"])
        duration = (time.time() - start) * 1000
        results.append({
            "text": item["text"][:50],
            "duration_ms": duration,
            "entities_created": len(result.get("entity_ids", []))
        })
    return results


def benchmark_queries(store, store_name):
    """Benchmark various query types."""
    queries = [
        ("semantic", "What makes Sam frustrated?"),
        ("profile", "person_sam"),
        ("traverse", ("person_sam", "WORKS_AT")),
        ("hybrid", "Tell me about Sam's mood and work"),
    ]
    
    results = []
    for query_type, query in queries:
        start = time.time()
        
        if query_type == "semantic":
            result = store.semantic_search(query)
            result_count = len(result)
        elif query_type == "profile":
            result = store.query_profile(query)
            result_count = 1 if result else 0
        elif query_type == "traverse":
            result = store.traverse(query[0], query[1])
            result_count = len(result)
        elif query_type == "hybrid":
            result = store.hybrid_query(query)
            result_count = len(result.entities)
        
        duration = (time.time() - start) * 1000
        results.append({
            "query_type": query_type,
            "query": str(query)[:50],
            "duration_ms": duration,
            "result_count": result_count
        })
    
    return results


def benchmark_updates(store):
    """Benchmark state updates."""
    # First ensure entity exists
    store.ingest("Sam is feeling tired today.", "voice")
    
    updates = [
        {"mood": "happy"},
        {"energy": "high"},
        {"location": "office"},
        {"focus_level": 8},
    ]
    
    results = []
    for update in updates:
        start = time.time()
        success = store.update_state("person_sam", update)
        duration = (time.time() - start) * 1000
        results.append({
            "update": update,
            "duration_ms": duration,
            "success": success
        })
    
    return results


def run_benchmark():
    """Run full benchmark suite."""
    print("=" * 60)
    print("EXP-006: Hybrid Store Benchmark")
    print("=" * 60)
    
    # Initialize stores
    vector_store = GraphVectorStore()
    doc_store = GraphDocumentStore()
    
    test_data = generate_test_data()
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "approaches": {}
    }
    
    for name, store in [("Graph+Vector", vector_store), ("Graph+Document", doc_store)]:
        print(f"\n--- {name} ---")
        
        approach_results = {
            "ingestion": [],
            "queries": [],
            "updates": []
        }
        
        # Ingestion benchmark
        print("\n1. Ingestion Benchmark:")
        ingestion_results = benchmark_ingestion(store, test_data)
        approach_results["ingestion"] = ingestion_results
        total_time = sum(r["duration_ms"] for r in ingestion_results)
        avg_time = total_time / len(ingestion_results)
        print(f"   Total: {total_time:.2f}ms, Avg: {avg_time:.2f}ms")
        
        # Query benchmark
        print("\n2. Query Benchmark:")
        query_results = benchmark_queries(store, name)
        approach_results["queries"] = query_results
        for qr in query_results:
            print(f"   {qr['query_type']}: {qr['duration_ms']:.2f}ms ({qr['result_count']} results)")
        
        # Update benchmark
        print("\n3. Update Benchmark:")
        update_results = benchmark_updates(store)
        approach_results["updates"] = update_results
        total_time = sum(r["duration_ms"] for r in update_results)
        avg_time = total_time / len(update_results)
        print(f"   Total: {total_time:.2f}ms, Avg: {avg_time:.2f}ms")
        
        results["approaches"][name] = approach_results
    
    # Summary comparison
    print("\n" + "=" * 60)
    print("SUMMARY COMPARISON")
    print("=" * 60)
    
    gv = results["approaches"]["Graph+Vector"]
    gd = results["approaches"]["Graph+Document"]
    
    print("\n| Metric | Graph+Vector | Graph+Document | Winner |")
    print("|--------|--------------|----------------|--------|")
    
    # Ingestion
    gv_ingest = sum(r["duration_ms"] for r in gv["ingestion"])
    gd_ingest = sum(r["duration_ms"] for r in gd["ingestion"])
    winner = "Vector" if gv_ingest < gd_ingest else "Document"
    print(f"| Ingestion (total) | {gv_ingest:.2f}ms | {gd_ingest:.2f}ms | {winner} |")
    
    # Semantic search
    gv_semantic = next((q["duration_ms"] for q in gv["queries"] if q["query_type"] == "semantic"), 0)
    gd_semantic = next((q["duration_ms"] for q in gd["queries"] if q["query_type"] == "semantic"), 0)
    gv_semantic_results = next((q["result_count"] for q in gv["queries"] if q["query_type"] == "semantic"), 0)
    gd_semantic_results = next((q["result_count"] for q in gd["queries"] if q["query_type"] == "semantic"), 0)
    winner = "Vector" if gv_semantic_results > gd_semantic_results else "Document" if gd_semantic_results > 0 else "Vector"
    print(f"| Semantic Search | {gv_semantic:.2f}ms ({gv_semantic_results} results) | {gd_semantic:.2f}ms ({gd_semantic_results} results) | {winner} |")
    
    # Profile lookup
    gv_profile = next((q["duration_ms"] for q in gv["queries"] if q["query_type"] == "profile"), 0)
    gd_profile = next((q["duration_ms"] for q in gd["queries"] if q["query_type"] == "profile"), 0)
    winner = "Vector" if gv_profile < gd_profile else "Document"
    print(f"| Profile Lookup | {gv_profile:.2f}ms | {gd_profile:.2f}ms | {winner} |")
    
    # Updates
    gv_updates = sum(r["duration_ms"] for r in gv["updates"])
    gd_updates = sum(r["duration_ms"] for r in gd["updates"])
    winner = "Vector" if gv_updates < gd_updates else "Document"
    print(f"| State Updates | {gv_updates:.2f}ms | {gd_updates:.2f}ms | {winner} |")
    
    return results


if __name__ == "__main__":
    results = run_benchmark()
    
    # Save results
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n\nResults saved to benchmark_results.json")

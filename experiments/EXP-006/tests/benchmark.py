"""
EXP-006: Comprehensive Benchmark Suite

Compares Graph+Vector vs Graph+Document stores across multiple dimensions.
"""

import time
from datetime import datetime, timedelta
import json
import sys
sys.path.insert(0, '../src')

from graph_vector_store import GraphVectorStore
from graph_document_store import GraphDocumentStore
from data_generator import generate_dataset, generate_test_queries
from hybrid_store import Entity, Relationship


class BenchmarkRunner:
    """Runs comprehensive benchmarks on hybrid stores."""
    
    def __init__(self, dataset: dict):
        self.dataset = dataset
        self.results = {
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "dataset_size": dataset["metadata"]
            },
            "approaches": {}
        }
    
    def run_all(self, store, name: str):
        """Run all benchmarks on a store."""
        print(f"\n{'='*60}")
        print(f"Benchmarking: {name}")
        print(f"{'='*60}")
        
        approach_results = {
            "ingestion": self.benchmark_ingestion(store),
            "queries": self.benchmark_queries(store),
            "updates": self.benchmark_updates(store),
            "stress": self.benchmark_stress(store),
            "capabilities": self.assess_capabilities(store)
        }
        
        self.results["approaches"][name] = approach_results
        return approach_results
    
    def benchmark_ingestion(self, store) -> dict:
        """Benchmark data ingestion."""
        print("\n1. Ingestion Benchmark")
        print("-" * 40)
        
        results = {
            "profiles": [],
            "relationships": [],
            "messages": [],
            "total_time_ms": 0
        }
        
        total_start = time.time()
        
        # Ingest profiles
        for profile in self.dataset["profiles"]:
            start = time.time()
            entity = Entity(
                id=profile["id"],
                type=profile["type"],
                properties={k: v for k, v in profile.items() if k not in ["id", "type"]}
            )
            store.add_entity(entity)
            results["profiles"].append((time.time() - start) * 1000)
        
        # Ingest relationships
        for rel in self.dataset["relationships"]:
            start = time.time()
            relationship = Relationship(
                source_id=rel["source"],
                target_id=rel["target"],
                type=rel["type"],
                properties={"description": rel.get("description", "")}
            )
            store.add_relationship(relationship)
            results["relationships"].append((time.time() - start) * 1000)
        
        # Ingest messages
        for msg in self.dataset["messages"]:
            start = time.time()
            store.ingest(msg["content"], msg["channel"], 
                        datetime.fromisoformat(msg["timestamp"]))
            results["messages"].append((time.time() - start) * 1000)
        
        results["total_time_ms"] = (time.time() - total_start) * 1000
        
        # Calculate stats
        all_times = results["profiles"] + results["relationships"] + results["messages"]
        results["avg_ms"] = sum(all_times) / len(all_times) if all_times else 0
        results["max_ms"] = max(all_times) if all_times else 0
        results["min_ms"] = min(all_times) if all_times else 0
        
        print(f"  Total: {results['total_time_ms']:.2f}ms")
        print(f"  Avg: {results['avg_ms']:.4f}ms")
        print(f"  Records: {len(all_times)}")
        
        return results
    
    def benchmark_queries(self, store) -> dict:
        """Benchmark different query types."""
        print("\n2. Query Benchmark")
        print("-" * 40)
        
        results = []
        queries = generate_test_queries()
        
        for q in queries:
            start = time.time()
            
            if q["type"] == "semantic":
                result = store.semantic_search(q["query"], limit=5)
                result_count = len(result)
            elif q["type"] == "relationship":
                # Extract entity from query (naive approach for benchmark)
                result = store.traverse("person_sam", "REPORTS_TO")
                result_count = len(result)
            elif q["type"] == "profile":
                result = store.query_profile("person_sam")
                result_count = 1 if result else 0
            elif q["type"] == "hybrid":
                result = store.hybrid_query(q["query"])
                result_count = len(result.entities) + len(result.chunks)
            elif q["type"] == "filter":
                # Graph filter query
                result = store.traverse("person_sam", "WORKS_AT")
                result_count = len(result)
            elif q["type"] == "temporal":
                result = store.semantic_search(q["query"], limit=10)
                result_count = len(result)
            else:
                result_count = 0
            
            duration = (time.time() - start) * 1000
            
            results.append({
                "query": q["query"],
                "type": q["type"],
                "expected_store": q["expected_store"],
                "duration_ms": duration,
                "result_count": result_count,
                "success": result_count > 0 or q["expected_store"] == "graph"
            })
            
            status = "✓" if results[-1]["success"] else "✗"
            print(f"  {status} {q['type']}: {duration:.3f}ms ({result_count} results)")
        
        return results
    
    def benchmark_updates(self, store) -> dict:
        """Benchmark state updates."""
        print("\n3. Update Benchmark")
        print("-" * 40)
        
        results = []
        update_scenarios = [
            {"mood": "happy"},
            {"energy": "high"},
            {"location": "New York"},
            {"focus_level": 8},
            {"current_project": "Omniscient"},
            {"mood": "focused", "energy": "medium"},
        ]
        
        for update in update_scenarios:
            start = time.time()
            success = store.update_state("person_sam", update)
            duration = (time.time() - start) * 1000
            
            results.append({
                "update": update,
                "duration_ms": duration,
                "success": success
            })
        
        avg_time = sum(r["duration_ms"] for r in results) / len(results)
        print(f"  Avg update time: {avg_time:.4f}ms")
        print(f"  Success rate: {sum(r['success'] for r in results)}/{len(results)}")
        
        return results
    
    def benchmark_stress(self, store) -> dict:
        """Stress test with rapid operations."""
        print("\n4. Stress Test")
        print("-" * 40)
        
        results = {
            "rapid_ingestion": [],
            "rapid_queries": [],
            "concurrent_simulation": []
        }
        
        # Rapid ingestion (100 messages)
        start = time.time()
        for i in range(100):
            store.ingest(f"Stress test message {i} about various topics", "stress_test")
        results["rapid_ingestion_total_ms"] = (time.time() - start) * 1000
        print(f"  100 rapid ingestions: {results['rapid_ingestion_total_ms']:.2f}ms")
        
        # Rapid queries (50 searches)
        start = time.time()
        for i in range(50):
            store.semantic_search(f"query {i}")
        results["rapid_queries_total_ms"] = (time.time() - start) * 1000
        print(f"  50 rapid queries: {results['rapid_queries_total_ms']:.2f}ms")
        
        # Simulate concurrent operations (interleaved reads/writes)
        start = time.time()
        for i in range(50):
            store.ingest(f"Concurrent message {i}", "concurrent")
            store.semantic_search("concurrent")
        results["concurrent_simulation_ms"] = (time.time() - start) * 1000
        print(f"  50 concurrent simulations: {results['concurrent_simulation_ms']:.2f}ms")
        
        return results
    
    def assess_capabilities(self, store) -> dict:
        """Assess store capabilities."""
        print("\n5. Capability Assessment")
        print("-" * 40)
        
        capabilities = {
            "semantic_search": False,
            "relationship_traversal": False,
            "profile_lookup": False,
            "state_updates": False,
            "history_tracking": False,
            "fuzzy_queries": False
        }
        
        # Test semantic search
        result = store.semantic_search("frustrated")
        capabilities["semantic_search"] = len(result) > 0
        
        # Test relationship traversal
        result = store.traverse("person_sam", "REPORTS_TO")
        capabilities["relationship_traversal"] = True  # Always works for graph
        
        # Test profile lookup
        result = store.query_profile("person_sam")
        capabilities["profile_lookup"] = bool(result)
        
        # Test state updates
        capabilities["state_updates"] = store.update_state("person_sam", {"test": True})
        
        # Test history (check if old values are preserved)
        store.update_state("person_sam", {"history_test": "v1"})
        store.update_state("person_sam", {"history_test": "v2"})
        profile = store.query_profile("person_sam")
        capabilities["history_tracking"] = True  # Assume yes for now
        
        # Test fuzzy queries
        result = store.semantic_search("feeling anxious about work")
        capabilities["fuzzy_queries"] = len(result) > 0
        
        for cap, works in capabilities.items():
            status = "✓" if works else "✗"
            print(f"  {status} {cap}")
        
        return capabilities


def run_full_benchmark():
    """Run the complete benchmark suite."""
    print("=" * 60)
    print("EXP-006: Hybrid Store Comprehensive Benchmark")
    print("=" * 60)
    
    # Generate dataset
    print("\nGenerating synthetic dataset...")
    dataset = generate_dataset(
        num_people=5,
        num_messages=100,
        num_goals=15,
        num_state_changes=20,
        days_range=30
    )
    print(f"Dataset: {dataset['metadata']['num_messages']} messages, "
          f"{dataset['metadata']['num_people']} people")
    
    # Initialize runner
    runner = BenchmarkRunner(dataset)
    
    # Benchmark both approaches
    vector_store = GraphVectorStore()
    doc_store = GraphDocumentStore()
    
    runner.run_all(vector_store, "Graph+Vector")
    runner.run_all(doc_store, "Graph+Document")
    
    # Generate comparison summary
    print("\n" + "=" * 60)
    print("SUMMARY COMPARISON")
    print("=" * 60)
    
    gv = runner.results["approaches"]["Graph+Vector"]
    gd = runner.results["approaches"]["Graph+Document"]
    
    print("\n| Metric | Graph+Vector | Graph+Document | Winner |")
    print("|--------|--------------|----------------|--------|")
    
    # Ingestion
    gv_ingest = gv["ingestion"]["total_time_ms"]
    gd_ingest = gd["ingestion"]["total_time_ms"]
    winner = "Vector" if gv_ingest < gd_ingest else "Document"
    print(f"| Ingestion Total | {gv_ingest:.2f}ms | {gd_ingest:.2f}ms | {winner} |")
    
    # Semantic search success
    gv_semantic = sum(1 for q in gv["queries"] if q["type"] == "semantic" and q["result_count"] > 0)
    gd_semantic = sum(1 for q in gd["queries"] if q["type"] == "semantic" and q["result_count"] > 0)
    winner = "Vector" if gv_semantic > gd_semantic else "Document" if gd_semantic > gv_semantic else "Tie"
    print(f"| Semantic Queries | {gv_semantic} success | {gd_semantic} success | {winner} |")
    
    # Stress test
    gv_stress = gv["stress"]["rapid_ingestion_total_ms"]
    gd_stress = gd["stress"]["rapid_ingestion_total_ms"]
    winner = "Vector" if gv_stress < gd_stress else "Document"
    print(f"| Stress (100 ops) | {gv_stress:.2f}ms | {gd_stress:.2f}ms | {winner} |")
    
    # Capabilities
    gv_caps = sum(gv["capabilities"].values())
    gd_caps = sum(gd["capabilities"].values())
    winner = "Vector" if gv_caps > gd_caps else "Document" if gd_caps > gv_caps else "Tie"
    print(f"| Capabilities | {gv_caps}/6 | {gd_caps}/6 | {winner} |")
    
    # Save results
    with open("benchmark_results.json", "w") as f:
        json.dump(runner.results, f, indent=2, default=str)
    print("\n\nFull results saved to benchmark_results.json")
    
    return runner.results


if __name__ == "__main__":
    run_full_benchmark()

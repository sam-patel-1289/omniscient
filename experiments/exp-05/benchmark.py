import time
import json
import statistics
from graph_store import GraphContextStore
from vector_store import VectorContextStore

class Benchmark:
    def __init__(self):
        print("Loading Data...")
        with open("experiments/exp-05/data/synthetic_dataset.json", "r") as f:
            self.data = json.load(f)

        self.graph_store = GraphContextStore()
        # Use a fresh persistent path for benchmark to avoid consistency test data
        self.vector_store = VectorContextStore(persistence_path="experiments/exp-05/chroma_benchmark")
        self.vector_store.reset()

    def benchmark_write(self):
        print("\n--- Benchmark: Write Speed ---")

        # Graph
        start = time.time()
        self.graph_store.ingest(self.data)
        graph_time = time.time() - start
        print(f"Graph Write Time: {graph_time:.4f}s")

        # Vector
        start = time.time()
        self.vector_store.ingest(self.data)
        vector_time = time.time() - start
        print(f"Vector Write Time: {vector_time:.4f}s")

        return graph_time, vector_time

    def test_implicit_context(self):
        print("\n--- Test: Implicit Context (The 'Idea Gap') ---")
        goal = "Launch 'Dark Mode' Feature"
        expected_value = "Minimalism"

        # Graph
        start = time.time()
        constraints = self.graph_store.find_implicit_constraints(goal)
        graph_time = time.time() - start
        graph_success = expected_value in constraints
        print(f"Graph: Found {constraints} in {graph_time:.4f}s. Success: {graph_success}")

        # Vector
        start = time.time()
        # We query for the GOAL and hope the retrieved chunks contain the VALUE
        results = self.vector_store.query(f"What are the implicit values for {goal}?", n_results=5)
        vector_time = time.time() - start

        found_values = []
        for r in results:
            meta = r['metadata']
            if meta.get('implied_value') and meta['implied_value'] != "None":
                found_values.append(meta['implied_value'])

        vector_success = expected_value in found_values
        print(f"Vector: Retrieved chunks with values {list(set(found_values))} in {vector_time:.4f}s. Success: {vector_success}")

    def test_temporal_context(self):
        print("\n--- Test: Temporal Query ---")
        query = "How did Sam feel during the Budget Review?"
        target_sentiment = "Determination" # From dataset

        # Graph (Manual traversal logic needed, but let's assume we implement a specific 'get_event_sentiment' or similar)
        # For this benchmark, we'll simulate a path search: Person -> Event(Budget Review) -> Message -> Sentiment
        start = time.time()
        found_sentiment = None
        # traversing...
        for n in self.graph_store.graph.nodes:
            if self.graph_store.graph.nodes[n].get('type') == 'Event' and 'Review' in str(self.graph_store.graph.nodes[n].get('description')):
                 # find related messages
                 pass
        # (Simplification: Graph requires writing specific traversal code for every query type.
        # Vector is 'fuzzy' but easier to query.)
        print("Graph: [Complexity Penalty] Requires writing custom traversal code for 'during event X'.")

        # Vector
        start = time.time()
        results = self.vector_store.query(query, n_results=3)
        vector_time = time.time() - start

        retrieved_sentiments = [r['metadata'].get('sentiment') for r in results]
        print(f"Vector: Retrieved {retrieved_sentiments} in {vector_time:.4f}s.")

    def run(self):
        self.benchmark_write()
        self.test_implicit_context()
        self.test_temporal_context()

if __name__ == "__main__":
    b = Benchmark()
    b.run()

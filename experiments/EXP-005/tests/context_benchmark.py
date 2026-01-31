import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from vector_store import VectorStore
from graph_store import GraphStore

def run_benchmark():
    print("Initializing Stores...")
    vector_db = VectorStore()
    graph_db = GraphStore()

    # Data
    # Graph requires explicit structure
    graph_db.add("User", "HAS_MOOD", "Happy")
    graph_db.add("User", "HAS_JOB", "Engineer")
    
    # Vector just takes text chunks
    docs = [
        "I started my new job as an Engineer last month.",
        "I feel really happy about the work environment.",
        "The weather is sunny today.",
        "My mood has improved since starting work."
    ]
    for d in docs:
        vector_db.add(d)

    query = "How has my mood changed since I started my job?"
    print(f"\nQuery: '{query}'")

    print("\n--- Graph Search ---")
    # Graph needs explicit entity extraction (simulated here)
    # The query mentions "mood" and "job", but doesn't have the specific nodes "Happy" or "Engineer"
    entities = ["User", "Mood", "Job"] 
    graph_results = graph_db.retrieve(entities)
    print("Graph Retrieved (Entities: User, Mood, Job):")
    if not graph_results:
        print("  (No direct edges found connecting these exact concepts in a useful way)")
    for r in graph_results:
        print(f"  - {r}")

    print("\n--- Vector Search ---")
    vector_results = vector_db.search(query)
    print("Vector Retrieved (Similarity):")
    for r in vector_results:
        print(f"  - {r}")

    print("\n--- Conclusion ---")
    if len(vector_results) > 0:
        print("Vector search successfully retrieved context via semantic similarity.")
    else:
        print("Vector search failed.")

if __name__ == "__main__":
    run_benchmark()

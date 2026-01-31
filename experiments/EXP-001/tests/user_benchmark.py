import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from stores.json_store import JsonStore
from stores.graph_store import GraphStore

def run_benchmark():
    print("=== EXP-001: Graph vs Doc Store Benchmark ===\n")

    # 1. Setup
    json_store = JsonStore()
    graph_store = GraphStore()

    # 2. Ingest
    # Story: "My sister lives in Austin." + "I'm visiting the capital of Texas." + "I bought coffee at Starbucks."
    
    # JSON Ingestion (Raw Text)
    json_payload = [
        "My sister lives in Austin.",
        "I'm visiting the capital of Texas.",
        "I bought coffee at Starbucks."
    ]
    for p in json_payload:
        json_store.add(p)

    # Graph Ingestion (Simulated Extraction)
    # We assume an Entity Extractor resolved "Capital of Texas" -> "Austin" and "Starbucks" -> "Starbucks"
    # and "My sister" -> "Sister".
    # Edges:
    graph_store.add("Sister", "lives_in", "Austin")
    graph_store.add("Me", "visiting", "Austin")
    graph_store.add("Austin", "is_capital_of", "Texas")
    graph_store.add("Me", "bought", "Coffee")
    graph_store.add("Me", "at", "Starbucks")
    # Redundant edge for "visiting" just in case
    graph_store.add("Me", "visiting", "Texas") # Loose inference often added in graphs

    print("--- Ingestion Complete ---")
    print(f"JSON Store: {len(json_store.facts)} docs")
    print(f"Graph Store: {len(graph_store.adj)} nodes\n")

    # 3. Query 1: Recall "Where did I get coffee?"
    print("--- Query 1: 'Where did I get coffee?' ---")
    
    # JSON Retrieval
    # Keywords: "coffee"
    j_res_1 = json_store.retrieve("coffee")
    print(f"[JSON] Result: {j_res_1}")

    # Graph Retrieval
    # Entities: "Me", "Coffee"
    g_res_1 = graph_store.retrieve(["Me", "Coffee"])
    print(f"[Graph] Result: {g_res_1}")
    print("")

    # 4. Query 2: Inference "Who am I visiting in Texas?"
    print("--- Query 2: 'Who am I visiting in Texas?' ---")

    # JSON Retrieval
    # Keywords: "visiting", "Texas"
    j_res_2 = json_store.retrieve("visiting Texas")
    print(f"[JSON] Result: {j_res_2}")

    # Graph Retrieval
    # Entities: "Me", "Texas", "Visiting" (Action as entity? or just Me and Texas)
    # Let's try "Me" and "Texas" and "Austin" (if we knew it). 
    # But strictly from query: "Me", "Texas".
    g_res_2 = graph_store.retrieve(["Me", "Texas"])
    print(f"[Graph] Result: {g_res_2}")

    # Analysis Helper
    # We want to know if we found "Sister".
    # Graph 1-hop from "Me" -> "visiting" -> "Austin".
    # Graph 1-hop from "Texas" -> "is_capital_of" -> "Austin".
    # Neither strictly returns "Sister" in 1 hop.
    # But let's see if we hit the "common node" Austin.
    
    # If we expanded 2 hops on the Graph results...
    # (Not implemented in store, but simulating analysis)
    print("\n[Analysis Note]: Does Graph result link to 'Sister'?")
    has_austin = any("Austin" in r for r in g_res_2)
    if has_austin:
        print("Graph retrieved 'Austin'. A 2nd hop would reveal: 'Sister lives_in Austin'.")
    else:
        print("Graph did not retrieve 'Austin'.")

if __name__ == "__main__":
    run_benchmark()

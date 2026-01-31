from typing import List, Tuple, Dict, Set

class GraphStore:
    def __init__(self):
        # Adjacency list: node -> [(relation, target_node)]
        self.adj: Dict[str, List[Tuple[str, str]]] = {}

    def add(self, source: str, relation: str, target: str):
        """Add a directed edge: source -[relation]-> target"""
        if source not in self.adj:
            self.adj[source] = []
        if target not in self.adj:
            self.adj[target] = []
            
        # Avoid duplicates
        if (relation, target) not in self.adj[source]:
            self.adj[source].append((relation, target))

    def retrieve(self, query_entities: List[str]) -> List[str]:
        """
        Finds 1-hop edges connected to any of the query entities (incoming or outgoing).
        Returns them as strings "Source Relation Target".
        """
        results = set()
        # Normalized lookup
        query_set = {e.lower() for e in query_entities}
        
        # Scan all edges (simple for small scale)
        for source, edges in self.adj.items():
            for relation, target in edges:
                if source.lower() in query_set or target.lower() in query_set:
                    results.add(f"{source} {relation} {target}")
                    
        return list(results)

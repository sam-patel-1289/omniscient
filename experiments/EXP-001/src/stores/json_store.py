from typing import List

class JsonStore:
    def __init__(self):
        self.facts = []

    def add(self, text: str):
        """Store a raw text fact."""
        self.facts.append(text)

    def retrieve(self, query: str) -> List[str]:
        """
        Simple keyword search. 
        Returns any fact that contains words from the query (ignoring stop words).
        """
        stop_words = {"where", "did", "i", "get", "who", "am", "visiting", "in", "the", "a", "at"}
        query_words = [w.lower().strip("?") for w in query.split() if w.lower() not in stop_words]
        
        results = []
        for fact in self.facts:
            # If any significant query word is in the fact, retrieve it
            if any(qw in fact.lower() for qw in query_words):
                results.append(fact)
        
        return results

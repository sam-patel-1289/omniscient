import math
from typing import List, Dict

class VectorStore:
    def __init__(self):
        # Text -> Vector
        self.store: Dict[str, List[float]] = {}
        # Pre-defined dummy embeddings for keywords to simulate semantic similarity
        # Dimensions: [Positivity/Mood, Professional/Work, Environmental/Nature]
        self.vocab = {
            "mood": [1.0, 0.0, 0.0],
            "happy": [0.9, 0.1, 0.0],
            "sad": [0.8, -0.2, 0.0],
            "improved": [0.5, 0.0, 0.0], # Positive change
            "job": [0.0, 1.0, 0.0],
            "work": [0.0, 0.9, 0.1],
            "engineer": [0.0, 0.9, 0.0],
            "career": [0.0, 0.8, 0.2],
            "weather": [0.0, 0.0, 1.0],
            "sun": [0.1, 0.0, 0.9]
        }

    def _get_embedding(self, text: str) -> List[float]:
        """Simple bag-of-words mean embedding based on dummy vocab"""
        words = text.lower().replace("?", "").replace(".", "").split()
        vec = [0.0, 0.0, 0.0]
        count = 0
        for w in words:
            if w in self.vocab:
                v = self.vocab[w]
                vec[0] += v[0]
                vec[1] += v[1]
                vec[2] += v[2]
                count += 1
        
        if count == 0:
            return [0.0, 0.0, 0.0]
        
        return [x / count for x in vec]

    def add(self, text: str):
        self.store[text] = self._get_embedding(text)

    def search(self, query: str, top_k: int = 3) -> List[str]:
        q_vec = self._get_embedding(query)
        if q_vec == [0.0, 0.0, 0.0]:
            return []

        scores = []
        for text, vec in self.store.items():
            # Cosine similarity
            dot = sum(a * b for a, b in zip(q_vec, vec))
            norm_q = math.sqrt(sum(a * a for a in q_vec))
            norm_v = math.sqrt(sum(a * a for a in vec))
            
            if norm_q * norm_v == 0:
                sim = 0
            else:
                sim = dot / (norm_q * norm_v)
            
            scores.append((sim, text))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        # Filter for somewhat relevant results
        return [text for sim, text in scores[:top_k] if sim > 0.01]

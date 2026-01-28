import chromadb
from chromadb.utils import embedding_functions
import json
import os
from sentence_transformers import SentenceTransformer

class VectorContextStore:
    def __init__(self, persistence_path="experiments/exp-05/chroma_db"):
        self.client = chromadb.PersistentClient(path=persistence_path)

        # We use a custom embedding function wrapper for SentenceTransformer
        # or we can use Chroma's built-in if compatible.
        # For control, I'll instantiate the model myself.
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        self.collection = self.client.get_or_create_collection(
            name="human_context",
            metadata={"hnsw:space": "cosine"}
        )

    def _serialize_to_text(self, record):
        """
        Converts a JSON record into a semantic string for embedding.
        """
        text = f"[{record['type']}] {record.get('timestamp', '')} "

        if record['type'] == 'Communication':
            text += f"{record.get('actor_name')} via {record.get('channel')}: \"{record.get('content')}\". "
            text += f"Sentiment: {record['metadata'].get('sentiment')}. "

        elif record['type'] == 'Episodic':
            text += f"{record.get('event_type')}: {record.get('description')}. "
            text += f"Participants: {', '.join(record['metadata'].get('participants', []))}. "

        elif record['type'] == 'Intent':
            text += f"Goal: {record.get('goal_name')}. {record.get('description')}. "
            text += f"Status: {record.get('status')}. "

        if 'related_goal' in record:
            text += f"Context: Related to {record['related_goal']}."

        return text

    def ingest(self, data):
        """
        Ingests a list of JSON records.
        """
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for record in data:
            text_rep = self._serialize_to_text(record)

            # Flatten metadata for Chroma (it prefers flat dicts of str/int/float)
            meta = {
                "type": record['type'],
                "timestamp": record.get('timestamp', ""),
                "actor_name": record.get('actor_name', ""),
                "related_goal": record.get('related_goal', "None"),
                "json_dump": json.dumps(record) # Store full record to retrieve later
            }
            # Add specific metadata fields that might be useful for filtering
            if 'metadata' in record:
                if 'sentiment' in record['metadata']:
                    meta['sentiment'] = record['metadata']['sentiment']
                if 'implied_value' in record['metadata']:
                    meta['implied_value'] = record['metadata']['implied_value']

            ids.append(record['id'])
            documents.append(text_rep)
            metadatas.append(meta)

            # Compute embedding
            # Note: doing this in batch is faster, but for clarity/simplicity in this loop:
            # We will batch it outside.

        # Batch embedding calculation
        embeddings = self.model.encode(documents).tolist()

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print(f"Ingested {len(ids)} records into Vector Store.")

    def query(self, query_text, n_results=5, filter_criteria=None):
        """
        Queries the store.
        """
        query_embedding = self.model.encode([query_text]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=filter_criteria # e.g., {"type": "Communication"}
        )

        # Format results
        formatted_results = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                })

        return formatted_results

    def reset(self):
        self.client.delete_collection("human_context")
        self.collection = self.client.create_collection("human_context")

# Quick test if run directly
if __name__ == "__main__":
    store = VectorContextStore()

    # Load data
    with open("experiments/exp-05/data/synthetic_dataset.json", "r") as f:
        data = json.load(f)

    store.ingest(data)

    # Test Query
    print("\n--- Query: 'Why did Sam dislike the design?' ---")
    res = store.query("Why did Sam dislike the design?")
    for r in res:
        print(f"[{r['distance']:.4f}] {r['document']}")

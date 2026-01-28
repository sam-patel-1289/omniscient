import time
import uuid
import json
import threading
import queue
import random
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

# --- 1. Data Schema ---

@dataclass
class ContextEvent:
    """
    Represents a unified event for human context (email, message, emotion, etc.)
    """
    content: str
    type: str  # 'email', 'message', 'emotion', 'conversation'
    user_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    embedding: Optional[List[float]] = None

    def to_json(self):
        return json.dumps(asdict(self))

# --- 2. Mock Vector Store ---

class MockVectorStore:
    """
    Simulates a Vector Database like ChromaDB.
    In a real app, this would wrap the DB client.
    """
    def __init__(self):
        self.store: Dict[str, ContextEvent] = {}
        # In a real vector DB, this would be an HNSW index
        # Here we just store the list for brute-force "search"
        self.index: List[ContextEvent] = []
        self.lock = threading.Lock()

    def upsert(self, event: ContextEvent):
        """
        Stores the event and its embedding.
        """
        with self.lock:
            self.store[event.id] = event
            # Simulate indexing time
            time.sleep(0.1)
            self.index.append(event)
            print(f"[DB] Stored event: {event.id} ({event.type})")

    def search(self, query_vector: List[float], limit: int = 3) -> List[ContextEvent]:
        """
        Simulates a semantic search.
        In reality, this computes cosine similarity.
        Here, we just return random results or recent ones for demonstration.
        """
        with self.lock:
            # Simulate search latency
            time.sleep(0.05)
            # Return the most recently added items as "relevant" for this mock
            return sorted(self.index, key=lambda x: x.timestamp, reverse=True)[:limit]

    def count(self) -> int:
        with self.lock:
            return len(self.index)

# --- 3. Async Ingestion Pipeline (Eventual Consistency) ---

class AsyncIngestionPipeline:
    """
    Handles the 'Eventual Consistency' by decoupling ingestion from processing.
    """
    def __init__(self, vector_store: MockVectorStore):
        self.queue = queue.Queue()
        self.vector_store = vector_store
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def ingest(self, content: str, type: str, user_id: str, metadata: Dict = None):
        """
        API Endpoint simulation.
        Returns immediately (Accepted).
        """
        if metadata is None:
            metadata = {}

        # 1. Create Event Object
        event = ContextEvent(
            content=content,
            type=type,
            user_id=user_id,
            metadata=metadata
        )

        # 2. Push to Queue
        self.queue.put(event)
        print(f"[API] Received & Queued: {event.id} - '{content[:30]}...'")
        return event.id

    def _worker_loop(self):
        """
        Background worker that processes the queue.
        """
        print("[Worker] Started.")
        while self.running:
            try:
                # Wait for an item (timeout allows checking self.running)
                event = self.queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                self._process_event(event)
            except Exception as e:
                print(f"[Worker] Error processing {event.id}: {e}")
            finally:
                self.queue.task_done()

    def _process_event(self, event: ContextEvent):
        """
        Simulates Embedding Generation and DB Insertion.
        """
        print(f"[Worker] Processing: {event.id}")

        # 1. Simulate Embedding Generation (Latency)
        # In real life: calls OpenAI or local model
        time.sleep(0.5)
        # Create a fake random vector of dim 4
        event.embedding = [random.random() for _ in range(4)]

        # 2. Store in Vector DB
        self.vector_store.upsert(event)
        print(f"[Worker] Finished: {event.id}")

    def stop(self):
        print("[System] Stopping pipeline...")
        self.running = False
        self.worker_thread.join()

# --- 4. Main Simulation ---

def main():
    print("=== Omniscient EXP-05: Vector Context Store Prototype ===")

    # Setup
    store = MockVectorStore()
    pipeline = AsyncIngestionPipeline(store)

    # Scenario: User sends data
    user_id = "user_123"

    print("\n--- Phase 1: Ingestion ---")
    pipeline.ingest("I am feeling really frustrated with my commute today.", "emotion", user_id, {"sentiment": "negative"})
    pipeline.ingest("Meeting notes: Project Alpha deadline pushed to Friday.", "conversation", user_id, {"participants": ["Sam", "Bob"]})
    pipeline.ingest("Receipt for coffee at Starbucks.", "email", user_id, {"amount": 5.50})

    print("\n--- Phase 2: Immediate Query (The 'Inconsistency' Gap) ---")
    # Immediately check DB - should be empty or partial
    count = store.count()
    print(f"[Query] Items in DB immediately: {count}")
    if count < 3:
        print("(Expected: 0 or low count, proving eventual consistency)")

    print("\n--- Phase 3: Waiting for Consistency ---")
    # Wait for queue to empty
    pipeline.queue.join()
    print("[System] Queue drained.")

    print("\n--- Phase 4: Final Query ---")
    results = store.search([0.1, 0.2, 0.3, 0.4])
    print(f"[Query] Items in DB after processing: {len(results)}")
    for res in results:
        print(f" - Found: [{res.type}] {res.content}")

    # Cleanup
    pipeline.stop()
    print("\n=== Experiment Complete ===")

if __name__ == "__main__":
    main()

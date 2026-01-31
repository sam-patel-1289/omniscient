import time
import threading
import queue
import uuid
import random
from datetime import datetime

# Import our stores
from graph_store import GraphContextStore
from vector_store import VectorContextStore

class EventualConsistencyTest:
    def __init__(self, store_type="graph"):
        self.queue = queue.Queue()
        self.running = True
        self.store_type = store_type

        if store_type == "graph":
            self.store = GraphContextStore()
        else:
            self.store = VectorContextStore(persistence_path="experiments/exp-05/chroma_consistency_test")
            self.store.reset()

        self.marker_id = str(uuid.uuid4())
        self.marker_detected_at = None
        self.marker_injected_at = None

    def worker(self):
        """
        Simulates the background worker processing the queue.
        Has artificial latency to simulate LLM/Embedding calls.
        """
        while self.running or not self.queue.empty():
            try:
                record = self.queue.get(timeout=0.1)

                # Simulate processing time
                # Vector is usually slower (embedding) than Graph (structure)
                delay = 0.05 if self.store_type == "graph" else 0.1
                time.sleep(delay)

                self.store.ingest([record])
                self.queue.task_done()
            except queue.Empty:
                continue

    def producer(self, n_items=50):
        """
        Floods the queue with noise, then injects the marker, then more noise.
        """
        # 1. Pre-noise
        for i in range(n_items // 2):
            self.queue.put(self._create_dummy_record())
            time.sleep(0.01) # Fast inputs

        # 2. Marker Event
        marker = self._create_dummy_record()
        marker['id'] = self.marker_id
        marker['content'] = "CRITICAL UPDATE: User is now furious."
        marker['metadata']['sentiment'] = "Furious"

        print(f"[{datetime.now().time()}] Injecting Marker Event...")
        self.marker_injected_at = time.time()
        self.queue.put(marker)

        # 3. Post-noise
        for i in range(n_items // 2):
            self.queue.put(self._create_dummy_record())
            time.sleep(0.01)

    def _create_dummy_record(self):
        return {
            "id": str(uuid.uuid4()),
            "type": "Communication",
            "timestamp": datetime.now().isoformat(),
            "actor_name": "Test User",
            "channel": "Slack",
            "content": "Just generating some load for the system.",
            "related_goal": "Stress Test",
            "metadata": {
                "sentiment": "Neutral",
                "implied_value": "None"
            }
        }

    def monitor(self):
        """
        Polls the store to see when the marker appears.
        """
        while self.running:
            start_query = time.time()
            found = False

            if self.store_type == "graph":
                # Check if node exists
                if self.marker_id in self.store.graph:
                    found = True
            else:
                # Query vector
                res = self.store.query("User is now furious", n_results=1)
                if res and "furious" in res[0]['document'].lower():
                    found = True

            if found:
                self.marker_detected_at = time.time()
                print(f"[{datetime.now().time()}] Marker Detected!")
                self.running = False # Stop the test
                break

            time.sleep(0.1) # Poll interval

    def run(self):
        print(f"--- Starting Consistency Test ({self.store_type.upper()}) ---")

        t_worker = threading.Thread(target=self.worker)
        t_monitor = threading.Thread(target=self.monitor)
        t_producer = threading.Thread(target=self.producer)

        t_worker.start()
        t_monitor.start()
        t_producer.start()

        t_producer.join() # Wait for producer to finish writing
        # Worker and Monitor will stop when Monitor finds the marker sets running=False

        t_monitor.join(timeout=10)
        self.running = False # Ensure worker stops if monitor timed out
        t_worker.join()

        if self.marker_detected_at:
            lag = self.marker_detected_at - self.marker_injected_at
            print(f"RESULTS: Consistency Lag = {lag:.4f} seconds")
            return lag
        else:
            print("RESULTS: Timed out waiting for consistency.")
            return -1

if __name__ == "__main__":
    # Run Graph Test
    test_graph = EventualConsistencyTest("graph")
    test_graph.run()

    print("\n" + "="*30 + "\n")

    # Run Vector Test
    test_vector = EventualConsistencyTest("vector")
    test_vector.run()

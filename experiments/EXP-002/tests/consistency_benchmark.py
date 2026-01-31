import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from slow_db import SlowDB
from queue_worker import QueueWorker
from agent_simulator import AgentSimulator

def run_benchmark():
    print("=== Starting EXP-002 Consistency Benchmark ===")
    
    # 1. Setup
    # Latency 3s to be safe and observable
    db = SlowDB(latency=3.0)
    worker = QueueWorker(db)
    agent = AgentSimulator(db, worker)
    
    worker.start()

    try:
        # 2. Update
        print("\n--- Step 1: Agent updates state ---")
        agent.update_memory("mood", "Happy")
        
        # 3. Immediate Query
        print("\n--- Step 2: Immediate Query (Expect Cache Hit) ---")
        val, source = agent.recall_memory("mood")
        print(f"Result: {val} (Source: {source})")
        
        if val == "Happy" and source == "cache":
            print("✅ SUCCESS: Immediate consistency achieved via Cache.")
        else:
            print(f"❌ FAILURE: Expected 'Happy' from 'cache', got '{val}' from '{source}'")

        # Verify DB is currently empty/stale (optional but good for proof)
        db_val = db.read("mood")
        if db_val is None:
             print("ℹ️ Verified: DB is still empty (Async write pending).")
        else:
             print(f"⚠️ Warning: DB already has data? That was too fast. Val: {db_val}")

        # 4. Wait for Consistency
        print("\n--- Step 3: Waiting 5s for Eventual Consistency ---")
        time.sleep(5)
        
        # 5. Query Again (Force DB Read)
        print("\n--- Step 4: Delayed Query (Force DB Read) ---")
        # We clear cache to simulate a new session or another agent
        agent.clear_cache()
        
        val_final, source_final = agent.recall_memory("mood")
        print(f"Result: {val_final} (Source: {source_final})")
        
        if val_final == "Happy" and source_final == "db":
            print("✅ SUCCESS: Eventual consistency achieved via DB.")
        else:
            print(f"❌ FAILURE: Expected 'Happy' from 'db', got '{val_final}' from '{source_final}'")

    finally:
        worker.stop()
        print("\n=== Benchmark Complete ===")

if __name__ == "__main__":
    run_benchmark()

import threading
import time
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from vulnerable_store import VulnerableStore
from optimistic_store import OptimisticStore, VersionConflict

NUM_THREADS = 50

def worker_vulnerable(store):
    store.increment()

def worker_optimistic_retry(store, results):
    # Optimistic locking requires the CLIENT (or wrapper) to handle retries
    retries = 0
    while True:
        try:
            store.increment()
            results['success'] += 1
            break
        except VersionConflict:
            retries += 1
            # Optional: exponential backoff could go here
            time.sleep(0.01) 
    results['retries'] += retries

def run_vulnerable_test():
    print("--- Running Vulnerable Store Test ---")
    store = VulnerableStore()
    store.reset()
    
    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker_vulnerable, args=(store,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    final_count = store.get_count()
    print(f"Target: {NUM_THREADS}")
    print(f"Actual: {final_count}")
    
    if final_count < NUM_THREADS:
        print("RESULT: LOST UPDATES DETECTED (VULNERABLE)")
    else:
        print("RESULT: NO UPDATES LOST (Are you lucky?)")
    print("-" * 30)
    return final_count

def run_optimistic_test():
    print("--- Running Optimistic Store Test (with Retry) ---")
    store = OptimisticStore()
    store.reset()
    
    results = {'success': 0, 'retries': 0}
    threads = []
    
    # We use a lock for the results dict just to update the test counters safely, 
    # unrelated to the store logic
    result_lock = threading.Lock()
    
    def safe_worker():
        local_retries = 0
        while True:
            try:
                store.increment()
                with result_lock:
                    results['success'] += 1
                break
            except VersionConflict:
                local_retries += 1
        
        with result_lock:
            results['retries'] += local_retries

    for _ in range(NUM_THREADS):
        t = threading.Thread(target=safe_worker)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    final_count = store.get_count()
    print(f"Target: {NUM_THREADS}")
    print(f"Actual: {final_count}")
    print(f"Total Retries: {results['retries']}")
    
    if final_count == NUM_THREADS:
        print("RESULT: ALL UPDATES SUCCESSFUL (INTEGRITY PRESERVED)")
    else:
        print(f"RESULT: MISMATCH ({final_count})")
    print("-" * 30)
    return final_count

if __name__ == "__main__":
    v_res = run_vulnerable_test()
    o_res = run_optimistic_test()

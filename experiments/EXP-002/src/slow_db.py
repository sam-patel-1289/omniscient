import time
import threading

class SlowDB:
    def __init__(self, latency=2.0):
        self.latency = latency
        self.data = {}
        self.lock = threading.Lock()

    def write(self, key, value):
        """Simulates a slow write operation."""
        # Simulate network/disk latency
        time.sleep(self.latency)
        
        with self.lock:
            self.data[key] = value
            print(f"[SlowDB] Wrote {key}={value}")

    def read(self, key):
        """Simulates a fast read operation."""
        with self.lock:
            return self.data.get(key)

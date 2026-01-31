import json
import time
import os
import random

class VulnerableStore:
    def __init__(self, db_path="vulnerable_counter.json"):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            self._write_state({"count": 0})

    def _read_state(self):
        with open(self.db_path, "r") as f:
            return json.load(f)

    def _write_state(self, state):
        with open(self.db_path, "w") as f:
            json.dump(state, f)

    def increment(self):
        # 1. Read
        state = self._read_state()
        current_count = state["count"]
        
        # 2. Simulate processing time (the "window of vulnerability")
        time.sleep(random.uniform(0.01, 0.05))
        
        # 3. Write
        state["count"] = current_count + 1
        self._write_state(state)
        return state["count"]

    def get_count(self):
        return self._read_state()["count"]

    def reset(self):
        self._write_state({"count": 0})

import json
import time
import os
import random
import fcntl

class VersionConflict(Exception):
    pass

class OptimisticStore:
    def __init__(self, db_path="optimistic_counter.json"):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump({"count": 0, "version": 0}, f)

    def _read_state(self):
        # Naive read (no lock needed for snapshot, though in real DBs consistency matters)
        # We handle consistency at commit time.
        with open(self.db_path, "r") as f:
            return json.load(f)

    def _commit(self, new_count, expected_version):
        # We need a lock ONLY for the check-and-set operation to simulate an atomic DB instruction
        with open(self.db_path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX) # Exclusive lock for the commit phase
            try:
                content = f.read()
                if not content:
                    current_state = {"count": 0, "version": 0}
                else:
                    current_state = json.loads(content)
                
                if current_state["version"] != expected_version:
                    raise VersionConflict(f"Version mismatch: expected {expected_version}, got {current_state['version']}")
                
                # Update
                current_state["count"] = new_count
                current_state["version"] += 1
                
                f.seek(0)
                json.dump(current_state, f)
                f.truncate()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def increment(self):
        # 1. Read (Snapshot)
        state = self._read_state()
        current_ver = state["version"]
        current_count = state["count"]
        
        # 2. Simulate processing time (Work)
        time.sleep(random.uniform(0.01, 0.05))
        
        # 3. Attempt Commit (Optimistic Check)
        self._commit(current_count + 1, current_ver)
        return current_count + 1

    def get_count(self):
        return self._read_state()["count"]

    def reset(self):
        with open(self.db_path, "w") as f:
            json.dump({"count": 0, "version": 0}, f)

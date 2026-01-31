class AgentSimulator:
    def __init__(self, db, worker):
        self.db = db
        self.worker = worker
        self.local_cache = {}

    def update_memory(self, key, value):
        """
        Updates memory with eventual consistency pattern.
        1. Write to local cache (Immediate)
        2. Push to queue (Async, Slow)
        """
        # 1. Optimistic update
        self.local_cache[key] = value
        print(f"[Agent] Updated local cache: {key}={value}")

        # 2. Async persistence
        self.worker.enqueue_update(key, value)

    def recall_memory(self, key):
        """
        Tries to recall memory.
        1. Check local cache (Fast, Optimistic)
        2. Check DB (Slow, Persistent)
        """
        # 1. Cache hit?
        if key in self.local_cache:
            return self.local_cache[key], "cache"
        
        # 2. Cache miss? Fetch from DB
        val = self.db.read(key)
        if val is not None:
            # Populate cache on read (Read-Through/Lazy Loading)
            self.local_cache[key] = val
            return val, "db"
        
        return None, "miss"

    def clear_cache(self):
        """For testing: force agent to forget local state to test DB consistency."""
        self.local_cache = {}
        print("[Agent] Cleared local cache")

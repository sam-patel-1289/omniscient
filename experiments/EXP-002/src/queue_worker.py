import threading
import queue
import time

class QueueWorker:
    def __init__(self, db_instance):
        self.db = db_instance
        self.queue = queue.Queue()
        self.running = False
        self.worker_thread = None

    def start(self):
        self.running = True
        self.worker_thread = threading.Thread(target=self._process, daemon=True)
        self.worker_thread.start()
        print("[QueueWorker] Started")

    def stop(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1)
        print("[QueueWorker] Stopped")

    def enqueue_update(self, key, value):
        print(f"[QueueWorker] Enqueued update for {key}={value}")
        self.queue.put((key, value))

    def _process(self):
        while self.running:
            try:
                # Timeout allows checking self.running periodically
                task = self.queue.get(timeout=0.5)
                key, value = task
                self.db.write(key, value)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[QueueWorker] Error: {e}")

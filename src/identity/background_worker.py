"""
Background worker for non-blocking identity analysis.

Processes analysis tasks in a separate thread to avoid blocking conversation.
"""

import queue
import threading
import time
from typing import Any, Callable, Optional

from loguru import logger


class BackgroundWorker:
    """Non-blocking background worker for identity analysis tasks"""

    def __init__(self):
        self.task_queue = queue.Queue()
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None

    def start(self):
        """Start the background worker thread"""
        if self.is_running:
            logger.warning("BackgroundWorker already running")
            return

        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("BackgroundWorker started")

    def enqueue_task(
        self, task_type: str, analyzer: Any, data: Any, callback: Callable[[Any], None]
    ):
        """
        Queue a new analysis task.

        Args:
            task_type: Type of analysis (communication_style, beliefs, etc)
            analyzer: Analyzer instance to use
            data: Data to analyze
            callback: Function to call with results
        """
        task = {
            "type": task_type,
            "analyzer": analyzer,
            "data": data,
            "callback": callback,
            "queued_at": time.time(),
        }
        self.task_queue.put(task)
        logger.debug(
            f"Queued {task_type} analysis (queue size: {self.task_queue.qsize()})"
        )

    def _worker_loop(self):
        """Main worker loop - processes tasks from queue"""
        logger.info("Worker loop started")

        while self.is_running:
            try:
                # Wait for task with timeout
                task = self.task_queue.get(timeout=1.0)

                task_type = task["type"]
                analyzer = task["analyzer"]
                data = task["data"]
                callback = task["callback"]

                logger.info(f"Processing {task_type} analysis...")
                start_time = time.time()

                # Run analysis based on type
                try:
                    if task_type == "communication_style":
                        result = analyzer.analyze(data)
                    elif task_type == "beliefs":
                        result = analyzer.extract(data)
                    elif task_type == "thought_patterns":
                        result = analyzer.analyze(data)
                    elif task_type == "memory":
                        result = analyzer.extract(data)
                    else:
                        logger.error(f"Unknown task type: {task_type}")
                        continue

                    elapsed = time.time() - start_time
                    logger.info(f"{task_type} analysis completed in {elapsed:.2f}s")

                    # Call callback with result
                    if callback and result:
                        try:
                            callback(result)
                        except Exception as e:
                            logger.error(f"Callback error for {task_type}: {e}")

                except Exception as e:
                    logger.error(f"Analysis error for {task_type}: {e}")

                self.task_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker loop error: {e}")

        logger.info("Worker loop stopped")

    def stop(self):
        """Stop the background worker"""
        logger.info("Stopping BackgroundWorker...")
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        logger.info("BackgroundWorker stopped")

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.task_queue.qsize()

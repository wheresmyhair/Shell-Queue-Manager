import logging
import queue
import threading
import time
from typing import Dict, List, Optional, Tuple, Any

from shell_queue_manager.core.task import ShellTask
from shell_queue_manager.utils.email import EmailNotifier

logger = logging.getLogger(__name__)


class QueueManager:
    """Manages the queue of shell script tasks."""
    
    def __init__(self):
        self._task_queue = queue.PriorityQueue()
        self._active_tasks: Dict[str, ShellTask] = {}
        self._completed_tasks: Dict[str, ShellTask] = {}
        self._lock = threading.Lock()
        self._task_history: List[str] = []  # Keeps track of task IDs in order
        self._max_history = 1000  # Maximum history to maintain
    
    def add_task(self, task: ShellTask) -> None:
        """Add a task to the queue."""
        with self._lock:
            # Priority: 0 for high, 1 for normal
            priority = 0 if task.priority else 1
            self._task_queue.put((priority, time.time(), task))
            self._task_history.append(task.task_id)
            
            # Maintain history size
            if len(self._task_history) > self._max_history:
                old_id = self._task_history.pop(0)
                if old_id in self._completed_tasks:
                    del self._completed_tasks[old_id]
    
    def get_next_task(self, block: bool = True, timeout: Optional[float] = None) -> Optional[ShellTask]:
        """Get the next task from queue."""
        assert len(self._active_tasks.keys()) == 0, "Cannot get next task when active tasks are present."
        
        try:
            _, _, task = self._task_queue.get(block=block, timeout=timeout)
            
            with self._lock:
                self._active_tasks[task.task_id] = task
            
            return task
        except queue.Empty:
            return None
    
    def mark_task_complete(self, task_id: str, result: Dict[str, Any], success: bool = True) -> None:
        """Mark a task as completed."""
        with self._lock:
            if task_id in self._active_tasks:
                task = self._active_tasks[task_id]
                if result["exit_code"] == -15:
                    task.cancel()
                else:
                    task.complete(result, success)
                self._completed_tasks[task_id] = task
                del self._active_tasks[task_id]
    
    def get_task(self, task_id: str) -> Optional[ShellTask]:
        """Get task by ID from active or completed tasks."""
        if task_id in self._active_tasks:
            logger.debug(f"get task {task_id} in _active_tasks")
            return self._active_tasks[task_id]
        if task_id in self._completed_tasks:
            logger.debug(f"get task {task_id} in _completed_tasks")
            return self._completed_tasks[task_id]
        return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get the current status of the queue."""
        with self._lock:
            return {
                "queue_size": self._task_queue.qsize(),
                "active_tasks": [task.to_dict() for task in self._active_tasks.values()],
                "total_completed": len(self._completed_tasks)
            }
    
    def get_queue_size(self) -> int:
        """Get the current queue size."""
        return self._task_queue.qsize()
    
    def task_done(self) -> None:
        """Mark current task as done in the queue."""
        self._task_queue.task_done()
    
    def clear_queue(self) -> int:
        """Clear all pending tasks from the queue. Returns the number of tasks cleared."""
        count = 0
        with self._lock:
            while not self._task_queue.empty():
                try:
                    self._task_queue.get_nowait()
                    self._task_queue.task_done()
                    count += 1
                except queue.Empty:
                    break
        return count
    
    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently completed tasks."""
        with self._lock:
            recent_ids = self._task_history[-limit:] if limit > 0 else self._task_history
            
        tasks = []
        for task_id in reversed(recent_ids):
            task = self.get_task(task_id)
            if task:
                tasks.append(task.to_dict())
        return tasks
    
    def get_lock(self) -> threading.Lock:
        """Get the queue manager's lock for thread-safe operations."""
        return self._lock

    def abort_task_by_id(self, task_id: str) -> bool:
        """
        Abort a task by its ID.
        
        Args:
            task_id: ID of the task to abort
            
        Returns:
            True if task was found and aborted, False otherwise
        """
        with self._lock:
            # Check if task is currently active
            if task_id in self._active_tasks:
                # Cannot abort active task here, must be done by worker
                return False
            
            # Check if task is in queue
            new_queue = queue.PriorityQueue()
            found = False
            
            while not self._task_queue.empty():
                try:
                    priority, timestamp, task = self._task_queue.get_nowait()
                    
                    if task.task_id == task_id:
                        # Mark task as canceled
                        task.cancel()
                        # Add to completed tasks
                        self._completed_tasks[task_id] = task
                        found = True
                        self._task_queue.task_done()
                        
                        logger.info(f"Removed task {task_id} from queue")
                    else:
                        # Put back in queue
                        new_queue.put((priority, timestamp, task))
                except queue.Empty:
                    break
            
            # Replace queue with new queue
            self._task_queue = new_queue
            
            return found

    def abort_tasks_by_path(self, script_path: str, email_notifier: EmailNotifier) -> int:
        """
        Abort all tasks matching a script path.
        
        Args:
            script_path: Path of the script to abort
            
        Returns:
            Number of tasks aborted
        """
        with self._lock:
            # Check for queued tasks
            new_queue = queue.PriorityQueue()
            aborted_count = 0
            
            while not self._task_queue.empty():
                try:
                    priority, timestamp, task = self._task_queue.get_nowait()
                    
                    if task.script_path == script_path:
                        # Mark task as canceled
                        task.cancel()
                        # Add to completed tasks
                        self._completed_tasks[task.task_id] = task
                        aborted_count += 1
                        self._task_queue.task_done()
                        email_notifier.send_task_aborted_notification(task.to_dict())
                        
                        logger.info(f"Removed task {task.task_id} from queue (matching path {script_path})")
                    else:
                        # Put back in queue
                        new_queue.put((priority, timestamp, task))
                except queue.Empty:
                    break
            
            # Replace queue with new queue
            self._task_queue = new_queue
            
            return aborted_count
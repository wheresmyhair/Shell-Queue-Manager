import logging
import os
import subprocess
import threading
import time
import io
from typing import Dict, Any, Optional, Callable

from shell_queue_manager.core.queue_manager import QueueManager
from shell_queue_manager.core.task import ShellTask, TaskStatus
from shell_queue_manager.utils.email import EmailNotifier

logger = logging.getLogger(__name__)


class Worker:
    """Worker that processes shell script tasks from the queue."""
    
    def __init__(
        self, 
        queue_manager: QueueManager, 
        email_notifier: Optional[EmailNotifier] = None,
        notify_on_failure: bool = True,
        notify_queue_low_threshold: int = 1
    ):
        """
        Initialize the worker.
        
        Args:
            queue_manager: Queue manager instance
            email_notifier: Email notifier instance
            notify_on_failure: Whether to notify on task failure
            notify_queue_low_threshold: Queue size threshold for low queue notification
        """
        self._queue_manager = queue_manager
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_task: Optional[ShellTask] = None
        self._on_task_start: Optional[Callable[[ShellTask], None]] = None
        self._on_task_complete: Optional[Callable[[ShellTask], None]] = None
        
        # Live output tracking
        self._current_output = ""
        self._process = None
        self._output_thread = None
        
        # Email notification settings
        self._email_notifier = email_notifier
        self._notify_on_failure = notify_on_failure
        self._notify_queue_low_threshold = notify_queue_low_threshold
        self._last_queue_size = 0  # Track queue size for change detection
    
    def start(self) -> None:
        """Start the worker thread."""
        if self._thread is None or not self._thread.is_alive():
            self._running = True
            self._thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._thread.start()
            logger.info("Worker started")
    
    def stop(self) -> None:
        """Stop the worker thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            logger.info("Worker stopped")
    
    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running and self._thread is not None and self._thread.is_alive()
    
    def get_current_task(self) -> Optional[ShellTask]:
        """Get the currently executing task."""
        return self._current_task
    
    def get_current_output(self) -> Dict[str, Any]:
        """Get the current task's output."""
        with self._queue_manager.get_lock():
            return {
                "output": self._current_output,
                "task_id": self._current_task.task_id if self._current_task else None,
                "script_path": self._current_task.script_path if self._current_task else None,
            }
    
    def set_callbacks(
        self,
        on_task_start: Optional[Callable[[ShellTask], None]] = None,
        on_task_complete: Optional[Callable[[ShellTask], None]] = None
    ) -> None:
        """Set callback functions for task events."""
        self._on_task_start = on_task_start
        self._on_task_complete = on_task_complete
    
    def _check_queue_state(self) -> None:
        """Check queue state and send notifications if needed."""
        if not self._email_notifier:
            return
            
        current_size = self._queue_manager.get_queue_size()
        
        # Check for low queue threshold
        if (self._last_queue_size > self._notify_queue_low_threshold and 
            current_size <= self._notify_queue_low_threshold):
            logger.info(f"Queue size reached low threshold: {current_size}")
            self._email_notifier.send_queue_low_notification(current_size)
        
        self._last_queue_size = current_size
    
    def _output_reader_with_file(self, stream, file):
        """Read from a stream line by line, append to the output buffer, and write to file."""
        try:
            for line in iter(stream.readline, ''):
                if line:
                    # Update in-memory buffer
                    with self._queue_manager.get_lock():
                        self._current_output += line
                    
                    # Write to file (no lock needed as file IO is thread-safe)
                    file.write(line)
                    file.flush()  # Ensure output is written immediately
        except Exception as e:
            error_msg = f"Error reading from stream: {e}"
            logger.error(error_msg)
            with self._queue_manager.get_lock():
                self._current_output += f"\n{error_msg}\n"
            file.write(f"\n{error_msg}\n")
            file.flush()
        
    def _worker_loop(self) -> None:
        """Main worker loop that processes tasks from the queue."""
        while self._running:
            try:
                # Check queue state
                self._check_queue_state()
                
                # Get next task
                task = self._queue_manager.get_next_task(block=True, timeout=5)
                
                if task is None:
                    continue
                
                self._current_task = task
                
                # Trigger start callback
                if self._on_task_start:
                    self._on_task_start(task)
                
                # Execute the task
                result = self._execute_script(task)
                
                # Check for task failure and send notification
                success = result.get("exit_code", -1) == 0
                if not success and self._notify_on_failure and self._email_notifier:
                    logger.info(f"Sending notification for failed task: {task.task_id}")
                    self._email_notifier.send_task_failed_notification(result)
                
                # Mark as complete
                self._queue_manager.mark_task_complete(task.task_id, result, success)
                
                # Trigger complete callback
                if self._on_task_complete:
                    self._on_task_complete(task)
                
                # Mark queue task as done
                self._queue_manager.task_done()
                
                with self._queue_manager.get_lock():
                    self._current_task = None
                
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                time.sleep(1)
    
    def _execute_script(self, task: ShellTask) -> Dict[str, Any]:
        """Execute a shell script and return the result."""
        try:
            # Mark task as running
            task.start()
            
            # Reset output buffer
            with self._queue_manager.get_lock():
                self._current_output = ""
            
            # Check if script exists
            if not os.path.isfile(task.script_path):
                raise FileNotFoundError(f"Script not found: {task.script_path}")
            
            # Check if script is executable
            if not os.access(task.script_path, os.X_OK):
                logger.warning(f"Script is not executable: {task.script_path}")
                # Try to make it executable
                try:
                    os.chmod(task.script_path, 0o755)
                except Exception as e:
                    logger.error(f"Failed to make script executable: {e}")
            
            # Create output file path (same path as script but with .log extension)
            output_file = os.path.dirname(task.script_path)+ f'/{task.task_id}.log'
            logger.info(f"Executing script: {task.script_path}, logging to: {output_file}")
            
            # Open output file for writing
            with open(output_file, 'w') as f_output:
                # Execute the shell script and capture output in real-time
                # Redirect stderr to stdout to merge the streams and tee to file
                self._process = subprocess.Popen(
                    ['/bin/bash', task.script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Redirect stderr to stdout
                    text=True,
                    bufsize=1  # Line buffered is sufficient for merged streams
                )
                
                # Setup thread to read merged output in real-time
                self._output_thread = threading.Thread(
                    target=self._output_reader_with_file,
                    args=(self._process.stdout, f_output)
                )
                
                self._output_thread.daemon = True
                self._output_thread.start()
                
                # Wait for process to complete
                exit_code = self._process.wait()
                
                # Wait for reader thread to finish
                if self._output_thread.is_alive():
                    self._output_thread.join(timeout=1.0)
                
                # Ensure we've captured all remaining output
                try:
                    remaining_output, _ = self._process.communicate(timeout=1.0)
                    if remaining_output:
                        with self._queue_manager.get_lock():
                            self._current_output += remaining_output
                        f_output.write(remaining_output)
                except subprocess.TimeoutExpired:
                    logger.warning("Timeout while reading remaining output")
                
            # Get final output
            with self._queue_manager.get_lock():
                output = self._current_output
            
            # Prepare result
            result = {
                "task_id": task.task_id,
                "script_path": task.script_path,
                "exit_code": exit_code,
                "output": output,
                "output_file": output_file  # Add path to the output file
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing script: {e}", exc_info=True)
            return {
                "task_id": task.task_id,
                "script_path": task.script_path,
                "error": str(e),
                "exit_code": -1
            }
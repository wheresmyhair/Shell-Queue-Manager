import pytest

from shell_queue_manager.core.task import ShellTask, TaskStatus

pytestmark = pytest.mark.core


def test_task_creation():
    """Test creating a task."""
    task = ShellTask(script_path="/path/to/script.sh")
    
    assert task.script_path == "/path/to/script.sh"
    assert not task.priority
    assert task.task_id is not None
    assert task.status == TaskStatus.QUEUED
    assert task.result is None

def test_task_lifecycle():
    """Test task lifecycle."""
    task = ShellTask(script_path="/path/to/script.sh")
    
    # Initial state
    assert task.status == TaskStatus.QUEUED
    assert task.started_at is None
    assert task.completed_at is None
    
    # Start task
    task.start()
    assert task.status == TaskStatus.RUNNING
    assert task.started_at is not None
    assert task.completed_at is None
    
    # Complete task
    result = {"exit_code": 0, "stdout": "Success"}
    task.complete(result, success=True)
    assert task.status == TaskStatus.COMPLETED
    assert task.result == result
    assert task.completed_at is not None
    
    # Convert to dict
    task_dict = task.to_dict()
    assert task_dict["task_id"] == task.task_id
    assert task_dict["script_path"] == task.script_path
    assert task_dict["status"] == TaskStatus.COMPLETED.value
    assert task_dict["execution_time"] is not None

def test_task_failure():
    """Test task failure."""
    task = ShellTask(script_path="/path/to/script.sh")
    
    # Start and fail task
    task.start()
    result = {"exit_code": 1, "stderr": "Error"}
    task.complete(result, success=False)
    
    assert task.status == TaskStatus.FAILED
    assert task.result == result

def test_task_cancel():
    """Test task cancellation."""
    task = ShellTask(script_path="/path/to/script.sh")
    
    # Start and cancel task
    task.start()
    task.cancel()
    
    assert task.status == TaskStatus.CANCELED
    assert task.completed_at is not None

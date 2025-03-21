import pytest

from shell_queue_manager.core.queue_manager import QueueManager
from shell_queue_manager.core.task import ShellTask

pytestmark = pytest.mark.core


def test_add_task(queue_manager: QueueManager):
    task = ShellTask(script_path="/path/to/script.sh")
    queue_manager.add_task(task)
    
    assert queue_manager.get_queue_size() == 1


def test_priority_ordering(queue_manager: QueueManager):
    """Test that priority tasks are ordered correctly."""
    task1 = ShellTask(script_path="/path/to/script1.sh", priority=False)
    queue_manager.add_task(task1)
    
    task2 = ShellTask(script_path="/path/to/script2.sh", priority=True)
    queue_manager.add_task(task2)
    
    next_task = queue_manager.get_next_task()
    assert next_task.script_path == "/path/to/script2.sh"
    
    queue_manager.mark_task_complete(next_task.task_id, {"exit_code": 0})
    next_task = queue_manager.get_next_task()
    assert next_task.script_path == "/path/to/script1.sh"


def test_get_task(queue_manager: QueueManager):
    """Test getting a task by ID."""
    task = ShellTask(script_path="/path/to/script.sh")
    queue_manager.add_task(task)
    
    next_task = queue_manager.get_next_task()  # This should mark the task as active
    retrieved_task = queue_manager.get_task(task.task_id)  # Find in active tasks
    
    assert retrieved_task is not None
    assert retrieved_task.task_id == task.task_id
    
    # Mark as complete
    result = {"exit_code": 0}
    queue_manager.mark_task_complete(task.task_id, result)
    
    retrieved_task = queue_manager.get_task(task.task_id)  # Should now be in completed tasks
    assert retrieved_task is not None
    assert retrieved_task.task_id == task.task_id


def test_cannot_get_next_task_with_active_tasks(queue_manager: QueueManager):
    """Test that get_next_task raises an exception when there are active tasks."""
    task = ShellTask(script_path="/path/to/script.sh")
    queue_manager.add_task(task)
    
    queue_manager.get_next_task()
    with pytest.raises(AssertionError, match="Cannot get next task when active tasks are present."):
        queue_manager.get_next_task()


def test_clear_queue(queue_manager: QueueManager):
    for i in range(5):
        task = ShellTask(script_path=f"/path/to/script{i}.sh")
        queue_manager.add_task(task)
    
    assert queue_manager.get_queue_size() == 5
    
    cleared = queue_manager.clear_queue()
    
    assert cleared == 5
    assert queue_manager.get_queue_size() == 0


def test_get_recent_tasks(queue_manager: QueueManager):
    for i in range(15):
        task = ShellTask(script_path=f"/path/to/script{i}.sh")
        queue_manager.add_task(task)
    
    for i in range(15):
        next_task = queue_manager.get_next_task()
        result = {"exit_code": 0}
        queue_manager.mark_task_complete(next_task.task_id, result)
    
    recent_tasks = queue_manager.get_recent_tasks(limit=10)
    assert len(recent_tasks) == 10
    assert recent_tasks[0]["script_path"] == "/path/to/script14.sh"
    assert recent_tasks[-1]["script_path"] == "/path/to/script5.sh"


def test_get_recent_tasks_with_no_tasks(queue_manager: QueueManager):
    """Test get_recent_tasks when there are no tasks."""
    recent_tasks = queue_manager.get_recent_tasks(limit=10)
    assert len(recent_tasks) == 0
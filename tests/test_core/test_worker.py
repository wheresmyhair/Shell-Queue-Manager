from unittest.mock import MagicMock

import pytest

from shell_queue_manager.core.queue_manager import QueueManager
from shell_queue_manager.core.worker import Worker
from shell_queue_manager.utils.email import EmailNotifier

pytestmark = pytest.mark.core


@pytest.fixture
def mock_email_notifier() -> EmailNotifier:
    """Create a mock email notifier."""
    notifier = MagicMock()
    notifier.send_queue_low_notification.return_value = True
    notifier.send_task_failed_notification.return_value = True
    return notifier

@pytest.fixture
def worker_with_email(
    queue_manager: QueueManager, 
    mock_email_notifier: EmailNotifier
):
    """Create worker with email notification."""
    worker = Worker(
        queue_manager=queue_manager,
        email_notifier=mock_email_notifier,
        notify_on_failure=True,
        notify_queue_low_threshold=2
    )
    yield worker
    worker.stop()

def test_notification_on_failure(
    worker_with_email: Worker, 
    queue_manager: QueueManager, 
    error_script: str
):
    """Test that an email is sent when a task fails."""
    # Add a failing task
    from shell_queue_manager.core.task import ShellTask
    task = ShellTask(script_path=error_script)
    queue_manager.add_task(task)
    
    # Start worker and wait for execution
    worker_with_email.start()
    import time
    time.sleep(1)  # Give time for execution
    
    # Check that notification was sent
    mock_notifier = worker_with_email._email_notifier
    mock_notifier.send_task_failed_notification.assert_called_once()

def test_notification_on_queue_low(
    worker_with_email: Worker, 
    queue_manager: QueueManager, 
    test_script: str
):
    """Test that an email is sent when queue size reaches threshold."""
    # Add tasks to fill the queue
    from shell_queue_manager.core.task import ShellTask
    for i in range(3):
        task = ShellTask(script_path=test_script)
        queue_manager.add_task(task)
    
    # Initial queue size is above threshold
    worker_with_email._last_queue_size = 3
    
    # Start worker and wait for execution until queue size drops
    worker_with_email.start()
    import time
    time.sleep(2)  # Give time for execution
    
    # Check that notification was sent when queue dropped to threshold
    mock_notifier = worker_with_email._email_notifier
    mock_notifier.send_queue_low_notification.assert_called_once()
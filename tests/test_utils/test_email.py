from unittest.mock import patch, MagicMock

import pytest

from shell_queue_manager.config import _load_private_config
from shell_queue_manager.utils.email import EmailNotifier

pytestmark = pytest.mark.utils


@pytest.fixture
def email_config():
    private_config = _load_private_config()
    """Create test email configuration."""
    return {
        "host": private_config["EMAIL_HOST"],
        "port": private_config["EMAIL_PORT"],
        "username": private_config["EMAIL_USERNAME"],
        "password": private_config["EMAIL_PASSWORD"],
        "sender": private_config["EMAIL_SENDER"],
        "recipients": private_config["EMAIL_RECIPIENTS"],
        "use_tls": private_config["EMAIL_USE_TLS"],
        "enable": private_config["EMAIL_ENABLED"]
    }

@pytest.fixture
def notifier(email_config):
    """Create email notifier instance."""
    return EmailNotifier(
        host=email_config["host"],
        port=email_config["port"],
        username=email_config["username"],
        password=email_config["password"],
        sender=email_config["sender"],
        recipients=email_config["recipients"],
        use_tls=email_config["use_tls"],
        enable=email_config["enable"]
    )

@patch("smtplib.SMTP")
def test_send_queue_low_notification(
    mock_smtp, 
    notifier: EmailNotifier,
    email_config,
):
    """Test sending queue low notification."""
    # Mock SMTP instance
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
    
    # Call method
    result = notifier.send_queue_low_notification(1)
    
    # Assertions
    assert result is True
    mock_smtp.assert_called_once_with(email_config["host"], email_config["port"])
    mock_smtp_instance.ehlo.assert_called()
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with(email_config["username"], email_config["password"])
    mock_smtp_instance.sendmail.assert_called_once()
    
    # Check email content
    call_args = mock_smtp_instance.sendmail.call_args[0]
    assert call_args[0] == email_config["sender"]
    assert call_args[1] == email_config["recipients"]
    assert "[Shell Queue Manager] Queue Running Low" in call_args[2]

@patch("smtplib.SMTP")
def test_send_task_failed_notification(
    mock_smtp, 
    notifier: EmailNotifier,
    email_config,
):
    """Test sending task failed notification."""
    # Mock SMTP instance
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
    
    # Sample task data
    task_data = {
        "task_id": "task123",
        "script_path": "/path/to/script.sh",
        "exit_code": 1,
        "stderr": "Command not found",
        "error": "Script execution failed"
    }
    
    # Call method
    result = notifier.send_task_failed_notification(task_data)
    
    # Assertions
    assert result is True
    mock_smtp.assert_called_once_with(email_config["host"], email_config["port"])
    mock_smtp_instance.sendmail.assert_called_once()
    
    # Check email content
    call_args = mock_smtp_instance.sendmail.call_args[0]
    assert "[Shell Queue Manager] Task Failed - task123" in call_args[2]
    assert "Script execution failed" in call_args[2]
    assert "Command not found" in call_args[2]

def test_disabled_notifications(email_config):
    """Test that notifications are not sent when disabled."""
    # Create notifier with disabled notifications
    email_config["enable"] = False
    disabled_notifier = EmailNotifier(**email_config)
    
    # Call methods
    with patch("smtplib.SMTP") as mock_smtp:
        queue_result = disabled_notifier.send_queue_low_notification(1)
        task_result = disabled_notifier.send_task_failed_notification({"task_id": "task123"})
    
    # Assertions
    assert queue_result is False
    assert task_result is False
    mock_smtp.assert_not_called()

@patch("smtplib.SMTP")
def test_error_handling(mock_smtp, notifier):
    """Test error handling during email sending."""
    # Mock SMTP to raise an exception
    mock_smtp.return_value.__enter__.side_effect = Exception("Connection failed")
    
    # Call method
    result = notifier.send_queue_low_notification(1)
    
    # Assertions
    assert result is False
    
def test_do_send_queue_low_notification(notifier: EmailNotifier):
    """Test sending queue low notification out."""
    result = notifier.send_queue_low_notification(1)
    assert result is True
    
def test_do_send_task_failed_notification(notifier: EmailNotifier):
    """Test sending task failed notification out."""
    task_data = {
        "task_id": "test_task123",
        "script_path": "/path/to/script.sh",
        "exit_code": 1,
        "stderr": "Command not found",
        "error": "Script execution failed (intended)"
    }
    
    result = notifier.send_task_failed_notification(task_data)
    assert result is True
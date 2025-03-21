import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Email notification utility for the Shell Queue Manager."""
    
    def __init__(self, 
                host: str, 
                port: int, 
                username: str, 
                password: str, 
                sender: str, 
                recipients: List[str],
                use_tls: bool = True,
                enable: bool = True):
        """
        Initialize the email notifier.
        
        Args:
            host: SMTP server hostname
            port: SMTP server port
            username: SMTP authentication username
            password: SMTP authentication password
            sender: Sender email address
            recipients: List of recipient email addresses
            use_tls: Whether to use TLS encryption
            enable: Whether email notifications are enabled
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender
        self.recipients = recipients
        self.use_tls = use_tls
        self.enable = enable
    
    def send_queue_low_notification(self, remaining_tasks: int) -> bool:
        """
        Send notification when queue is running low on tasks.
        
        Args:
            remaining_tasks: Number of remaining tasks in queue
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enable:
            logger.info("Email notifications disabled. Skipping queue low notification.")
            return False
        
        subject = f"[Shell Queue Manager] Queue Running Low - {remaining_tasks} task(s) remaining"
        
        html_content = f"""
        <html>
        <body>
            <h2>Shell Queue Manager Alert</h2>
            <p>The task queue is running low.</p>
            
            <h3>Details:</h3>
            <ul>
                <li><strong>Remaining Tasks:</strong> {remaining_tasks}</li>
                <li><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
            
            <p>This is an automated notification from your Shell Queue Manager.</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Shell Queue Manager Alert
        
        The task queue is running low.
        
        Details:
        - Remaining Tasks: {remaining_tasks}
        - Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        This is an automated notification from your Shell Queue Manager.
        """
        
        return self._send_email(subject, text_content, html_content)
    
    def send_task_failed_notification(self, task: Dict[str, Any]) -> bool:
        """
        Send notification when a task fails.
        
        Args:
            task: Task information dictionary
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enable:
            logger.info("Email notifications disabled. Skipping task failed notification.")
            return False
        
        subject = f"[Shell Queue Manager] Task Failed - {task.get('task_id', 'Unknown')}"
        
        # Prepare error details
        error_msg = task.get('error', 'No error details available')
        stderr = task.get('stderr', 'No stderr output available')
        exit_code = task.get('exit_code', 'Unknown')
        
        html_content = f"""
        <html>
        <body>
            <h2>Shell Queue Manager Alert</h2>
            <p>A task has failed execution.</p>
            
            <h3>Task Details:</h3>
            <ul>
                <li><strong>Task ID:</strong> {task.get('task_id', 'Unknown')}</li>
                <li><strong>Script Path:</strong> {task.get('script_path', 'Unknown')}</li>
                <li><strong>Exit Code:</strong> {exit_code}</li>
                <li><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
            
            <h3>Error Information:</h3>
            <div style="background-color: #f8d7da; padding: 10px; border-radius: 5px;">
                <p><strong>Error:</strong> {error_msg}</p>
            </div>
            
            <h3>Standard Error Output:</h3>
            <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">{stderr}</pre>
            
            <p>This is an automated notification from your Shell Queue Manager.</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Shell Queue Manager Alert
        
        A task has failed execution.
        
        Task Details:
        - Task ID: {task.get('task_id', 'Unknown')}
        - Script Path: {task.get('script_path', 'Unknown')}
        - Exit Code: {exit_code}
        - Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Error Information:
        {error_msg}
        
        Standard Error Output:
        {stderr}
        
        This is an automated notification from your Shell Queue Manager.
        """
        
        return self._send_email(subject, text_content, html_content)
    
    def _send_email(self, subject: str, text_content: str, html_content: Optional[str] = None) -> bool:
        """
        Send an email.
        
        Args:
            subject: Email subject
            text_content: Plain text content
            html_content: HTML content (optional)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender
            message["To"] = ", ".join(self.recipients)
            
            # Add text part
            message.attach(MIMEText(text_content, "plain"))
            
            # Add HTML part if provided
            if html_content:
                message.attach(MIMEText(html_content, "html"))
            
            # Setup SMTP connection
            context = ssl.create_default_context() if self.use_tls else None
            
            if self.use_tls:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(self.username, self.password)
                    server.sendmail(self.sender, self.recipients, message.as_string())
            else:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.login(self.username, self.password)
                    server.sendmail(self.sender, self.recipients, message.as_string())
            
            logger.info(f"Successfully sent email notification: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}", exc_info=True)
            return False
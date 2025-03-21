import logging

from flask import Flask

from shell_queue_manager.api.routes import api_bp
from shell_queue_manager.config import load_config, get_email_config
from shell_queue_manager.core.queue_manager import QueueManager
from shell_queue_manager.core.worker import Worker
from shell_queue_manager.utils.email import EmailNotifier


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    default_config = load_config()
    
    # Apply default configuration
    app.config.from_mapping(default_config)
    
    # Apply custom configuration
    if config:
        app.config.from_mapping(config)
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    
    logger = logging.getLogger(__name__)
    
    # Initialize email notifier
    email_notifier = None
    if app.config.get('EMAIL_ENABLED', False):
        email_config = get_email_config(app.config)
        email_notifier = EmailNotifier(
            host=email_config['host'],
            port=email_config['port'],
            username=email_config['username'],
            password=email_config['password'],
            sender=email_config['sender'],
            recipients=email_config['recipients'],
            use_tls=email_config['use_tls'],
            enable=email_config['enable']
        )
        logger.info("Email notifications enabled")
    else:
        logger.info("Email notifications disabled")
    
    # Initialize core components
    queue_manager = QueueManager()
    worker = Worker(
        queue_manager=queue_manager,
        email_notifier=email_notifier,
        notify_on_failure=app.config.get('NOTIFY_ON_TASK_FAILURE', True),
        notify_queue_low_threshold=app.config.get('NOTIFY_QUEUE_LOW_THRESHOLD', 1)
    )
    
    # Store core components in app config
    app.config['QUEUE_MANAGER'] = queue_manager
    app.config['WORKER'] = worker
    app.config['EMAIL_NOTIFIER'] = email_notifier
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Start worker
    worker.start()
    
    # # Register shutdown handler
    # @app.teardown_appcontext
    # def shutdown_worker(exception=None):
    #     worker = app.config.get('WORKER')
    #     if worker:
    #         worker.stop()
    
    return app
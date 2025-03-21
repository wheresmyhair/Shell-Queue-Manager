import os
import tempfile

import pytest

from shell_queue_manager.core.queue_manager import QueueManager
from shell_queue_manager.core.worker import Worker
from shell_queue_manager.api.app import create_app


def pytest_configure(config: pytest.Config):
    config.addinivalue_line("markers", "dothis: only do this test")
    config.addinivalue_line("markers", "core: core functionality")
    config.addinivalue_line("markers", "utils: utility functions")
    config.addinivalue_line("markers", "api: API endpoints")


@pytest.fixture
def test_script():
    """Create a temporary test script."""
    with tempfile.NamedTemporaryFile(suffix='.sh', delete=False) as temp:
        temp.write(b"""#!/bin/bash\necho "Test script executed successfully"\nexit 0\n""")
        temp_name = temp.name
    
    # Make script executable
    os.chmod(temp_name, 0o755)
    
    yield temp_name
    
    # Cleanup
    if os.path.exists(temp_name):
        os.unlink(temp_name)


@pytest.fixture
def error_script():
    """Create a temporary error script."""
    with tempfile.NamedTemporaryFile(suffix='.sh', delete=False) as temp:
        temp.write(b"""#!/bin/bash\necho "This script will fail"\nexit 1""")
        temp_name = temp.name
    
    # Make script executable
    os.chmod(temp_name, 0o755)
    
    yield temp_name
    
    # Cleanup
    if os.path.exists(temp_name):
        os.unlink(temp_name)


@pytest.fixture
def queue_manager():
    """Create a queue manager instance."""
    return QueueManager()


@pytest.fixture
def worker(queue_manager):
    """Create a worker instance."""
    worker = Worker(queue_manager)
    yield worker
    worker.stop()


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = create_app({
        'TESTING': True,
    })
    
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()
import json
from http import HTTPStatus

import pytest

pytestmark = pytest.mark.api


def test_submit_script(client, test_script):
    """Test submitting a script."""
    response = client.post(
        '/api/submit',
        json={'script_path': str(test_script)}
    )
    
    assert response.status_code == HTTPStatus.CREATED
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'task_id' in data

def test_submit_invalid_script(client):
    """Test submitting an invalid script."""
    response = client.post(
        '/api/submit',
        json={'script_path': '/nonexistent/path.sh'}
    )
    
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_get_status(client):
    """Test getting queue status."""
    response = client.get('/api/status')
    
    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert 'queue_size' in data
    assert 'active_tasks' in data
    assert 'worker_running' in data

def test_task_lifecycle(client, test_script):
    """Test full task lifecycle through API."""
    # Submit task
    response = client.post(
        '/api/submit',
        json={'script_path': test_script}
    )
    data = json.loads(response.data)
    task_id = data['task_id']
    
    # Check status
    import time
    time.sleep(1)
    response = client.get(f'/api/status/{task_id}')
    assert response.status_code == HTTPStatus.OK
    
    data = json.loads(response.data)
    assert data['status'] in ['completed', 'running']
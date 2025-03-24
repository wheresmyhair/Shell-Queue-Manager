import json
import time
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

def test_live_output(client, tmp_path):
    """Test retrieving live output from a running script."""
    # Create a test script that outputs gradually
    script_path = tmp_path / "output_test.sh"
    script_content = """#!/bin/bash
echo "Starting test script"
sleep 1
echo "Step 1 complete"
sleep 1
echo "Step 2 complete"
sleep 1
echo "Script finished"
"""
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    # Submit the script
    response = client.post(
        '/api/submit',
        json={'script_path': str(script_path)}
    )
    
    assert response.status_code == HTTPStatus.CREATED
    data = json.loads(response.data)
    task_id = data['task_id']
    print(data)
    
    # Wait a moment for the script to start running
    time.sleep(1.0)  # Give it a bit more time
    
    # Check live output
    response = client.get('/api/live-output')
    assert response.status_code == HTTPStatus.OK
    
    data = json.loads(response.data)
    print(data)
    assert data['task_id'] == task_id
    assert "Starting test script" in data['output'], f"Expected 'Starting test script' in output, got: {data['output']}"
    
    # Wait a bit and check again to see progression
    time.sleep(2.0)  # Give it a bit more time
    
    response = client.get('/api/live-output')
    assert response.status_code == HTTPStatus.OK
    
    data = json.loads(response.data)
    print(data)
    assert "Step 1 complete" in data['output'], \
        f"Expected 'Step 1 complete' in output, got: {data['output']}"
    
    # Wait for completion
    time.sleep(3)
    
    # Verify the task completed
    response = client.get(f'/api/status/{task_id}')
    assert response.status_code == HTTPStatus.OK
    
    data = json.loads(response.data)
    print(data)
    assert data['status'] == 'completed'
    
    # Check that live output endpoint correctly reports no active task
    time.sleep(0.5)  # Give time for worker to reset state
    response = client.get('/api/live-output')
    assert response.status_code == HTTPStatus.NOT_FOUND
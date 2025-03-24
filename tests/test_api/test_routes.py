import json
import os
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
    
    # Verify output file was created
    output_file = os.path.dirname(script_path) + f"/{task_id}.log"
    assert os.path.exists(output_file), f"Output file not created: {output_file}"
    
    # Check output file contents
    with open(output_file, 'r') as f:
        file_content = f.read()
        assert "Starting test script" in file_content
        assert "Script finished" in file_content
    
    # Check that live output endpoint correctly reports no active task
    time.sleep(0.5)  # Give time for worker to reset state
    response = client.get('/api/live-output')
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_abort_task(client, tmp_path):
    """Test aborting a task by ID."""
    # Create a test script that runs for a while
    script_path = tmp_path / "long_script.sh"
    script_content = """#!/bin/bash
echo "Starting long script"
sleep 10
echo "This should not be printed"
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
    print(data)
    task_id = data['task_id']
    
    # Wait a moment for the script to start running
    time.sleep(1.0)
    
    # Abort the task
    response = client.post(f'/api/tasks/abort/{task_id}')
    assert response.status_code == HTTPStatus.OK
    
    data = json.loads(response.data)
    print(data)
    assert data['status'] == 'success'
    assert 'aborted successfully' in data['message']
    
    # Verify the task was marked as canceled
    time.sleep(0.5)  # Give time for worker to update status
    response = client.get(f'/api/status/{task_id}')
    
    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert data['status'] == 'canceled'

@pytest.mark.dothis
def test_abort_tasks_by_path(client, tmp_path):
    """Test aborting tasks by script path."""
    # Create a test script that will be queued multiple times
    script_path = tmp_path / "duplicate_script.sh"
    script_content = """#!/bin/bash
echo "This script will be aborted"
sleep 5
"""
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    
    # Submit the script multiple times
    for _ in range(3):  # Submit 3 copies of the same script
        response = client.post(
            '/api/submit',
            json={'script_path': str(script_path)}
        )
        assert response.status_code == HTTPStatus.CREATED
    
    # Wait a moment for the first script to start running
    time.sleep(1.0)
    
    # Abort all tasks with this script path
    response = client.post(
        '/api/tasks/abort-by-path',
        json={'script_path': str(script_path)}
    )
    
    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    print(data)
    assert data['status'] == 'success'
    assert data['running_aborted'] is True
    assert data['queued_aborted'] == 2  # 2 queued + 1 running
    
    # Verify queue is now empty
    response = client.get('/api/status')
    assert response.status_code == HTTPStatus.OK
    data = json.loads(response.data)
    assert data['queue_size'] == 0
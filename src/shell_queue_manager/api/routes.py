import logging
import os
from http import HTTPStatus

from flask import Blueprint, request, jsonify, current_app

from shell_queue_manager.api.schemas import (
    TaskSubmitRequest, 
    SubmitResponse, 
    QueueStatusResponse, 
    TaskResponse, 
    TaskListResponse,
    LiveOutputResponse
)
from shell_queue_manager.core.task import ShellTask

logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__)


@api_bp.route('/submit', methods=['POST'])
def submit_script():
    """Submit a shell script to the queue."""
    try:
        # Validate request
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON"}), HTTPStatus.BAD_REQUEST
        
        # Parse and validate request using Pydantic model
        try:
            task_request = TaskSubmitRequest(**data)
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), HTTPStatus.BAD_REQUEST
        
        # Check if script exists
        if not os.path.isfile(task_request.script_path):
            return jsonify({"status": "error", "message": f"File not found: {task.script_path}"}), HTTPStatus.BAD_REQUEST
        
        # Create task
        task = ShellTask(
            script_path=task_request.script_path,
            priority=task_request.priority,
            task_id=task_request.task_id
        )
        
        # Add to queue
        queue_manager = current_app.config['QUEUE_MANAGER']
        queue_manager.add_task(task)
        
        # Start worker if needed
        worker = current_app.config['WORKER']
        if not worker.is_running():
            worker.start()
        
        # Prepare response
        response = SubmitResponse(
            status="success",
            task_id=task.task_id,
            message="Task submitted successfully",
            position=queue_manager.get_queue_size(),
            priority=task.priority
        )
        
        return jsonify(response.model_dump()), HTTPStatus.CREATED
        
    except Exception as e:
        logger.error(f"Error submitting script: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get the status of the queue and running tasks."""
    try:
        queue_manager = current_app.config['QUEUE_MANAGER']
        worker = current_app.config['WORKER']
        
        queue_status = queue_manager.get_queue_status()
        queue_status['worker_running'] = worker.is_running()
        
        return jsonify(queue_status), HTTPStatus.OK
        
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route('/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get the status of a specific task."""
    try:
        queue_manager = current_app.config['QUEUE_MANAGER']
        task = queue_manager.get_task(task_id)
        
        if task:
            return jsonify(task.to_dict()), HTTPStatus.OK
        
        return jsonify({
            "status": "error",
            "message": f"Task {task_id} not found"
        }), HTTPStatus.NOT_FOUND
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route('/tasks/recent', methods=['GET'])
def get_recent_tasks():
    """Get recently completed tasks."""
    try:
        limit = request.args.get('limit', default=10, type=int)
        
        queue_manager = current_app.config['QUEUE_MANAGER']
        tasks = queue_manager.get_recent_tasks(limit)
        
        response = TaskListResponse(
            tasks=tasks,
            count=len(tasks)
        )
        
        return jsonify(response.dict()), HTTPStatus.OK
        
    except Exception as e:
        logger.error(f"Error getting recent tasks: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route('/tasks/clear', methods=['POST'])
def clear_queue():
    """Clear all pending tasks from the queue."""
    try:
        queue_manager = current_app.config['QUEUE_MANAGER']
        count = queue_manager.clear_queue()
        
        return jsonify({
            "status": "success",
            "message": f"Cleared {count} tasks from queue"
        }), HTTPStatus.OK
        
    except Exception as e:
        logger.error(f"Error clearing queue: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route('/live-output', methods=['GET'])
def get_live_output():
    """Get the live output of the currently running task."""
    try:
        worker = current_app.config['WORKER']
        
        if not worker.is_running():
            return jsonify({
                "status": "error",
                "message": "Worker is not running"
            }), HTTPStatus.BAD_REQUEST
        
        current_task = worker.get_current_task()
        if not current_task:
            return jsonify({
                "status": "error",
                "message": "No task is currently running"
            }), HTTPStatus.NOT_FOUND
        
        # Get live output
        output = worker.get_current_output()
        
        # Prepare response
        response = {
            "status": "success",
            "task_id": output["task_id"],
            "script_path": output["script_path"],
            "output": output["output"]
        }
        
        return jsonify(response), HTTPStatus.OK
        
    except Exception as e:
        logger.error(f"Error getting live output: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route('/tasks/abort/<task_id>', methods=['POST'])
def abort_task(task_id):
    """Abort a specific task by ID."""
    try:
        queue_manager = current_app.config['QUEUE_MANAGER']
        worker = current_app.config['WORKER']
        
        # First check if it's the current running task
        current_task = worker.get_current_task()
        if current_task and current_task.task_id == task_id:
            # Abort current task
            success = worker.abort_current_task()
            if success:
                return jsonify({
                    "status": "success",
                    "message": f"Running task {task_id} aborted successfully"
                }), HTTPStatus.OK
        
        # If not running or abort failed, check if it's in queue
        success = queue_manager.abort_task_by_id(task_id)
        if success:
            return jsonify({
                "status": "success",
                "message": f"Queued task {task_id} aborted successfully"
            }), HTTPStatus.OK
        
        return jsonify({
            "status": "error",
            "message": f"Task {task_id} not found or could not be aborted"
        }), HTTPStatus.NOT_FOUND
        
    except Exception as e:
        logger.error(f"Error aborting task: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route('/tasks/abort-by-path', methods=['POST'])
def abort_tasks_by_path():
    """Abort tasks matching a script path."""
    try:
        # Validate request
        data = request.json
        if not data or 'script_path' not in data:
            return jsonify({
                "status": "error", 
                "message": "Missing script_path parameter"
            }), HTTPStatus.BAD_REQUEST
        
        script_path = data['script_path']
        
        queue_manager = current_app.config['QUEUE_MANAGER']
        worker = current_app.config['WORKER']
        
        # First check if it's the current running task
        current_task = worker.get_current_task()
        running_aborted = False
        
        if current_task and current_task.script_path == script_path:
            # Abort current task
            success = worker.abort_current_task()
            running_aborted = success
        
        # Then abort any queued tasks with the same path
        queued_aborted = queue_manager.abort_tasks_by_path(script_path, worker._email_notifier)
        
        if running_aborted or queued_aborted > 0:
            message = []
            if running_aborted:
                message.append("Running task aborted successfully")
            if queued_aborted > 0:
                message.append(f"{queued_aborted} queued task(s) aborted successfully")
                
            return jsonify({
                "status": "success",
                "message": ". ".join(message),
                "running_aborted": running_aborted,
                "queued_aborted": queued_aborted
            }), HTTPStatus.OK
        
        return jsonify({
            "status": "error",
            "message": f"No tasks matching path {script_path} found"
        }), HTTPStatus.NOT_FOUND
        
    except Exception as e:
        logger.error(f"Error aborting tasks: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR
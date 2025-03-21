import logging
from http import HTTPStatus

from flask import Blueprint, request, jsonify, current_app

from shell_queue_manager.api.schemas import (
    TaskSubmitRequest, 
    SubmitResponse, 
    QueueStatusResponse, 
    TaskResponse, 
    TaskListResponse
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

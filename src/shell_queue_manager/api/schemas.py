import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator


class TaskSubmitRequest(BaseModel):
    """Schema for task submission request."""
    script_path: str = Field(..., description="Path to the shell script to execute")
    priority: bool = Field(False, description="If True, the task will be prioritized")
    task_id: Optional[str] = Field(None, description="Custom task ID (generated if not provided)")
    
    @field_validator('script_path')
    def validate_script_path(cls, v):
        """Validate that the script path exists."""
        if not os.path.isfile(v):
            raise ValueError(f"Script not found: {v}")
        return v


class TaskResponse(BaseModel):
    """Schema for task response."""
    task_id: str = Field(..., description="Unique task identifier")
    script_path: str = Field(..., description="Path to the shell script")
    status: str = Field(..., description="Current status of the task")
    priority: bool = Field(..., description="If the task was prioritized")
    created_at: float = Field(..., description="Timestamp when task was created")
    started_at: Optional[float] = Field(None, description="Timestamp when task execution started")
    completed_at: Optional[float] = Field(None, description="Timestamp when task execution completed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result if completed")


class LiveOutputResponse(BaseModel):
    """Schema for live output response."""
    status: str = Field("success", description="Status of the request")
    task_id: str = Field(..., description="ID of the currently running task")
    script_path: str = Field(..., description="Path to the script being executed")
    output: str = Field("", description="Current output from the script (stdout and stderr combined)")


class QueueStatusResponse(BaseModel):
    """Schema for queue status response."""
    queue_size: int = Field(..., description="Number of tasks waiting in queue")
    active_tasks: List[TaskResponse] = Field([], description="Currently running tasks")
    total_completed: int = Field(0, description="Total number of completed tasks")
    worker_running: bool = Field(..., description="Whether worker is running")


class TaskListResponse(BaseModel):
    """Schema for task list response."""
    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    count: int = Field(..., description="Number of tasks in the list")


class SubmitResponse(BaseModel):
    """Schema for task submission response."""
    status: str = Field("success", description="Status of the request")
    task_id: str = Field(..., description="ID of the submitted task")
    message: str = Field("Task submitted successfully", description="Response message")
    position: int = Field(..., description="Position in the queue")
    priority: bool = Field(False, description="Whether the task is prioritized")
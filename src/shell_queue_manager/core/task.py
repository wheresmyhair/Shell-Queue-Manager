import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional


class TaskStatus(Enum):
    """Task execution status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class ShellTask:
    """Shell script task data model."""
    script_path: str
    priority: bool = False
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.QUEUED
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_id": self.task_id,
            "script_path": self.script_path,
            "priority": self.priority,
            "status": self.status.value,
            "result": self.result,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_time": (self.completed_at - self.started_at) if self.completed_at and self.started_at else None
        }
    
    def start(self):
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()
    
    def complete(self, result: Dict[str, Any], success: bool = True):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        self.result = result
        self.completed_at = time.time()

    def cancel(self):
        """Mark task as canceled."""
        self.status = TaskStatus.CANCELED
        self.completed_at = time.time()

    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
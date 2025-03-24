import logging
import os
import sys
import time
from typing import Dict, Any, Optional

from shell_queue_manager.config import load_config
from shell_queue_manager.utils.logger import setup_logger

# Set up logger
logger = logging.getLogger("shell_queue_manager")


def get_api_client(config: Dict[str, Any]):
    """
    Create an API client for the Shell Queue Manager.
    """
    import requests
    from requests.exceptions import RequestException
    
    host = config["HOST"]
    if host == "0.0.0.0":
        host = "127.0.0.1"
    
    class ShellQueueClient:
        def __init__(self, host: str, port: int):
            self.base_url = f"http://{host}:{port}/api"
            
        def submit_script(self, script_path: str, priority: bool = False, task_id: Optional[str] = None) -> Dict[str, Any]:
            """Submit a script to the queue."""
            try:
                response = requests.post(
                    f"{self.base_url}/submit",
                    json={
                        "script_path": script_path,
                        "priority": priority,
                        "task_id": task_id
                    }
                )
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                logger.error(f"Error submitting script: {e}")
                return {"status": "error", "message": str(e)}
        
        def get_status(self) -> Dict[str, Any]:
            """Get the status of the queue and running tasks."""
            try:
                response = requests.get(f"{self.base_url}/status")
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                logger.error(f"Error getting status: {e}")
                return {"status": "error", "message": str(e)}
        
        def get_task_status(self, task_id: str) -> Dict[str, Any]:
            """Get the status of a specific task."""
            try:
                response = requests.get(f"{self.base_url}/status/{task_id}")
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                logger.error(f"Error getting task status: {e}")
                return {"status": "error", "message": str(e)}
        
        def get_recent_tasks(self, limit: int = 10) -> Dict[str, Any]:
            """Get recently completed tasks."""
            try:
                response = requests.get(f"{self.base_url}/tasks/recent", params={"limit": limit})
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                logger.error(f"Error getting recent tasks: {e}")
                return {"status": "error", "message": str(e)}
        
        def clear_queue(self) -> Dict[str, Any]:
            """Clear all pending tasks from the queue."""
            try:
                response = requests.post(f"{self.base_url}/tasks/clear")
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                logger.error(f"Error clearing queue: {e}")
                return {"status": "error", "message": str(e)}
        
        def get_live_output(self) -> Dict[str, Any]:
            """Get the live output of the currently running task."""
            try:
                response = requests.get(f"{self.base_url}/live-output")
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                logger.error(f"Error getting live output: {e}")
                return {"status": "error", "message": str(e)}
        
        def abort_task(self, task_id: str) -> Dict[str, Any]:
            """Abort a specific task by ID."""
            try:
                response = requests.post(f"{self.base_url}/tasks/abort/{task_id}")
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                logger.error(f"Error aborting task: {e}")
                return {"status": "error", "message": str(e)}
        
        def abort_tasks_by_path(self, script_path: str) -> Dict[str, Any]:
            """Abort tasks matching a script path."""
            try:
                response = requests.post(
                    f"{self.base_url}/tasks/abort-by-path",
                    json={"script_path": script_path}
                )
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                logger.error(f"Error aborting tasks by path: {e}")
                return {"status": "error", "message": str(e)}
    
    return ShellQueueClient(host, config["PORT"])

def command_submit(args):
    """Handle the 'submit' command to add a script to the queue."""
    config = load_config()
    client = get_api_client(config)
    
    # Validate script path
    script_path = os.path.abspath(args.script_path)
    if not os.path.isfile(script_path):
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)
    
    # Submit the script
    response = client.submit_script(
        script_path=script_path,
        priority=args.priority,
        task_id=args.task_id
    )
    
    if response["status"] == "success":
        print(f"Task submitted successfully")
        print(f"Task ID: {response['task_id']}")
        print(f"Position in queue: {response['position']}")
        if response["priority"]:
            print("Priority: HIGH")
    else:
        print(f"Error: {response['message']}")
        sys.exit(1)

def command_status(args):
    """Handle the 'status' command to get queue status."""
    config = load_config()
    client = get_api_client(config)
    
    if args.task_id:
        # Get status of a specific task
        response = client.get_task_status(args.task_id)
        
        if "status" in response and response["status"] == "error":
            print(f"Error: {response['message']}")
            sys.exit(1)
        
        print(f"Task ID: {response['task_id']}")
        print(f"Script: {response['script_path']}")
        print(f"Status: {response['status']}")
        
        if response["status"] in ["completed", "failed", "canceled"]:
            if "result" in response and response["result"]:
                print(f"Exit Code: {response['result'].get('exit_code', 'N/A')}")
            
            if response["execution_time"]:
                print(f"Execution Time: {response['execution_time']:.2f} seconds")
            
            # Show output file location if available
            if "result" in response and response["result"] and "output_file" in response["result"]:
                print(f"Output File: {response['result']['output_file']}")
    else:
        # Get overall queue status
        response = client.get_status()
        
        print(f"Queue Size: {response['queue_size']}")
        print(f"Worker Running: {'Yes' if response['worker_running'] else 'No'}")
        print(f"Total Completed Tasks: {response['total_completed']}")
        
        if response['active_tasks']:
            print("\nCurrently Running:")
            for task in response['active_tasks']:
                print(f"  Task ID: {task['task_id']}")
                print(f"  Script: {task['script_path']}")
                print(f"  Started At: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task['started_at']))}")
                print()

def command_list(args):
    """Handle the 'list' command to list recent tasks."""
    config = load_config()
    client = get_api_client(config)
    
    response = client.get_recent_tasks(args.limit)
    
    if "status" in response and response["status"] == "error":
        print(f"Error: {response['message']}")
        sys.exit(1)
    
    if not response["tasks"]:
        print("No recent tasks found.")
        return
    
    print(f"Recent Tasks (Total: {response['count']}):")
    print()
    
    for task in response["tasks"]:
        # Format timestamps
        created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task['created_at']))
        completed_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task['completed_at'])) if task['completed_at'] else "N/A"
        
        print(f"Task ID: {task['task_id']}")
        print(f"Script: {task['script_path']}")
        print(f"Status: {task['status']}")
        print(f"Created: {created_at}")
        print(f"Completed: {completed_at}")
        
        if task["status"] in ["completed", "failed"] and task["result"]:
            print(f"Exit Code: {task['result']['exit_code']}")
        
        print()

def command_clear(args):
    """Handle the 'clear' command to clear the queue."""
    config = load_config()
    client = get_api_client(config)
    
    if args.force or input("Are you sure you want to clear all tasks from the queue? (y/n): ").lower() == 'y':
        response = client.clear_queue()
        
        if response["status"] == "success":
            print(response["message"])
        else:
            print(f"Error: {response['message']}")
            sys.exit(1)
    else:
        print("Operation canceled.")

def command_watch(args):
    """Handle the 'watch' command to watch live output of the current task."""
    config = load_config()
    client = get_api_client(config)
    
    try:
        last_output = ""
        refresh_interval = args.interval
        
        while True:
            response = client.get_live_output()
            
            if "status" in response and response["status"] == "error":
                if "No task is currently running" in response["message"]:
                    print("\nNo task is currently running.")
                    if not args.follow:
                        break
                else:
                    print(f"\nError: {response['message']}")
                    if not args.follow:
                        sys.exit(1)
            else:
                # Clear screen if not in append mode
                if not args.append:
                    os.system('cls' if os.name == 'nt' else 'clear')
                
                # Only print new output in append mode
                if args.append:
                    current_output = response["output"]
                    new_output = current_output[len(last_output):]
                    if new_output:
                        print(new_output, end="", flush=True)
                    last_output = current_output
                else:
                    # Print task info and full output
                    print(f"Task ID: {response['task_id']}")
                    print(f"Script: {response['script_path']}")
                    print("\n--- Output ---\n")
                    print(response["output"])
            
            # Check if we should continue watching
            if not args.follow:
                break
            
            time.sleep(refresh_interval)
            
    except KeyboardInterrupt:
        print("\nWatch stopped.")

def command_abort(args):
    """Handle the 'abort' command to abort tasks."""
    config = load_config()
    client = get_api_client(config)
    
    if args.task_id:
        # Abort a specific task by ID
        response = client.abort_task(args.task_id)
    elif args.script_path:
        # Abort tasks by script path
        script_path = os.path.abspath(args.script_path)
        response = client.abort_tasks_by_path(script_path)
    else:
        print("Error: Either --task-id or --script must be specified.")
        sys.exit(1)
    
    if response["status"] == "success":
        print(response["message"])
    else:
        print(f"Error: {response['message']}")
        sys.exit(1)
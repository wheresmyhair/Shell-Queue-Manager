import logging
import os
import subprocess
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


def validate_script(script_path: str) -> bool:
    """
    Validate that a script exists and is executable.
    
    Args:
        script_path: Path to the shell script
        
    Returns:
        True if the script is valid, False otherwise
    """
    # Check if file exists
    if not os.path.isfile(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
    
    # Check if file is executable
    if not os.access(script_path, os.X_OK):
        logger.warning(f"Script is not executable: {script_path}")
        try:
            # Try to make it executable
            os.chmod(script_path, 0o755)
            logger.info(f"Made script executable: {script_path}")
        except Exception as e:
            logger.error(f"Failed to make script executable: {e}")
            return False
    
    return True


def execute_script(script_path: str, 
                  timeout: Optional[int] = None, 
                  env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Execute a shell script and return the result.
    
    Args:
        script_path: Path to the shell script
        timeout: Timeout in seconds for script execution
        env: Environment variables to pass to the script
        
    Returns:
        Dictionary with execution results
    """
    # Validate script
    if not validate_script(script_path):
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Invalid script: {script_path}",
            "error": f"Script not found or not executable: {script_path}"
        }
    
    try:
        # Create environment
        script_env = os.environ.copy()
        if env:
            script_env.update(env)
        
        # Execute script
        start_time = os.times()
        process = subprocess.Popen(
            ['/bin/bash', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=script_env
        )
        
        # Wait for process to complete with optional timeout
        stdout, stderr = process.communicate(timeout=timeout)
        end_time = os.times()
        
        # Calculate execution time
        user_time = end_time.user - start_time.user
        system_time = end_time.system - start_time.system
        
        return {
            "success": process.returncode == 0,
            "exit_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "user_time": user_time,
            "system_time": system_time,
            "total_time": user_time + system_time
        }
        
    except subprocess.TimeoutExpired:
        # Kill process if timeout
        process.kill()
        stdout, stderr = process.communicate()
        
        return {
            "success": False,
            "exit_code": -1,
            "stdout": stdout,
            "stderr": stderr,
            "error": f"Script execution timed out after {timeout} seconds"
        }
        
    except Exception as e:
        logger.error(f"Error executing script: {e}", exc_info=True)
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
            "error": str(e)
        }


def is_script_safe(script_path: str) -> Tuple[bool, str]:
    """
    Perform basic security checks on a script.
    
    Args:
        script_path: Path to the shell script
        
    Returns:
        Tuple of (is_safe, reason)
    """
    # Check if file exists
    if not os.path.isfile(script_path):
        return False, f"Script not found: {script_path}"
    
    try:
        # Read script content
        with open(script_path, 'r') as f:
            content = f.read()
            
        # Check for potentially dangerous commands
        dangerous_commands = [
            "rm -rf /", "rm -rf /*", "mkfs", "dd if=/dev/zero",
            "> /dev/sda", "fork bomb", ":(){:|:&};:"
        ]
        
        for cmd in dangerous_commands:
            if cmd in content:
                return False, f"Script contains dangerous command: {cmd}"
        
        return True, "Script appears safe"
            
    except Exception as e:
        return False, f"Error checking script: {e}"
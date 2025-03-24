# Shell Queue Manager

A Python service for queueing and executing shell scripts via a REST API.

## Features

- REST API for submitting shell scripts to a queue
- Sequential execution of scripts (no concurrent execution)
- Priority queue support for urgent scripts
- Comprehensive status tracking and querying
- Real-time output monitoring of running scripts
- Task abortion for running or queued scripts
- Modular design for easy maintenance and extension

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/shell-queue-manager.git
cd shell-queue-manager

# Install the package
pip install -e .
```

## Usage

### Running the server

```bash
# Run directly
shell-queue

# With custom options
shell-queue --host 127.0.0.1 --port 8000 --log-file /var/log/shell-queue.log
```

### API Usage

Submit a script:
```bash
curl -X POST http://localhost:5000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"script_path": "/path/to/your/script.sh"}
```

### Response Codes

- `200 OK`: Returns the current output successfully
- `404 Not Found`: No task is currently running
- `400 Bad Request`: Worker is not running
- `500 Internal Server Error`: Server error occurred


Submit a high-priority script:
```bash
curl -X POST http://localhost:5000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"script_path": "/path/to/your/script.sh", "priority": true}'
```

Get queue status:
```bash
curl -X GET http://localhost:5000/api/status
```

Get task status:
```bash
curl -X GET http://localhost:5000/api/status/{task_id}
```

Get live output of the currently running script:
```bash
curl -X GET http://localhost:5000/api/live-output
```

## Real-time Output Monitoring

Shell Queue Manager now supports monitoring the output of currently running scripts in real time. This feature allows you to:

- Check the current output of the running script
- Monitor script progress without waiting for completion
- Debug scripts as they execute

All script output (both stdout and stderr) is automatically saved to a log file with the same name as the script but with a .log extension. For example, if you run `/path/to/script.sh`, the output will be saved to `/path/to/<task_id>.log`.

### Example Usage:

To monitor the output of a script in real-time:

1. Submit a script to the queue:
```bash
curl -X POST http://localhost:5000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"script_path": "/path/to/your/script.sh"}'
```

2. Check the live output as it runs:
```bash
curl -X GET http://localhost:5000/api/live-output
```

3. Poll regularly to see progress:
```bash
# Using watch to poll every 2 seconds
watch -n 2 'curl -s http://localhost:5000/api/live-output'
```

The response will include the current stdout and stderr:
```json
{
  "status": "success",
  "task_id": "12345678-1234-5678-1234-567812345678",
  "script_path": "/path/to/your/script.sh",
  "output": "Starting process...\nInitializing data...\n"
}
```

## Task Abortion

Shell Queue Manager now supports aborting tasks that are either running or queued. This allows you to:

- Cancel a specific task by its ID
- Cancel all tasks matching a specific script path
- Automatically receive email notifications when tasks are aborted

### Example Usage:

To abort a specific task by ID:

```bash
# First, get the task ID from the status endpoint
curl -X GET http://localhost:5000/api/status

# Then abort using the task ID
curl -X POST http://localhost:5000/api/tasks/abort/12345678-1234-5678-1234-567812345678
```

To abort all tasks associated with a specific script:

```bash
curl -X POST http://localhost:5000/api/tasks/abort-by-path \
  -H "Content-Type: application/json" \
  -d '{"script_path": "/path/to/your/script.sh"}'
```

The abort functionality behaves as follows:

- If the task is currently running, the process will be terminated
- If the task is in the queue, it will be removed
- The task status will be marked as "canceled"
- Email notifications will be sent if configured

# Shell Queue Manager CLI Reference

The Shell Queue Manager provides a command-line interface (CLI) for interacting with the queue service without having to use the REST API directly.

## Command Overview

The Shell Queue Manager CLI provides the following commands:

- `shell-queue server` - Run the API server
- `shell-queue config` - Manage configuration
- `shell-queue submit` - Submit a script to the queue
- `shell-queue status` - Get queue status
- `shell-queue list` - List recent tasks
- `shell-queue clear` - Clear all pending tasks
- `shell-queue watch` - Watch live output of the running task
- `shell-queue abort` - Abort a task

Each command has its own set of options and subcommands.

## Server Commands

### Start the server

```bash
shell-queue server [options]
```

Options:
- `--host HOST` - Server binding address (default from config)
- `--port PORT` - Server binding port (default from config)
- `--debug` - Enable debug mode
- `--log-file PATH` - Log file path
- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}` - Log level

## Configuration Commands

### Create a new configuration file

```bash
shell-queue config create [--path PATH] [--non-interactive]
```

Options:
- `--path PATH` - Path to save the configuration file
- `--non-interactive` - Use default values without prompting

### Show current configuration

```bash
shell-queue config show
```

## Client Commands

### Submit a script to the queue

```bash
shell-queue submit SCRIPT_PATH [options]
```

Options:
- `--priority, -p` - Prioritize this task
- `--task-id TASK_ID` - Custom task ID (generated if not provided)

Example:
```bash
shell-queue submit /path/to/script.sh -p
```

### Get queue status

```bash
shell-queue status [options]
```

Options:
- `--task-id TASK_ID, -t TASK_ID` - Task ID to get status for

Examples:
```bash
# Get overall queue status
shell-queue status

# Get status of a specific task
shell-queue status -t 12345678-1234-5678-1234-567812345678
```

### List recent tasks

```bash
shell-queue list [options]
```

Options:
- `--limit N, -n N` - Maximum number of tasks to show (default: 10)

Example:
```bash
shell-queue list -n 5
```

### Clear all pending tasks

```bash
shell-queue clear [options]
```

Options:
- `--force, -f` - Don't ask for confirmation

Example:
```bash
shell-queue clear -f
```

### Watch live output of the current task

```bash
shell-queue watch [options]
```

Options:
- `--interval SECONDS, -i SECONDS` - Refresh interval in seconds (default: 1.0)
- `--follow, -f` - Keep watching until interrupted
- `--append, -a` - Append new output instead of refreshing screen

Examples:
```bash
# Watch live output once
shell-queue watch

# Watch continuously with 2-second refresh
shell-queue watch -f -i 2

# Watch continuously with appending output (good for logging)
shell-queue watch -f -a
```

### Abort a task

```bash
shell-queue abort [options]
```

Options:
- `--task-id TASK_ID, -t TASK_ID` - Task ID to abort
- `--script PATH, -s PATH` - Abort all tasks for this script path

Examples:
```bash
# Abort a specific task
shell-queue abort -t 12345678-1234-5678-1234-567812345678

# Abort all tasks for a specific script
shell-queue abort -s /path/to/script.sh
```

## Standalone CLI Commands

For convenience, you can also use standalone commands for each operation:

- `shell-queue-submit` - Submit a script to the queue
- `shell-queue-status` - Get queue status
- `shell-queue-list` - List recent tasks
- `shell-queue-clear` - Clear all pending tasks
- `shell-queue-watch` - Watch live output of the running task
- `shell-queue-abort` - Abort a task

These standalone commands accept the same options as their counterparts under the main `shell-queue` command.

Example:
```bash
shell-queue-submit /path/to/script.sh -p
shell-queue-watch -f
```
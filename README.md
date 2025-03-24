# Shell Queue Manager

A Python service for queueing and executing shell scripts via a REST API.

## Features

- REST API for submitting shell scripts to a queue
- Sequential execution of scripts (no concurrent execution)
- Priority queue support for urgent scripts
- Comprehensive status tracking and querying
- Real-time output monitoring of running scripts
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
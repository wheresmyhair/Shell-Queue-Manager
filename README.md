# Shell Queue Manager

A Python service for queueing and executing shell scripts via a REST API.

## Features

- REST API for submitting shell scripts to a queue
- Sequential execution of scripts (no concurrent execution)
- Priority queue support for urgent scripts
- Comprehensive status tracking and querying
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

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### API Usage

Submit a script:
```bash
curl -X POST http://localhost:5000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"script_path": "/path/to/your/script.sh"}'
```

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

## Email Notifications

Shell Queue Manager supports sending notifications via email to alert you in the following situations:

1. When only a certain number of tasks remain in the queue (default is 1)
2. When a task execution fails

### Configuring Email Notifications

Email notifications can be configured through the following methods:

#### Environment Variables

```bash
export SHELL_QUEUE_EMAIL_ENABLED=true
export SHELL_QUEUE_EMAIL_HOST=smtp.example.com
export SHELL_QUEUE_EMAIL_PORT=587
export SHELL_QUEUE_EMAIL_USERNAME=your_username
export SHELL_QUEUE_EMAIL_PASSWORD=your_password
export SHELL_QUEUE_EMAIL_SENDER=shell-queue@example.com
export SHELL_QUEUE_EMAIL_RECIPIENTS=admin@example.com,alerts@example.com
export SHELL_QUEUE_EMAIL_USE_TLS=true

export SHELL_QUEUE_NOTIFY_QUEUE_LOW_THRESHOLD=1
export SHELL_QUEUE_NOTIFY_ON_TASK_FAILURE=true
```

#### Configuration File

Modify the default configuration in config.py:

```python
DEFAULT_CONFIG = {
    "EMAIL_ENABLED": True,
    "EMAIL_HOST": "smtp.example.com",
    "EMAIL_PORT": 587,
    "EMAIL_USERNAME": "your_username",
    "EMAIL_PASSWORD": "your_password",
    "EMAIL_SENDER": "shell-queue@example.com",
    "EMAIL_RECIPIENTS": ["admin@example.com"],
    "EMAIL_USE_TLS": True,
    
    "NOTIFY_QUEUE_LOW_THRESHOLD": 1,
    "NOTIFY_ON_TASK_FAILURE": True,
}
```

## Private Configuration Management

Shell Queue Manager supports using private configuration files to store sensitive information (such as email passwords) that won't be committed to version control systems.

### Configuration File Location

The system will look for private configuration files in the following priority order:

1. `shell_queue_manager/private_config.json` (in-package configuration)
2. `repo_dir/private_config.json` (project configuration)

### Creating Private Configuration

You can use the configuration management tool to create configuration files:

```bash
python -m shell_queue_manager.cli.config_manager create

# Specify save path
python -m shell_queue_manager.cli.config_manager create --path /path/to/private_config.json

# Use default template (non-interactive)
python -m shell_queue_manager.cli.config_manager create --non-interactive
```

### View Current Configuration

```bash
python -m shell_queue_manager.cli.config_manager show
```

### Private Configuration Example

```json
{
    "EMAIL_ENABLED": true,
    "EMAIL_HOST": "smtp.example.com",
    "EMAIL_PORT": 587,
    "EMAIL_USERNAME": "your_username",
    "EMAIL_PASSWORD": "your_password",
    "EMAIL_SENDER": "shell-queue@example.com",
    "EMAIL_RECIPIENTS": [
        "admin@example.com",
        "alerts@example.com"
    ],
    "EMAIL_USE_TLS": true,
    "NOTIFY_QUEUE_LOW_THRESHOLD": 1,
    "NOTIFY_ON_TASK_FAILURE": true
}
```

### Configuration Loading Priority

The system loads configurations in the following priority order:

1. Environment variables (highest priority)
2. Private configuration file
3. Default configuration (lowest priority)

The project's `.gitignore` file is already configured to ignore private configuration files (private_config.json). Please ensure you don't commit configuration files containing sensitive information to the version control system.

## License
Apache 2.0
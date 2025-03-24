import argparse
import logging
import sys

from shell_queue_manager.api.app import create_app
from shell_queue_manager.config import load_config
from shell_queue_manager.cli.config_manager import create_config, show_config
from shell_queue_manager.cli.commands import (
    command_submit, command_status, command_list, 
    command_clear, command_watch, command_abort
)
from shell_queue_manager.utils.logger import setup_logger

logger = logging.getLogger("shell_queue_manager")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Shell Queue Manager")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Run API server")
    server_parser.add_argument(
        "--host", 
        default=None, 
        help="Server binding address (default uses configuration file)"
    )
    
    server_parser.add_argument(
        "--port", 
        type=int, 
        default=None, 
        help="Server binding port (default uses configuration file)"
    )
    
    server_parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    
    server_parser.add_argument(
        "--log-file", 
        help="Log file path"
    )
    
    server_parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level"
    )
    
    # Configuration command
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_command", help="Configuration commands")
    
    # Create configuration command
    create_config_parser = config_subparsers.add_parser("create", help="Create new configuration file")
    create_config_parser.add_argument("--path", help="Configuration file save path")
    create_config_parser.add_argument("--non-interactive", action="store_true", 
                                     help="Non-interactive mode (use default values)")
    
    # Show configuration command
    config_subparsers.add_parser("show", help="Show current configuration")
    
    # Client commands
    
    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit a script to the queue")
    submit_parser.add_argument("script_path", help="Path to the shell script to execute")
    submit_parser.add_argument("--priority", "-p", action="store_true", help="Prioritize this task")
    submit_parser.add_argument("--task-id", help="Custom task ID (generated if not provided)")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Get status of the queue or a specific task")
    status_parser.add_argument("--task-id", "-t", help="Task ID to get status for")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List recent tasks")
    list_parser.add_argument("--limit", "-n", type=int, default=10, help="Maximum number of tasks to show")
    
    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear all pending tasks from the queue")
    clear_parser.add_argument("--force", "-f", action="store_true", help="Don't ask for confirmation")
    
    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch live output of the current task")
    watch_parser.add_argument("--interval", "-i", type=float, default=1.0, help="Refresh interval in seconds")
    watch_parser.add_argument("--follow", "-f", action="store_true", help="Keep watching until interrupted")
    watch_parser.add_argument("--append", "-a", action="store_true", help="Append new output instead of refreshing")
    
    # Abort command
    abort_parser = subparsers.add_parser("abort", help="Abort a task")
    abort_group = abort_parser.add_mutually_exclusive_group(required=True)
    abort_group.add_argument("--task-id", "-t", help="Task ID to abort")
    abort_group.add_argument("--script", "-s", dest="script_path", help="Abort all tasks for this script path")
    
    return parser.parse_args()

def run_server(args):
    """Run API server"""
    config = load_config()
    # Command line arguments override configuration
    
    if args.host:
        config["HOST"] = args.host
    if args.port:
        config["PORT"] = args.port
    if args.debug:
        config["DEBUG"] = args.debug
    if args.log_file:
        config["LOG_FILE"] = args.log_file
    if args.log_level:
        config["LOG_LEVEL"] = args.log_level
    
    # Set up logging
    log_level = getattr(logging, config["LOG_LEVEL"])
    setup_logger(
        "shell_queue_manager", 
        log_level=log_level,
        log_file=config["LOG_FILE"]
    )
    
    logger.info(f"Starting Shell Queue Manager server at {config['HOST']}:{config['PORT']}")
    
    # Create and run application
    app = create_app(config)
    
    # Run application
    app.run(
        host=config["HOST"],
        port=config["PORT"],
        debug=config["DEBUG"]
    )

def main():
    """Main entry point"""
    args = parse_args()
    
    # Execute corresponding operation based on command
    if args.command == "server":
        run_server(args)
    elif args.command == "config":
        if args.config_command == "create":
            create_config(args.path, not args.non_interactive)
        elif args.config_command == "show":
            show_config()
        else:
            print("Please specify a configuration command: create or show")
    elif args.command == "submit":
        command_submit(args)
    elif args.command == "status":
        command_status(args)
    elif args.command == "list":
        command_list(args)
    elif args.command == "clear":
        command_clear(args)
    elif args.command == "watch":
        command_watch(args)
    elif args.command == "abort":
        command_abort(args)
    else:
        # Run server by default if no command is specified
        if len(sys.argv) == 1:
            run_server(parse_args([]))
        else:
            print("Unknown command. Use -h to see help.")
            sys.exit(1)

if __name__ == "__main__":
    main()
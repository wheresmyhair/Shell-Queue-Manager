import argparse
import logging
import sys

from shell_queue_manager.api.app import create_app
from shell_queue_manager.config import load_config
from shell_queue_manager.cli.config_manager import create_config, show_config
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
    else:
        # Run server by default
        if len(sys.argv) == 1:
            run_server(parse_args())
        else:
            print("Unknown command. Use -h to see help.")
            sys.exit(1)

if __name__ == "__main__":
    main()
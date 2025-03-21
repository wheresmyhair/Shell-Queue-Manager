import argparse
import getpass
import json
import os

from shell_queue_manager.config import PRIVATE_CONFIG_FILES, DEFAULT_CONFIG


def create_config(path=None, interactive=True):
    if not path:
        path = PRIVATE_CONFIG_FILES[0]
    
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    if os.path.exists(path):
        if interactive:
            overwrite = input(f"Configuration file {path} already exists. Overwrite? (y/n): ")
            if overwrite.lower() != 'y':
                print("Cancelled")
                return False
        else:
            print(f"Configuration file {path} already exists, not overwritten")
            return False
    
    config = {}
    
    if interactive:
        print("Create a new Shell Queue Manager configuration file")
        print("------------------------------------")
        print("Please enter email notification settings (press Enter to skip or use default values):")
        
        # Enable email notifications
        enable_email = input("Enable email notifications? (y/n) [n]: ")
        config["EMAIL_ENABLED"] = enable_email.lower() == 'y'
        
        if config["EMAIL_ENABLED"]:
            # SMTP server settings
            config["EMAIL_HOST"] = input(f"SMTP server [{DEFAULT_CONFIG['EMAIL_HOST']}]: ") or DEFAULT_CONFIG["EMAIL_HOST"]
            config["EMAIL_PORT"] = int(input(f"SMTP port [{DEFAULT_CONFIG['EMAIL_PORT']}]: ") or DEFAULT_CONFIG["EMAIL_PORT"])
            config["EMAIL_USE_TLS"] = input("Use TLS encryption? (y/n) [y]: ").lower() != 'n'
            
            # User credentials
            config["EMAIL_USERNAME"] = input("SMTP username: ")
            config["EMAIL_PASSWORD"] = getpass.getpass("SMTP password: ")
            
            # Sender and recipients
            config["EMAIL_SENDER"] = input("Sender address: ")
            recipients_str = input("Recipient addresses (separate multiple recipients with commas): ")
            config["EMAIL_RECIPIENTS"] = [r.strip() for r in recipients_str.split(",") if r.strip()]
            
            # Notification conditions
            config["NOTIFY_QUEUE_LOW_THRESHOLD"] = int(input("Queue low threshold (number of tasks) [1]: ") or "1")
            config["NOTIFY_ON_TASK_FAILURE"] = input("Notify on task failure? (y/n) [y]: ").lower() != 'n'
    else:
        # Non-interactive mode uses default template
        config = {
            "EMAIL_ENABLED": False,
            "EMAIL_HOST": DEFAULT_CONFIG["EMAIL_HOST"],
            "EMAIL_PORT": DEFAULT_CONFIG["EMAIL_PORT"],
            "EMAIL_USERNAME": "",
            "EMAIL_PASSWORD": "",
            "EMAIL_SENDER": "",
            "EMAIL_RECIPIENTS": [],
            "EMAIL_USE_TLS": True,
            "NOTIFY_QUEUE_LOW_THRESHOLD": 1,
            "NOTIFY_ON_TASK_FAILURE": True
        }
    
    # Save configuration
    with open(path, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"Configuration saved to: {path}")
    return True

def show_config():
    """Display current configuration and configuration file locations"""
    print("Shell Queue Manager Configuration")
    print("------------------------")
    
    # Check configuration files
    found_configs = []
    for path in PRIVATE_CONFIG_FILES:
        if os.path.exists(path):
            found_configs.append(path)
    
    if found_configs:
        print("\nFound configuration files:")
        for path in found_configs:
            print(f"- {path}")
        
        # Show contents of the first configuration file
        try:
            with open(found_configs[0], 'r') as f:
                config = json.load(f)
                
                print("\nConfiguration contents:")
                for key, value in config.items():
                    # Hide password
                    if key == "EMAIL_PASSWORD" and value:
                        value = "******"
                    print(f"{key}: {value}")
        except Exception as e:
            print(f"Error reading configuration file: {e}")
    else:
        print("\nNo configuration files found. Configuration file search paths:")
        for path in PRIVATE_CONFIG_FILES:
            print(f"- {path}")
        
        print("\nUsing default configuration.")

def main():
    """Configuration management command line entry point"""
    parser = argparse.ArgumentParser(description="Shell Queue Manager Configuration Management Tool")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create configuration command
    create_parser = subparsers.add_parser("create", help="Create a new configuration file")
    create_parser.add_argument("--path", help="Path to save the configuration file")
    create_parser.add_argument("--non-interactive", action="store_true", 
                              help="Non-interactive mode (use default values)")
    
    # Show configuration command
    show_parser = subparsers.add_parser("show", help="Show current configuration")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_config(args.path, not args.non_interactive)
    elif args.command == "show":
        show_config()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
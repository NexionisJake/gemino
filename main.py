import os
import argparse
from agents.manager import ManagerAgent
from rich.console import Console
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file in parent directory
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)

    console = Console()
    parser = argparse.ArgumentParser(description="PurpleVibe Autonomous Security Auditor")
    parser.add_argument("--target", default="target_code", help="Directory using relative path to audit")
    parser.add_argument("--watch", action="store_true", help="Run in Shadow Daemon mode (Real-Time Watchdog)")
    args = parser.parse_args()

    # Resolve absolute path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(base_dir, args.target)

    if not os.path.exists(target_path):
        console.print(f"[bold red]Target directory {target_path} does not exist.[/bold red]")
        return

    # Check API Key
    if not os.environ.get("GOOGLE_API_KEY"):
        console.print("[bold red]GOOGLE_API_KEY environment variable not set.[/bold red]")
        console.print("Please set it: export GOOGLE_API_KEY='your_key'")
        return

    if args.watch:
        from daemon import run_daemon
        run_daemon(target_path)
    else:
        agent = ManagerAgent(target_path)
        agent.run()

if __name__ == "__main__":
    main()

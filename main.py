import os
import argparse
from agents.manager import ManagerAgent
from rich.console import Console

def main():
    console = Console()
    parser = argparse.ArgumentParser(description="PurpleVibe Autonomous Security Auditor")
    parser.add_argument("--target", default="target_code", help="Directory using relative path to audit")
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

    agent = ManagerAgent(target_path)
    agent.run()

if __name__ == "__main__":
    main()

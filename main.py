import os
import sys
import warnings

# Suppress annoying pygame/pkg_resources warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

import argparse
# Load dotenv BEFORE other imports to ensure env vars are set
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)
import asyncio

from rich.console import Console
import traceback

def main():
    try:
        from agents.manager import ManagerAgent
        
        console = Console()
        parser = argparse.ArgumentParser(description="Argus — The Hundred-Eyed AI Security Auditor | Team Phalanx")
        parser.add_argument("--target", default="target_code", help="Directory using relative path to audit")
        parser.add_argument("--watch", action="store_true", help="Run in Shadow Daemon mode (Real-Time Watchdog)")
        parser.add_argument("--mode", default="standard", help="Set the AI Persona (standard, pirate, corporate)")
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
            agent = ManagerAgent(target_path, persona=args.mode)
            asyncio.run(agent.run())
            
    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")
    except Exception as e:
        console = Console()
        console.print(f"\n[bold red]FATAL ERROR: {e}[/bold red]")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

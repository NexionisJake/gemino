import os
import time
import sys
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from rich.console import Console
from agents.scanner import ScannerAgent

# Attempt to import VibeEngine
try:
    from vibe_engine import VibeEngine
except ImportError:
    # Handle import if running as a module or script
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from vibe_engine import VibeEngine

console = Console()

class ShadowGuardian(FileSystemEventHandler):
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.vibe = VibeEngine()
        self.scanner = ScannerAgent()
        self.last_scan_time = 0
        self.scan_cooldown = 2  # Seconds to avoid double triggering

    def on_modified(self, event):
        if event.is_directory:
            return
        
        filename = event.src_path
        if filename.endswith(".py") and "exploit_" not in filename and "test_" not in filename and "vibe_engine" not in filename:
            # Simple debounce
            current_time = time.time()
            if current_time - self.last_scan_time < self.scan_cooldown:
                return
            self.last_scan_time = current_time

            console.print(f"\n[bold yellow]⚡ Detected change in {filename}. Waking up Agent...[/bold yellow]")
            self.vibe.speak("File change detected. Analyzing.")
            
            # Trigger scan
            try:
                result = self.scanner.scan_file(filename)
                if result and result.get("vulnerabilities"):
                    count = len(result["vulnerabilities"])
                    console.print(f"[bold red]⚠ Found {count} potential vulnerabilities![/bold red]")
                    self.vibe.alert("danger")
                    self.vibe.speak(f"Warning. {count} vulnerabilities detected in modified file.")
                else:
                    console.print("[bold green]✓ File appears clean.[/bold green]")
                    self.vibe.speak("File clean.")
            except Exception as e:
                console.print(f"[bold red]Error during scan: {e}[/bold red]")

def run_daemon(target_dir):
    event_handler = ShadowGuardian(target_dir)
    observer = Observer()
    observer.schedule(event_handler, target_dir, recursive=True)
    observer.start()
    
    console.print(f"[bold magenta]👁 Shadow Daemon Watching: {target_dir}[/bold magenta]")
    console.print("[dim]Press Ctrl+C to stop...[/dim]")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[bold red]Stopping Shadow Daemon...[/bold red]")
    
    observer.join()

import os
import time
import json
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from .scanner import ScannerAgent
from .patcher import PatcherAgent
from .verifier import VerifierAgent
from .improver import ImproverAgent
import sys

# Attempt to import VibeEngine, handle path if needed
try:
    from vibe_engine import VibeEngine
except ImportError:
    # If running from inside agents/, we might need to look up
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from vibe_engine import VibeEngine

from report_generator import generate_html_report

console = Console()

ASCII_BANNER = """
[bold magenta]
    ██████╗ ██╗   ██╗██████╗ ██████╗ ██╗     ███████╗██╗   ██╗██╗██████╗ ███████╗
    ██╔══██╗██║   ██║██╔══██╗██╔══██╗██║     ██╔════╝██║   ██║██║██╔══██╗██╔════╝
    ██████╔╝██║   ██║██████╔╝██████╔╝██║     █████╗  ██║   ██║██║██████╔╝█████╗  
    ██╔═══╝ ██║   ██║██╔══██╗██╔═══╝ ██║     ██╔══╝  ╚██╗ ██╔╝██║██╔══██╗██╔══╝  
    ██║     ╚██████╔╝██║  ██║██║     ███████╗███████╗ ╚████╔╝ ██║██████╔╝███████╗
    ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚══════╝╚══════╝  ╚═══╝  ╚═╝╚═════╝ ╚══════╝
[/bold magenta]
[cyan]                    ⚡ Autonomous Security Auditor ⚡[/cyan]
[dim]                       Powered by Gemini 2.5 Flash[/dim]
"""

MAX_PATCH_RETRIES = 2

class ManagerAgent:
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Trace file for agent memory
        self.trace_file = os.path.join(self.reports_dir, 'agent_trace.json')
        if os.path.exists(self.trace_file):
            os.remove(self.trace_file)
        
        self.scanner = ScannerAgent(trace_file=self.trace_file)
        self.patcher = PatcherAgent(trace_file=self.trace_file)
        self.improver = ImproverAgent(trace_file=self.trace_file)
        self.verifier = VerifierAgent()
        self.vibe = VibeEngine()
        
        # Dashboard State
        self.vuln_states = []
        self.current_thought = "Initializing PurpleVibe Systems..."

    def generate_dashboard(self):
        # Premium Layout
        layout = Layout()
        layout.split(
            Layout(name="header", size=4),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Header
        grid_header = Table.grid(expand=True)
        grid_header.add_column(justify="center", ratio=1)
        grid_header.add_row("[bold white]🟣 PURPLE VIBE[/bold white] [dim]||[/dim] [cyan]AUTONOMOUS SECURITY AUDITOR[/cyan]")
        grid_header.add_row("[dim]Powered by Gemini 1.5 Flash • Neural Voice Enabled[/dim]")
        
        layout["header"].update(Panel(grid_header, style="slate_blue1", border_style="bright_magenta"))
        
        # Body - Vuln Feed
        table = Table(expand=True, border_style="slate_blue1", header_style="bold cyan")
        table.add_column("TARGET FILE", style="bright_white")
        table.add_column("THREAT TYPE", style="red")
        table.add_column("STATUS", style="white")
        
        for item in self.vuln_states:
            status_style = item.get("color", "white")
            status_text = item["status"].upper()
            if status_text == "FIXED": status_text = "✓ SECURE"
            if status_text == "FAILED": status_text = "✗ FAILED"
            
            table.add_row(
                item["file"], 
                item["vuln_type"].upper(), 
                Text(status_text, style=status_style)
            )
            
        layout["body"].update(Panel(table, title="[bold white]LIVE THREAT INTELLIGENCE[/bold white]", border_style="cyan"))
        
        # Footer - Brain
        thought_text = Text(f"▶ {self.current_thought}", style="italic bright_green")
        layout["footer"].update(Panel(thought_text, title="SYSTEM LOGIC", border_style="green"))
        
        return layout

    def log_thought(self, message, speak=False):
        self.current_thought = message
        if speak:
            self.vibe.speak(message)

    def update_vuln_status(self, file, vuln_type, status, color="white"):
        found = False
        for item in self.vuln_states:
            if item["file"] == file and item["vuln_type"] == vuln_type:
                item["status"] = status
                item["color"] = color
                found = True
                break
        if not found:
            self.vuln_states.append({"file": file, "vuln_type": vuln_type, "status": status, "color": color})

    def run(self):
        # Show ASCII banner
        console.print(ASCII_BANNER)
        self.vibe.speak("System Online.")
        time.sleep(1)
        
        report_data = {
            "vulnerabilities_found": [],
            "patches_attempted": [],
            "verification_results": []
        }

        # Collect files
        files_to_scan = []
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_") and not file.startswith("exploit_"):
                    files_to_scan.append(os.path.join(root, file))
        
        # Phase 1: Scan
        console.print("\n[bold cyan]Phase 1: Scanning for vulnerabilities...[/bold cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            scan_task = progress.add_task("Scanning files...", total=len(files_to_scan))
            
            for full_path in files_to_scan:
                file_name = os.path.basename(full_path)
                progress.update(scan_task, description=f"Scanning {file_name}...")
                
                scan_result = self.scanner.scan_file(full_path)
                
                if scan_result and "vulnerabilities" in scan_result:
                    vulns = scan_result["vulnerabilities"]
                    if vulns:
                        # Report found
                        self.vibe.alert("danger")
                        self.vibe.speak(f"Critical: {len(vulns)} threats found.")
                        
                        for vuln in vulns:
                            vuln_type = self._extract_vuln_type(vuln)
                            self.update_vuln_status(file_name, vuln_type, "Detected", "red")
                            report_data["vulnerabilities_found"].append(vuln)
                
                progress.advance(scan_task)
        
        if not report_data["vulnerabilities_found"]:
            console.print("\n[bold green]✓ No vulnerabilities found! All clear.[/bold green]\n")
            self.vibe.speak("Scan, complete. System Secure.")
            self._save_reports(report_data)
            self.vibe.shutdown()
            return
        
        console.print(f"\n[bold red]Found {len(report_data['vulnerabilities_found'])} vulnerability(ies). Starting remediation...[/bold red]\n")
        time.sleep(1)
        
        # Phase 2: Remediation Dashboard
        with Live(self.generate_dashboard(), refresh_per_second=4) as live:
            self.log_thought("Entering remediation phase...", speak=True)
            live.update(self.generate_dashboard())
            
            # Group vulns
            vulns_by_file = {}
            for vuln in report_data["vulnerabilities_found"]:
                file_name = vuln.get("file", "unknown")
                if file_name not in vulns_by_file:
                    vulns_by_file[file_name] = []
                vulns_by_file[file_name].append(vuln)
            
            for file_name, vulns in vulns_by_file.items():
                full_path = None
                for root, _, files in os.walk(self.target_dir):
                    if file_name in files:
                        full_path = os.path.join(root, file_name)
                        break
                
                if not full_path: continue
                
                for vuln in vulns:
                    vuln_type = self._extract_vuln_type(vuln)
                    self.handle_vulnerability(vuln, full_path, report_data, live, file_name, vuln_type)
                    time.sleep(2)
            
            self.log_thought("Audit Complete. Generating reports...", speak=True)
            live.update(self.generate_dashboard())
            time.sleep(2)
        
        self._save_reports(report_data)
        self.vibe.speak("Audit complete. Shutting down.")
        self.vibe.shutdown()

    def _extract_vuln_type(self, vuln):
        vuln_type = vuln.get("type", vuln.get("vulnerability", "Unknown"))
        for known in ["SQL Injection", "Command Injection", "Path Traversal", "SSRF", "Hardcoded"]:
            if known.lower() in vuln_type.lower() or known.lower() in vuln.get("description", "").lower():
                return known
        return vuln_type[:25] if len(vuln_type) > 25 else vuln_type

    def _save_reports(self, report_data):
        json_path = os.path.join(self.reports_dir, 'final_report.json')
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        html_path = os.path.join(self.reports_dir, 'summary.html')
        generate_html_report(report_data, html_path)
        
        console.print(f"\n[bold green]✓ Reports saved:[/bold green]")
        console.print(f"  📄 JSON: {json_path}")
        console.print(f"  🌐 HTML: {html_path}")
        console.print(f"  🧠 Agent Trace: {self.trace_file}\n")

    def handle_vulnerability(self, vuln, file_path, report_data, live, file_name, vuln_type):
        self.log_thought(f"Analyzing {vuln_type} in {file_name}...", speak=True)
        self.update_vuln_status(file_name, vuln_type, "Analyzing", "yellow")
        live.update(self.generate_dashboard())
        
        # [NEW] Generate Attack Graph
        self.log_thought("Visualizing attack vector...", speak=False)
        graph_code = self.patcher.generate_attack_graph(vuln, file_name)
        if graph_code:
            vuln["attack_graph"] = graph_code
        
        with open(file_path, 'r') as f:
            original_content = f.read()

        # Step 1: Generate Exploit Demo (Phase 4 Feature)
        self.log_thought("Generating Proof-of-Concept Exploit...", speak=False)
        self.update_vuln_status(file_name, vuln_type, "Generating Exploit", "red")
        live.update(self.generate_dashboard())
        
        exploit_data = self.patcher.create_exploit(vuln, original_content, file_name)
        if exploit_data:
            exploit_code = exploit_data.get("exploit_code")
            if exploit_code:
                exploit_path = os.path.join(os.path.dirname(file_path), f"exploit_{file_name}")
                with open(exploit_path, 'w') as f:
                    f.write(exploit_code)
                self.log_thought(f"Exploit script saved to exploit_{file_name}", speak=True)
        
        # Step 2: Patching Loop
        error_feedback = None
        for attempt in range(MAX_PATCH_RETRIES + 1):
            if attempt > 0:
                self.log_thought(f"Retry attempt {attempt}/{MAX_PATCH_RETRIES}...", speak=True)
                self.update_vuln_status(file_name, vuln_type, f"Retry {attempt}", "magenta")
                live.update(self.generate_dashboard())
            
            patch_result = self.patcher.create_patch(vuln, original_content, file_name, error_feedback)
            
            if not patch_result:
                self.update_vuln_status(file_name, vuln_type, "Patch Gen Failed", "red")
                return

            repro_code = patch_result.get("reproduction_test_code")
            fixed_code = patch_result.get("fixed_code")

            if not repro_code or not fixed_code:
                self.update_vuln_status(file_name, vuln_type, "Invalid Patch", "red")
                return

            test_filename = f"test_{file_name}"
            test_path = os.path.join(os.path.dirname(file_path), test_filename)
            with open(test_path, 'w') as f:
                f.write(repro_code)

            # Verify reproduction
            self.log_thought(f"Verifying vulnerability reproduction...", speak=False)
            self.update_vuln_status(file_name, vuln_type, "Verifying Exploit", "yellow")
            live.update(self.generate_dashboard())
            
            passed_initial, initial_output = self.verifier.run_test(test_path)
            
            # Apply fix
            self.log_thought("Applying secure patch logic...", speak=False)
            self.update_vuln_status(file_name, vuln_type, "Patching", "magenta")
            live.update(self.generate_dashboard())
            
            backup_path = file_path + ".bak"
            with open(backup_path, 'w') as f:
                f.write(original_content)
                
            with open(file_path, 'w') as f:
                f.write(fixed_code)

            # Verify fix
            self.log_thought("Verifying security patch...", speak=True)
            self.update_vuln_status(file_name, vuln_type, "Verifying Patch", "cyan")
            live.update(self.generate_dashboard())
            
            passed_fix, fix_output = self.verifier.run_test(test_path)
            
            if passed_fix:
                self.vibe.alert("success")
                self.log_thought("Patch verified. Threat neutralized.", speak=True)
                self.update_vuln_status(file_name, vuln_type, "✓ Fixed", "green")
                report_data["verification_results"].append({"file": file_path, "status": "Fixed"})
                live.update(self.generate_dashboard())
                return
            else:
                with open(file_path, 'w') as f:
                    f.write(original_content)
                
                if attempt < MAX_PATCH_RETRIES:
                    error_feedback = fix_output
                    self.log_thought(f"Patch verification failed. Retrying...", speak=True)
                else:
                     # [NEW] META-PROGRAMMING TRIGGER
                    self.vibe.alert("danger")
                    self.log_thought("Max retries reached. Initiating Self-Evolution Protocol...", speak=True)
                    self.update_vuln_status(file_name, vuln_type, "Evolving...", "magenta")
                    live.update(self.generate_dashboard())
                    
                    # 1. Improve the Skill
                    skill_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'skills', 'repair_code.md')
                    success = self.improver.improve_skill(fix_output, skill_path)
                    
                    if success:
                         self.log_thought("Neural pathways updated. Instructions rewritten.", speak=True)
                         # Optional: You could try ONE more time with the new brain, 
                         # but for the demo, just showing the update is enough.
                         self.update_vuln_status(file_name, vuln_type, "Skill Upgraded", "bright_magenta")
                    else:
                         self.log_thought("Evolution failed. System halt.", speak=True)
                         self.update_vuln_status(file_name, vuln_type, "✗ Failed", "red")
                    
                    report_data["verification_results"].append({"file": file_path, "status": "Failed"})
        
        live.update(self.generate_dashboard())

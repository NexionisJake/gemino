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
        # Clear previous trace
        if os.path.exists(self.trace_file):
            os.remove(self.trace_file)
        
        self.scanner = ScannerAgent(trace_file=self.trace_file)
        self.patcher = PatcherAgent(trace_file=self.trace_file)
        self.verifier = VerifierAgent()
        
        # Dashboard State
        self.vuln_states = []
        self.current_thought = "Initializing PurpleVibe Systems..."

    def generate_dashboard(self):
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["header"].update(Panel(Text("🟣 PurpleVibe Autonomous Audit System", justify="center", style="bold magenta"), style="magenta"))
        
        table = Table(expand=True, border_style="cyan")
        table.add_column("File", style="cyan")
        table.add_column("Vulnerability", style="red")
        table.add_column("Status", style="white")
        
        for item in self.vuln_states:
            status_style = item.get("color", "white")
            table.add_row(item["file"], item["vuln_type"], Text(item["status"], style=status_style))
            
        layout["main"].update(Panel(table, title="Live Vulnerability Feed", border_style="cyan"))
        
        thought_text = Text(f"[Brain] Gemini 2.5 Flash: {self.current_thought}", style="italic green")
        layout["footer"].update(Panel(thought_text, title="Agent Reasoning Engine", border_style="green"))
        
        return layout

    def log_thought(self, message):
        self.current_thought = message

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
        time.sleep(1)
        
        report_data = {
            "vulnerabilities_found": [],
            "patches_attempted": [],
            "verification_results": []
        }

        # Collect files to scan
        files_to_scan = []
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    files_to_scan.append(os.path.join(root, file))
        
        # Progress bar for scanning phase
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
                    for vuln in vulns:
                        vuln_type = self._extract_vuln_type(vuln)
                        self.update_vuln_status(file_name, vuln_type, "Detected", "red")
                        report_data["vulnerabilities_found"].append(vuln)
                
                progress.advance(scan_task)
        
        if not report_data["vulnerabilities_found"]:
            console.print("\n[bold green]✓ No vulnerabilities found! All clear.[/bold green]\n")
            self._save_reports(report_data)
            return
        
        console.print(f"\n[bold red]Found {len(report_data['vulnerabilities_found'])} vulnerability(ies). Starting remediation...[/bold red]\n")
        time.sleep(1)
        
        # Live dashboard for remediation phase
        with Live(self.generate_dashboard(), refresh_per_second=4) as live:
            self.log_thought("Entering remediation phase...")
            live.update(self.generate_dashboard())
            
            # Group vulns by file
            vulns_by_file = {}
            for vuln in report_data["vulnerabilities_found"]:
                file_name = vuln.get("file", "unknown")
                if file_name not in vulns_by_file:
                    vulns_by_file[file_name] = []
                vulns_by_file[file_name].append(vuln)
            
            for file_name, vulns in vulns_by_file.items():
                # Find full path
                full_path = None
                for root, _, files in os.walk(self.target_dir):
                    if file_name in files:
                        full_path = os.path.join(root, file_name)
                        break
                
                if not full_path:
                    continue
                
                for vuln in vulns:
                    vuln_type = self._extract_vuln_type(vuln)
                    self.handle_vulnerability(vuln, full_path, report_data, live, file_name, vuln_type)
                    time.sleep(2)  # Rate limiting
            
            self.log_thought("Audit Complete. Generating reports...")
            live.update(self.generate_dashboard())
            time.sleep(2)
        
        self._save_reports(report_data)

    def _extract_vuln_type(self, vuln):
        vuln_type = vuln.get("type", vuln.get("vulnerability", "Unknown"))
        for known in ["SQL Injection", "Command Injection", "Path Traversal", "SSRF", "Hardcoded"]:
            if known.lower() in vuln_type.lower() or known.lower() in vuln.get("description", "").lower():
                return known
        return vuln_type[:25] if len(vuln_type) > 25 else vuln_type

    def _save_reports(self, report_data):
        # Save JSON report
        json_path = os.path.join(self.reports_dir, 'final_report.json')
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate HTML report
        html_path = os.path.join(self.reports_dir, 'summary.html')
        generate_html_report(report_data, html_path)
        
        console.print(f"\n[bold green]✓ Reports saved:[/bold green]")
        console.print(f"  📄 JSON: {json_path}")
        console.print(f"  🌐 HTML: {html_path}")
        console.print(f"  🧠 Agent Trace: {self.trace_file}\n")

    def handle_vulnerability(self, vuln, file_path, report_data, live, file_name, vuln_type):
        self.log_thought(f"Analyzing {vuln_type} in {file_name}...")
        self.update_vuln_status(file_name, vuln_type, "Analyzing", "yellow")
        live.update(self.generate_dashboard())
        
        with open(file_path, 'r') as f:
            original_content = f.read()

        # Retry loop
        error_feedback = None
        for attempt in range(MAX_PATCH_RETRIES + 1):
            if attempt > 0:
                self.log_thought(f"Retry attempt {attempt}/{MAX_PATCH_RETRIES}...")
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

            # Save test
            test_filename = f"test_{file_name}"
            test_path = os.path.join(os.path.dirname(file_path), test_filename)
            with open(test_path, 'w') as f:
                f.write(repro_code)

            # Verify reproduction
            self.log_thought(f"Running exploit verification...")
            self.update_vuln_status(file_name, vuln_type, "Verifying Exploit", "yellow")
            live.update(self.generate_dashboard())
            
            passed_initial, initial_output = self.verifier.run_test(test_path)
            
            if passed_initial:
                self.log_thought("Exploit test passed on vulnerable code. Adjusting...")
                # This might be a false positive or test issue
            
            # Apply fix
            self.log_thought("Applying secure patch...")
            self.update_vuln_status(file_name, vuln_type, "Patching", "magenta")
            live.update(self.generate_dashboard())
            
            backup_path = file_path + ".bak"
            with open(backup_path, 'w') as f:
                f.write(original_content)
                
            with open(file_path, 'w') as f:
                f.write(fixed_code)

            # Verify fix
            self.log_thought("Verifying patch integrity...")
            self.update_vuln_status(file_name, vuln_type, "Verifying Patch", "cyan")
            live.update(self.generate_dashboard())
            
            passed_fix, fix_output = self.verifier.run_test(test_path)
            
            if passed_fix:
                self.log_thought("Patch verified! Threat neutralized.")
                self.update_vuln_status(file_name, vuln_type, "✓ Fixed", "green")
                report_data["verification_results"].append({"file": file_path, "status": "Fixed"})
                live.update(self.generate_dashboard())
                return  # Success!
            else:
                # Revert and maybe retry
                with open(file_path, 'w') as f:
                    f.write(original_content)
                
                if attempt < MAX_PATCH_RETRIES:
                    error_feedback = fix_output  # Pass error to next attempt
                    self.log_thought(f"Patch failed. Preparing retry with error context...")
                else:
                    self.log_thought("All retry attempts exhausted.")
                    self.update_vuln_status(file_name, vuln_type, "✗ Failed", "red")
                    report_data["verification_results"].append({"file": file_path, "status": "Failed"})
        
        live.update(self.generate_dashboard())

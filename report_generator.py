import os
import json
from datetime import datetime

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Argus Security Audit Report</title>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #eee;
            min-height: 100vh;
            padding: 40px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(138, 43, 226, 0.2);
            border-radius: 15px;
            border: 1px solid rgba(138, 43, 226, 0.4);
        }}
        h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #9b59b6, #3498db);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .timestamp {{ color: #888; font-size: 0.9rem; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-number {{ font-size: 3rem; font-weight: bold; }}
        .stat-label {{ color: #888; margin-top: 5px; }}
        .critical {{ color: #e74c3c; }}
        .fixed {{ color: #2ecc71; }}
        .failed {{ color: #f39c12; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{
            font-size: 1.5rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(138, 43, 226, 0.5);
        }}
        .vuln-card {{
            background: rgba(231, 76, 60, 0.1);
            border: 1px solid rgba(231, 76, 60, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
        }}
        .vuln-card.fixed {{
            background: rgba(46, 204, 113, 0.1);
            border-color: rgba(46, 204, 113, 0.3);
        }}
        .vuln-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .vuln-type {{ font-weight: bold; font-size: 1.1rem; }}
        .vuln-severity {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        .severity-critical {{ background: #e74c3c; }}
        .severity-high {{ background: #e67e22; }}
        .severity-medium {{ background: #f1c40f; color: #333; }}
        .severity-low {{ background: #3498db; }}
        .vuln-file {{ color: #9b59b6; margin: 10px 0; }}
        .vuln-desc {{ color: #aaa; line-height: 1.6; margin-bottom: 15px; }}
        
        /* Graph Styling */
        .graph-container {{
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            display: flex;
            justify-content: center;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-top: 10px;
        }}
        .status-fixed {{ background: #2ecc71; color: #fff; }}
        .status-failed {{ background: #e74c3c; color: #fff; }}
        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            border-top: 1px solid rgba(255,255,255,0.1);
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>👁️ Argus Security Audit Report</h1>
            <p class="timestamp">Generated: {timestamp}</p>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_vulns}</div>
                <div class="stat-label">Vulnerabilities Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-number fixed">{fixed_count}</div>
                <div class="stat-label">Successfully Fixed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number failed">{failed_count}</div>
                <div class="stat-label">Failed to Fix</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Vulnerability Details</h2>
            {vuln_cards}
        </div>
        
        <footer>
            <p>Powered by Argus — The Hundred-Eyed AI Guardian | Team Phalanx</p>
            <p>Using Gemini 2.5 Flash AI</p>
        </footer>
    </div>
</body>
</html>
'''

def generate_html_report(report_data, output_path):
    """Generate HTML report from JSON report data."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    vulns = report_data.get("vulnerabilities_found", [])
    results = report_data.get("verification_results", [])
    
    total_vulns = len(vulns)
    fixed_count = sum(1 for r in results if r.get("status") == "Fixed")
    failed_count = sum(1 for r in results if r.get("status") == "Failed")
    
    # Build vulnerability cards
    vuln_cards = ""
    for v in vulns:
        severity = v.get("severity", "Medium").lower()
        vuln_type = v.get("type", v.get("vulnerability", "Unknown"))
        file_name = v.get("file", "unknown")
        line = v.get("line", "?")
        desc = v.get("description", "No description provided.")
        graph_code = v.get("attack_graph", "")
        
        # Check if fixed
        is_fixed = any(r.get("status") == "Fixed" for r in results if file_name in r.get("file", ""))
        card_class = "vuln-card fixed" if is_fixed else "vuln-card"
        status_html = '<span class="status-badge status-fixed">✓ FIXED</span>' if is_fixed else '<span class="status-badge status-failed">✗ OPEN</span>'
        
        # Render Graph if available
        graph_html = ""
        if graph_code:
            graph_html = f'<div class="graph-container"><div class="mermaid">{graph_code}</div></div>'

        vuln_cards += f'''
        <div class="{card_class}">
            <div class="vuln-header">
                <span class="vuln-type">{vuln_type}</span>
                <span class="vuln-severity severity-{severity}">{severity.upper()}</span>
            </div>
            <p class="vuln-file">📁 {file_name} : Line {line}</p>
            <p class="vuln-desc">{desc}</p>
            {graph_html}
            {status_html}
        </div>
        '''
    
    if not vuln_cards:
        vuln_cards = '<div class="vuln-card fixed"><p>No vulnerabilities detected! 🎉</p></div>'
    
    html = HTML_TEMPLATE.format(
        timestamp=timestamp,
        total_vulns=total_vulns,
        fixed_count=fixed_count,
        failed_count=failed_count,
        vuln_cards=vuln_cards
    )
    
    with open(output_path, "w") as f:
        f.write(html)
    
    return output_path

if __name__ == "__main__":
    # Test data including a mermaid graph
    sample = {
        "vulnerabilities_found": [
            {
                "file": "login.py", "line": 5, "type": "SQL Injection", "severity": "Critical", 
                "description": "User input concatenated into SQL.",
                "attack_graph": "graph LR; User-->Login; Login-->Database; Database-->Hacked;"
            }
        ],
        "verification_results": [{"file": "login.py", "status": "Fixed"}]
    }
    generate_html_report(sample, "reports/summary.html")
    print("Report generated!")

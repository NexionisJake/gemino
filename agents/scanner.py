import os
import json
from google import genai
from google.genai.types import GenerateContentConfig
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from google.genai.errors import ClientError

class ScannerAgent:
    def __init__(self, model_name="gemini-1.5-flash", trace_file=None):
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model_name = model_name
        self.trace_file = trace_file
        
    def _log_trace(self, action, prompt_summary, response):
        """Log agent thinking to trace file."""
        if not self.trace_file:
            return
        try:
            if os.path.exists(self.trace_file):
                with open(self.trace_file, 'r') as f:
                    traces = json.load(f)
            else:
                traces = []
            
            traces.append({
                "agent": "ScannerAgent",
                "model": self.model_name,
                "action": action,
                "prompt_summary": prompt_summary[:200] + "...",
                "response_preview": str(response)[:500] + "..."
            })
            
            with open(self.trace_file, 'w') as f:
                json.dump(traces, f, indent=2)
        except Exception:
            pass

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(10),
        retry=retry_if_exception_type(ClientError)  # Only retry on API errors
    )
    def _generate_with_retry(self, prompt):
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=GenerateContentConfig(response_mime_type="application/json")
        )
        return response.text, json.loads(response.text)

    def scan_file(self, file_path):
        with open(file_path, 'r') as f:
            code_content = f.read()
            
        skill_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'skills', 'audit_code.md')
        with open(skill_path, 'r') as f:
            skill_instructions = f.read()
            
        prompt = f"{skill_instructions}\n\nFile Name: {os.path.basename(file_path)}\n\nCode to Analyze:\n```python\n{code_content}\n```"
        
        try:
            raw_response, parsed = self._generate_with_retry(prompt)
            
            # Enforce correct filename in results
            if parsed and "vulnerabilities" in parsed:
                for vuln in parsed["vulnerabilities"]:
                    vuln["file"] = os.path.basename(file_path)
            
            self._log_trace("scan_file", f"Scanning {os.path.basename(file_path)}", parsed)
            return parsed
        except Exception as e:
            print(f"[!] Error scanning {os.path.basename(file_path)}: {e}")
            return {"vulnerabilities": []}

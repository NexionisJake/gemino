import os
import json
from google import genai
from google.genai.types import GenerateContentConfig
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from google.genai.errors import ClientError

class PatcherAgent:
    def __init__(self, model_name="gemini-flash-latest", trace_file=None):
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
                "agent": "PatcherAgent",
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
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(ClientError)
    )
    def _generate_with_retry(self, prompt):
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=GenerateContentConfig(response_mime_type="application/json")
        )
        return response.text, json.loads(response.text)

    def create_exploit(self, vulnerability, file_content, filename):
        """Generates a standalone exploit script."""
        skill_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'skills', 'generate_exploit.md')
        with open(skill_path, 'r') as f:
            skill_instructions = f.read()

        prompt = f"""{skill_instructions}

Vulnerability Details:
{json.dumps(vulnerability, indent=2)}

File Name: {filename}

Target Code:
```python
{file_content}
```
"""
        try:
            raw_response, parsed = self._generate_with_retry(prompt)
            self._log_trace("create_exploit", f"Exploiting {filename}", parsed)
            return parsed
        except Exception as e:
            print(f"[!] Error creating exploit: {e}")
            return None

    def create_patch(self, vulnerability, file_content, filename, error_feedback=None):
        """Create a patch. If error_feedback is provided, it's a retry with previous error."""
        skill_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'skills', 'repair_code.md')
        with open(skill_path, 'r') as f:
            skill_instructions = f.read()

        prompt = f"""{skill_instructions}

Vulnerability Details:
{json.dumps(vulnerability, indent=2)}

File Name: {filename}

Original Code:
```python
{file_content}
```
"""
        if error_feedback:
            prompt += f"""

IMPORTANT: Your previous patch attempt FAILED with this error:
```
{error_feedback[:1000]}
```
Please analyze the error and generate a CORRECTED patch.
"""

        try:
            raw_response, parsed = self._generate_with_retry(prompt)
            action = "create_patch_retry" if error_feedback else "create_patch"
            self._log_trace(action, f"Patching {filename}", parsed)
            return parsed
        except Exception as e:
            print(f"[!] Error creating patch: {e}")
            return None

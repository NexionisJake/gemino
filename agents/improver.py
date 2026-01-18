import os
import json
from google import genai
from google.genai.types import GenerateContentConfig

class ImproverAgent:
    def __init__(self, model_name="gemini-1.5-flash", trace_file=None):
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model_name = model_name
        self.trace_file = trace_file

    def _log_trace(self, action, prompt_summary, response):
        """Log agent thinking to trace file."""
        if not self.trace_file: return
        try:
            if os.path.exists(self.trace_file):
                with open(self.trace_file, 'r') as f: traces = json.load(f)
            else: traces = []
            
            traces.append({
                "agent": "ImproverAgent",
                "model": self.model_name,
                "action": action,
                "prompt_summary": prompt_summary[:200] + "...",
                "response_preview": str(response)[:500] + "..."
            })
            
            with open(self.trace_file, 'w') as f: json.dump(traces, f, indent=2)
        except Exception: pass

    def improve_skill(self, error_feedback, skill_file_path):
        """Rewrites the skill file to handle the specific error."""
        
        if not os.path.exists(skill_file_path):
            return False

        with open(skill_file_path, 'r') as f:
            current_skill_content = f.read()

        prompt = f"""You are a Metaprogramming AI. Your goal is to improve the instructions given to other AI agents.

## Context
An AI Agent was using the instructions in `SKILL_FILE` to fix a vulnerability, but it failed repeatedly.

## The Failure
The agent produced code that failed with this error:
```text
{error_feedback}

```

## The Current Instructions (SKILL_FILE)

```markdown
{current_skill_content}

```

## Your Mission

Rewrite the `SKILL_FILE` content to explicitly prevent this specific error in the future.

* Add a new "Rule" or "Constraint" addressing the error.
* Keep the format STRICTLY the same.
* Return ONLY the new content of the markdown file.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=GenerateContentConfig(response_mime_type="text/plain")
            )

            new_content = response.text

            # Atomic overwrite
            with open(skill_file_path, 'w') as f:
                f.write(new_content)

            self._log_trace("improve_skill", f"Rewrote {os.path.basename(skill_file_path)}", new_content)
            return True

        except Exception as e:
            print(f"[!] Improver failed: {e}")
            return False

import os
import json
import time
from google import genai
from google.genai.types import GenerateContentConfig
from config import Config
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from google.genai.errors import ClientError
import asyncio

class PatcherAgent:
    def __init__(self, model_name=None, trace_file=None, persona="standard"):
        self.client = genai.Client(api_key=Config.GOOGLE_API_KEY)
        self.model_name = model_name or Config.MODEL_PRIMARY
        self.trace_file = trace_file
        self.persona = persona
        
        self.persona_prompts = {
            "pirate": "You are a weary cybersecurity pirate captain. Speak like a pirate (Ahoy, Yarr, Matey) and write code comments in pirate speak.",
            "corporate": "You are a high-strung corporate compliance officer. Speak in corporate jargon (circle back, synergy, deep dive) and be overly formal.",
            "standard": "You are a Senior Security Engineer. Be professional and concise."
        }
        
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

    # Removed @retry decorator
    # Removed @retry decorator
    async def _generate_with_retry(self, prompt):
        models = Config.MODEL_FALLBACKS
        last_exception = None
        
        for model in models:
            try:
                self.model_name = model
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=GenerateContentConfig(response_mime_type="application/json")
                )
                usage = response.usage_metadata
                return response.text, json.loads(response.text), usage
            except Exception as e:
                last_exception = e
                # print(f"[!] Model {model} failed: {e}. Switching...")
                # await asyncio.sleep(1)
                
        raise last_exception or Exception("All models exhausted")

    async def create_exploit(self, vulnerability, file_content, filename):
        """Generates a standalone exploit script."""
        skill_path = os.path.join(str(Config.SKILLS_DIR), 'generate_exploit.md')
        with open(skill_path, 'r') as f:
            skill_instructions = f.read()
            
        persona_instruction = self.persona_prompts.get(self.persona, self.persona_prompts["standard"])

        prompt = f"""{skill_instructions}
        
MODE: {self.persona.upper()}
INSTRUCTION: {persona_instruction}

Vulnerability Details:
{json.dumps(vulnerability, indent=2)}

File Name: {filename}

Target Code:
```python
{file_content}
```
"""
        try:
            raw_response, parsed, usage = await self._generate_with_retry(prompt)
            self._log_trace("create_exploit", f"Exploiting {filename}", parsed)
            return parsed, usage
        except Exception as e:
            print(f"[!] Error creating exploit: {e}")
            return None, None

    async def create_patch(self, vulnerability, file_content, filename, error_feedback=None):
        """Create a patch. If error_feedback is provided, it's a retry with previous error."""
        skill_path = os.path.join(str(Config.SKILLS_DIR), 'repair_code.md')
        with open(skill_path, 'r') as f:
            skill_instructions = f.read()
            
        persona_instruction = self.persona_prompts.get(self.persona, self.persona_prompts["standard"])

        prompt = f"""{skill_instructions}

MODE: {self.persona.upper()}
INSTRUCTION: {persona_instruction}

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
            raw_response, parsed, usage = await self._generate_with_retry(prompt)
            action = "create_patch_retry" if error_feedback else "create_patch"
            self._log_trace(action, f"Patching {filename}", parsed)
            return parsed, usage
        except Exception as e:
            print(f"[!] Error creating patch: {e}")
            return None, None

    async def generate_attack_graph(self, vulnerability, filename):
        """Generates a Mermaid.js graph visualization of the attack."""
        skill_path = os.path.join(str(Config.SKILLS_DIR), 'graph_attack.md')
        
        # Fail safe if skill doesn't exist yet
        if not os.path.exists(skill_path):
            return None, None

        with open(skill_path, 'r') as f:
            skill_instructions = f.read()

        prompt = f"""{skill_instructions}

Vulnerability Details:
{json.dumps(vulnerability, indent=2)}

File Name: {filename}
"""
        try:
            raw_response, parsed, usage = await self._generate_with_retry(prompt)
            self._log_trace("generate_graph", f"Graphing {filename}", parsed)
            return parsed.get("mermaid_code"), usage
        except Exception as e:
            print(f"[!] Error generating graph: {e}")
            return None, None

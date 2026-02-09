import os
import json
import time
from google import genai
import re
import hashlib
from config import Config
from google.genai.types import GenerateContentConfig
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from google.genai.errors import ClientError

class ScannerAgent:
    def __init__(self, model_name=None, trace_file=None):
        self.model_name = model_name or Config.MODEL_PRIMARY
        self.client = genai.Client(api_key=Config.GOOGLE_API_KEY)
        self.trace_file = trace_file
        self.cache_file = os.path.join(str(Config.REPORTS_DIR), '.argus_cache.json')
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def _compute_hash(self, content):
        return hashlib.md5(content.encode('utf-8')).hexdigest()
        
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

    def _redact_secrets(self, content):
        """Redacts potential secrets from code."""
        # Generic patterns for API keys, tokens, etc.
        patterns = [
            r"AIza[0-9A-Za-z-_]{35}", # Google API Key
            r"sk-[a-zA-Z0-9]{32,}",   # OpenAI Key
            r"(?i)(api_key|secret|token)\s*=\s*['\"]([a-zA-Z0-9_\-]{20,})['\"]"
        ]
        
        redacted = content
        for pattern in patterns:
            redacted = re.sub(pattern, r"\1='[REDACTED]'", redacted)
            
        return redacted

    # Removed @retry decorator
    async def _generate_with_retry(self, prompt):
        models = Config.MODEL_FALLBACKS
        last_exception = None
        
        for model in models:
            try:
                self.model_name = model
                # Use async client
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=GenerateContentConfig(response_mime_type="application/json")
                )
                usage = response.usage_metadata
                return response.text, json.loads(response.text), usage
            except Exception as e:
                last_exception = e
                print(f"[!] Model {model} failed: {e}. Switching...")
                # await asyncio.sleep(1) # Optional, but good for rate limits
                
        raise last_exception or Exception("All models exhausted")

    async def scan_file(self, file_path):
        return await self.scan_project([file_path])

    async def scan_project(self, file_paths):
        """Scans multiple files in a single request."""
        combined_code = ""
        files_to_process = []
        cached_results = {"vulnerabilities": []}
        
        for path in file_paths:
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    
                file_hash = self._compute_hash(content)
                cached_entry = self.cache.get(path)
                
                if cached_entry and cached_entry.get("hash") == file_hash:
                    # Cache hit
                    print(f"[dim]Cache hit for {os.path.basename(path)}[/dim]")
                    if cached_entry.get("vulns"):
                        cached_results["vulnerabilities"].extend(cached_entry["vulns"])
                    continue
                    
                # Cache miss
                content = self._redact_secrets(content)
                combined_code += f"\n\n--- FILE: {os.path.basename(path)} ---\n{content}\n"
                files_to_process.append(path)
                
            except Exception:
                pass
            
        if not files_to_process and not cached_results["vulnerabilities"]:
            return None, None
            
        if not files_to_process:
             # All cached
             return cached_results, None

        skill_path = os.path.join(str(Config.SKILLS_DIR), 'audit_code.md')
        with open(skill_path, 'r') as f:
            skill_instructions = f.read()
            
        prompt = f"{skill_instructions}\n\nFiles to Analyze:\n{combined_code}"
        
        try:
            raw_response, parsed, usage = await self._generate_with_retry(prompt)
            
            # Enforce correct filename in results is difficult here, rely on LLM
            # but we can filter known files
            if parsed and "vulnerabilities" in parsed:
                valid_names = [os.path.basename(p) for p in files_to_process]
                
                # Update Cache
                current_file_vulns = {} # file_path -> list of vulns
                
                for vuln in parsed["vulnerabilities"]:
                    fname = vuln.get("file")
                    if fname not in valid_names:
                         vuln["file"] = "unknown"
                         continue
                         
                    # Find full path
                    full_path = next((p for p in files_to_process if os.path.basename(p) == fname), None)
                    if full_path:
                        if full_path not in current_file_vulns: current_file_vulns[full_path] = []
                        current_file_vulns[full_path].append(vuln)

                # Save to cache
                for path in files_to_process:
                    with open(path, 'r') as f: content = f.read()
                    self.cache[path] = {
                        "hash": self._compute_hash(content),
                        "vulns": current_file_vulns.get(path, [])
                    }
                self._save_cache()
                
                # Merge cached results
                parsed["vulnerabilities"].extend(cached_results["vulnerabilities"])
            
            self._log_trace("scan_project", f"Scanning {len(files_to_process)} files", parsed)
            return parsed, usage
        except Exception as e:
            print(f"[!] Error scanning project: {e}")
            return None, None


import os
import sys
import asyncio
import socketio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent directory to path to import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from agents.scanner import ScannerAgent
    from agents.patcher import PatcherAgent
    from vibe_engine import VibeEngine
except ImportError:
    # Mock for development if running isolated
    class ScannerAgent:
        async def scan_file(self, f): return ({"vulnerabilities": []}, 0)
    class PatcherAgent:
        async def create_patch(self, v, c, f): return "patched_code", {}
    class VibeEngine:
        def speak(self, t): pass
        def alert(self, t): pass
        def set_persona(self, p): pass

# Initialize FastAPI
app = FastAPI(title="Argus Security Auditor", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)


# Global State
guardian = None
observer = None
patcher = None  # Lazy init

class WebGuardian(FileSystemEventHandler):
    def __init__(self, target_dir, sio_server):
        self.target_dir = target_dir
        self.sio = sio_server
        self.scanner = ScannerAgent()
        self.vibe = VibeEngine()
        self.last_scan_time = 0
        self.scan_cooldown = 2

    def on_modified(self, event):
        if event.is_directory:
            return
        
        filename = event.src_path
        if filename.endswith(".py") and "exploit_" not in filename:
            current_time = asyncio.get_event_loop().time()
            # Note: asyncio.get_event_loop().time() might not work in thread. using time.time
            import time
            current_time = time.time()

            if current_time - self.last_scan_time < self.scan_cooldown:
                return
            self.last_scan_time = current_time

            asyncio.run_coroutine_threadsafe(self.process_file(filename), loop)

    async def process_file(self, filename):
        rel_path = os.path.relpath(filename, self.target_dir)
        await self.sio.emit('log', {'message': f'Change detected: {rel_path}', 'type': 'info'})
        
        try:
            scan_result, usage = await self.scanner.scan_file(filename)
            
            if scan_result and scan_result.get("vulnerabilities"):
                count = len(scan_result["vulnerabilities"])
                await self.sio.emit('log', {'message': f'⚠ Found {count} vulnerabilities in {rel_path}!', 'type': 'error'})
                await self.sio.emit('vulnerability_update', {'vulnerabilities': scan_result["vulnerabilities"], 'file': rel_path})
                # Auto-speak if critical
                self.vibe.alert("danger")
            else:
                await self.sio.emit('log', {'message': f'✓ {rel_path} is clean.', 'type': 'success'})
        
        except Exception as e:
            await self.sio.emit('log', {'message': f'Error scanning {rel_path}: {str(e)}', 'type': 'error'})

@app.on_event("startup")
async def startup_event():
    global loop
    loop = asyncio.get_running_loop()

@app.get("/")
async def root():
    return {"message": "Argus Neural Interface Online", "status": "active"}

@app.post("/api/start_watch")
async def start_watch(target: str = "target_code"):
    global guardian, observer
    if observer and observer.is_alive():
        return {"status": "already_watching"}
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    target_path = os.path.join(base_dir, target)
    
    if not os.path.exists(target_path):
        return {"status": "error", "message": "Target directory not found"}

    guardian = WebGuardian(target_path, sio)
    observer = Observer()
    observer.schedule(guardian, target_path, recursive=True)
    observer.start()
    
    return {"status": "started", "target": target_path}

@app.post("/api/stop_watch")
async def stop_watch():
    global observer
    if observer:
        observer.stop()
        observer.join()
        observer = None
    return {"status": "stopped"}

@app.post("/api/vibe_check")
async def vibe_check():
    """Triggers an audio response from the VibeEngine."""
    if guardian:
        guardian.vibe.speak("Systems nominal. Vibe check passed. Neural architecture functioning at 100 percent.")
        return {"status": "vibing", "message": "Vibe Check Initiated"}
    else:
        # Fallback if guardian not active
        vibe = VibeEngine()
        vibe.speak("Vibe Engine initialized. Waiting for Neural Link.")
        return {"status": "vibing", "message": "Vibe Engine Initialized"}

class FileRequest(BaseModel):
    path: str

@app.post("/api/file_content")
async def get_file_content(req: FileRequest):
    """Reads the content of a file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Security check: prevent traversing up
    safe_path = os.path.abspath(os.path.join(base_dir, "target_code", req.path))
    if not safe_path.startswith(os.path.join(base_dir, "target_code")):
         # For demo purposes, we might allow reading from the root if needed, but let's stick to target_code or relative paths from project root
         # Let's adjust logic to be relative to project root for flexibility
         target_path = os.path.join(base_dir, req.path)
    else:
        target_path = safe_path

    if not os.path.exists(target_path):
        # Try relative to target_code if fail
        target_path = os.path.join(base_dir, "target_code", req.path)
        if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail="File not found")

    with open(target_path, "r") as f:
        content = f.read()
    return {"content": content, "path": req.path}

class PatchRequest(BaseModel):
    vulnerability: dict
    file: str

@app.post("/api/auto_patch")
async def auto_patch(req: PatchRequest):
    """Attempts to auto-match a vulnerability."""
    global patcher
    if patcher is None:
        print("Initializing PatcherAgent lazily...")
        patcher = PatcherAgent()

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    target_path = os.path.join(base_dir, "target_code", req.file)
    
    if not os.path.exists(target_path):
         target_path = os.path.join(base_dir, req.file) # Try direct path
         if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail="File not found")

    with open(target_path, "r") as f:
        content = f.read()
    
    await sio.emit('log', {'message': f'Initiating Auto-Patch for {req.file}...', 'type': 'warning'})
    
    try:
        patched_data, usage = await patcher.create_patch(req.vulnerability, content, req.file)
        
        # Handle different key names from model
        new_code = patched_data.get("fixed_code") or patched_data.get("patched_code")
        
        if patched_data and new_code:
            # Apply patch
            with open(target_path, "w") as f:
                f.write(new_code)
            
            await sio.emit('log', {'message': f'Successfully patched {req.file}.', 'type': 'success'})
            return {"status": "patched"}
        else:
             print(f"Patch generation returned None or missing code key. Keys: {patched_data.keys() if patched_data else 'None'}")
             await sio.emit('log', {'message': f'Patch generation failed: Missing code in response.', 'type': 'error'})
             raise HTTPException(status_code=500, detail="Patch generation failed")
             
    except Exception as e:
        import traceback
        traceback.print_exc()
        await sio.emit('log', {'message': f'Patch error: {str(e)}', 'type': 'error'})
        raise HTTPException(status_code=500, detail=str(e))

@sio.event
async def connect(sid, environ):
    await sio.emit('log', {'message': 'Neural Link Established...'})

if __name__ == "__main__":
    uvicorn.run("main:socket_app", host="0.0.0.0", port=8000, reload=True)

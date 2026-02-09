
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # --- Paths ---
    BASE_DIR = Path(__file__).parent.resolve()
    REPORTS_DIR = BASE_DIR.parent / "reports"
    SKILLS_DIR = BASE_DIR / "skills"
    
    # Ensure directories exist
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # --- API Keys ---
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        # Construct a warning but don't crash yet, let main handle it
        pass

    # --- Models ---
    # Primary model for reasoning
    MODEL_PRIMARY = os.getenv("ARGUS_MODEL_PRIMARY", "gemini-1.5-flash-latest") # Default to flash for speed
    # Fallback models in order of preference
    MODEL_FALLBACKS = [
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-2.0-flash-exp"
    ]

    # --- Scanner Settings ---
    SCAN_RETRIES = int(os.getenv("ARGUS_SCAN_RETRIES", "3"))
    MAX_CONCURRENT_SCANS = int(os.getenv("ARGUS_MAX_CONCURRENT_SCANS", "5"))

    # --- Patcher Settings ---
    MAX_PATCH_RETRIES = int(os.getenv("ARGUS_PATCH_RETRIES", "2"))
    
    # --- Vibe Engine (TTS) ---
    VIBE_ENABLED = os.getenv("ARGUS_VIBE_ENABLED", "true").lower() == "true"
    TTS_VOICE_DEFAULT = os.getenv("ARGUS_TTS_VOICE", "en-US-AriaNeural")
    TTS_VOICE_PIRATE = "en-US-ChristopherNeural"  # Deep male voice
    TTS_VOICE_CORPORATE = "en-US-JennyNeural"    # Professional female voice

    # --- Cost Tracking (Approximate per 1M tokens) ---
    COST_FLASH_INPUT = 0.075
    COST_FLASH_OUTPUT = 0.30
    COST_PRO_INPUT = 3.50
    COST_PRO_OUTPUT = 10.50

config = Config()

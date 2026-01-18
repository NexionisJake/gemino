import os
import time
from google import genai
from google.genai.errors import ClientError
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../.env')
load_dotenv(env_path)

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not set")
    exit(1)

client = genai.Client(api_key=api_key)
model_name = "gemini-flash-latest"

print(f"Testing connectivity to {model_name}...")
start_time = time.time()

try:
    print("Listing available models...")
    for model in client.models.list():
        print(f" - {model.name}")
        
    response = client.models.generate_content(
        model=model_name,
        contents="Ping"
    )
    elapsed = time.time() - start_time
    print(f"✓ Success! Response received in {elapsed:.2f}s")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"✗ Failed: {e}")

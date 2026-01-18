import os
import time
from google import genai
from google.genai.errors import ClientError

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not set")
    exit(1)

client = genai.Client(api_key=api_key)
model_name = "gemini-3-flash-preview"

print(f"Testing connectivity to {model_name}...")
start_time = time.time()

try:
    response = client.models.generate_content(
        model=model_name,
        contents="Ping"
    )
    elapsed = time.time() - start_time
    print(f"✓ Success! Response received in {elapsed:.2f}s")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()

import os
import time
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# We expect ALPACA_API_KEY and ALPACA_SECRET_KEY to be set in the environment
if "ALPACA_API_KEY" not in os.environ or "ALPACA_SECRET_KEY" not in os.environ:
    print("WARNING: Alpaca API keys not found in environment. Please set them in .env")

print("Starting live dry-run daemon for VRP-Agent...")
while True:
    print(f"\n--- Running agent.py at {datetime.now()} ---")
    try:
        subprocess.run([r".\venv\Scripts\python", r"src\orchestration\agent.py"], check=True)
    except Exception as e:
        print(f"Error running agent: {e}")
    
    # Wait 4 hours (14400 seconds)
    print("Waiting 4 hours until next run...")
    time.sleep(14400)

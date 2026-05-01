import asyncio
import os
from dotenv import load_dotenv

# Load env before importing app dependencies so Groq gets the key
load_dotenv()

from app.schemas.common import UserInput
from app.routers.agent import pipeline_endpoint
import json

async def main():
    # Verify key is loaded
    api_key = os.environ.get("GROQ_API_KEY", "")
    print(f"Loaded API Key: {'YES' if api_key else 'NO'} (Length: {len(api_key)})")
    
    payload = UserInput(
        business_domain="SaaS Fintech for small businesses",
        content_goal="Increase signups for our new API product",
        target_audience="Startup founders and CTOs",
        tone="authoritative but approachable",
    )
    
    print("\nRunning full AI pipeline (Decision -> Simulate -> Generate -> Feedback)...")
    try:
        result = pipeline_endpoint(payload)
        print("\n=== PIPELINE SUCCESS ===")
        print(result.model_dump_json(indent=2))
        print("========================")
    except Exception as e:
        print(f"\n=== PIPELINE FAILED ===")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

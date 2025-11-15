#!/usr/bin/env python3
"""Quick script to test web chat session creation."""

import requests
import json

def test_session():
    """Test creating a new session."""

    # Create new session
    print("Creating new session...")
    response = requests.post(
        "http://localhost:8000/api/session/new",
        json={
            "config": {
                "orchestrator_type": "function_calling",
                "enable_memory": False,
                "confirmation_mode": "auto"
            }
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session created: {data['session_id']}")
        print(f"   Config: {json.dumps(data['config'], indent=2)}")
        return data['session_id']
    else:
        print(f"❌ Failed to create session: {response.status_code}")
        print(f"   {response.text}")
        return None

if __name__ == "__main__":
    test_session()

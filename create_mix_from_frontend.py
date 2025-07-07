#!/usr/bin/env python3
"""
Create audio mix from frontend session data
Takes the session ID from your frontend and creates the actual audio mix
"""

import json
import requests
import sys
from mix_generator import create_mix_from_session_data

def get_session_data(session_id, api_base="https://4as1uxx25a.execute-api.us-east-1.amazonaws.com/dev"):
    """Fetch session data from the API"""
    try:
        url = f"{api_base}/api/session/{session_id}"
        print(f"🔄 Fetching session data from: {url}")
        
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error fetching session: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error fetching session data: {e}")
        return None

def main():
    # Use the session ID from your frontend
    session_id = "531b1f5e-4169-4ce6-99f2-e5e865437bf5"
    
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    
    print(f"🎯 Creating mix from session: {session_id}")
    
    # Fetch session data
    session_data = get_session_data(session_id)
    if not session_data:
        print("❌ Could not fetch session data")
        return
    
    print(f"✅ Session data retrieved:")
    print(f"   Episode: {session_data.get('episode_number')}")
    print(f"   Theme: {session_data.get('theme')}")
    print(f"   Ideas: {len(session_data.get('ideas', []))}")
    print(f"   Music: {len(session_data.get('music_generations', []))}")
    
    # Save session data for reference
    with open('latest_session.json', 'w') as f:
        json.dump(session_data, f, indent=2)
    print("💾 Session data saved to: latest_session.json")
    
    # Create the mix
    print("\n🎵 Starting mix generation...")
    output_file = create_mix_from_session_data(session_data)
    
    if output_file:
        print(f"\n🎉 SUCCESS! Your No Agenda mix is ready!")
        print(f"📁 File: {output_file}")
        print(f"\n🎧 Play your mix:")
        print(f"   open '{output_file}'")
        print(f"\n📱 Or drag and drop into your audio player!")
    else:
        print("❌ Mix generation failed")

if __name__ == '__main__':
    main()
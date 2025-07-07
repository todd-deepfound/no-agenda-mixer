#!/usr/bin/env python3
"""
Generate themed mixes directly from frontend session data
Easy-to-use script for creating No Agenda mixes with different themes
"""

import json
import requests
import sys
from datetime import datetime
from pathlib import Path
from pydub import AudioSegment

def timestamp_to_seconds(timestamp_str):
    """Convert timestamp string like '1:25:45' to seconds"""
    try:
        parts = timestamp_str.split(':')
        if len(parts) == 2:  # MM:SS format
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS format
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 0
    except ValueError:
        return 0

def create_session_and_mix(episode=1779, theme="Best Of"):
    """Create a new session and generate a mix"""
    
    api_base = "https://4as1uxx25a.execute-api.us-east-1.amazonaws.com/dev"
    
    # Create a new session
    print(f"🔄 Creating session for Episode {episode} - Theme: {theme}")
    
    session_response = requests.post(
        f"{api_base}/api/start_session",
        headers={'Content-Type': 'application/json'},
        json={'episode_number': episode, 'theme': theme}
    )
    
    if session_response.status_code != 200:
        print(f"❌ Failed to create session: {session_response.text}")
        return None
    
    session_data = session_response.json()
    session_id = session_data['session_id']
    print(f"✅ Session created: {session_id}")
    
    # Generate ideas
    print("🧠 Generating mix ideas...")
    ideas_response = requests.post(
        f"{api_base}/api/generate_ideas/{session_id}",
        headers={'Content-Type': 'application/json'},
        json={}
    )
    
    if ideas_response.status_code != 200:
        print(f"❌ Failed to generate ideas: {ideas_response.text}")
        return None
    
    print("✅ Ideas generated successfully")
    
    # Get the full session data
    full_session_response = requests.get(f"{api_base}/api/session/{session_id}")
    if full_session_response.status_code != 200:
        print(f"❌ Failed to get session data: {full_session_response.text}")
        return None
    
    session_data = full_session_response.json()
    
    # Now create the mix
    return create_mix_from_session(session_data)

def create_mix_from_session(session_data):
    """Create an audio mix from session data"""
    
    episode_number = session_data.get('episode_number', 1779)
    theme = session_data.get('theme', 'Best Of')
    ideas = session_data.get('ideas', [])
    
    if not ideas:
        print("❌ No ideas found in session data")
        return None
    
    latest_ideas = ideas[0]['ideas']
    segments = latest_ideas.get('segments', [])
    
    print(f"🎧 Creating mix for Episode {episode_number} - Theme: {theme}")
    print(f"📝 Found {len(segments)} segments")
    
    # Load the podcast
    podcast_path = Path(__file__).parent / 'audio' / f'NA-{episode_number}-2025-07-06-Final.mp3'
    if not podcast_path.exists():
        print(f"❌ Podcast file not found: {podcast_path}")
        return None
    
    try:
        podcast = AudioSegment.from_mp3(str(podcast_path))
        print(f"✅ Loaded podcast: {len(podcast)/60000:.1f} minutes")
    except Exception as e:
        print(f"❌ Error loading podcast: {e}")
        return None
    
    # Extract segments and create mix
    mix_segments = []
    
    for i, segment in enumerate(segments):
        name = segment.get('name', f'Segment {i+1}')
        timestamp = segment.get('timestamp', '0:00:00')
        duration = segment.get('duration', 15)
        
        print(f"🎙️  {i+1}. {name} ({timestamp}, {duration}s)")
        
        start_ms = timestamp_to_seconds(timestamp) * 1000
        end_ms = start_ms + (duration * 1000)
        
        if start_ms < len(podcast) and end_ms <= len(podcast):
            segment_audio = podcast[start_ms:end_ms]
            segment_audio = segment_audio.fade_in(300).fade_out(300)
            mix_segments.append(segment_audio)
            
            # Add transition between segments
            if i < len(segments) - 1:
                mix_segments.append(AudioSegment.silent(duration=800))
    
    if not mix_segments:
        print("❌ No segments extracted")
        return None
    
    # Combine and export
    final_mix = sum(mix_segments).normalize()
    
    timestamp = datetime.now().strftime("%H%M%S")
    safe_theme = theme.replace(' ', '_').replace('/', '_')
    output_path = Path(__file__).parent / 'output' / f'NA{episode_number}_{safe_theme}_{timestamp}.mp3'
    output_path.parent.mkdir(exist_ok=True)
    
    try:
        final_mix.export(str(output_path), format='mp3', bitrate='192k')
        
        print(f"✅ Mix created: {output_path}")
        print(f"⏱️  Duration: {len(final_mix)/1000:.1f} seconds")
        print(f"🎵 Segments: {len(segments)}")
        
        return str(output_path)
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return None

def main():
    """Main function - easy theme selection"""
    
    themes = {
        '1': 'Best Of',
        '2': 'Conspiracy Corner', 
        '3': 'Media Meltdown',
        '4': 'Donation Nation',
        '5': 'Musical Mayhem'
    }
    
    print("🎧 No Agenda Mix Generator")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        # Use command line argument
        theme_choice = sys.argv[1]
        if theme_choice in themes:
            theme = themes[theme_choice]
        else:
            theme = theme_choice  # Custom theme
    else:
        # Interactive mode
        print("Choose a theme:")
        for key, value in themes.items():
            print(f"  {key}. {value}")
        print("  6. Custom theme")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice in themes:
            theme = themes[choice]
        elif choice == '6':
            theme = input("Enter custom theme: ").strip()
            if not theme:
                theme = "Custom"
        else:
            print("Invalid choice, using 'Best Of'")
            theme = "Best Of"
    
    print(f"\n🎯 Creating mix with theme: {theme}")
    
    # Create session and mix
    output_file = create_session_and_mix(episode=1779, theme=theme)
    
    if output_file:
        print(f"\n🎉 SUCCESS! Your mix is ready!")
        print(f"📁 File: {output_file}")
        print(f"\n🎧 Play now:")
        print(f"   open '{output_file}'")
        
        # Auto-open the file
        import subprocess
        subprocess.run(['open', output_file])
    else:
        print("❌ Mix generation failed")

if __name__ == '__main__':
    main()
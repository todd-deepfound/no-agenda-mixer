#!/usr/bin/env python3
"""
Quick POC Mix Generator
Creates a fast proof-of-concept mix using just the podcast segments (no AI music generation wait)
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
            print(f"Warning: Invalid timestamp format: {timestamp_str}")
            return 0
    except ValueError:
        print(f"Warning: Could not parse timestamp: {timestamp_str}")
        return 0

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

def create_quick_mix(session_data):
    """Create a quick POC mix from session data"""
    
    # Extract session info
    episode_number = session_data.get('episode_number', 1779)
    theme = session_data.get('theme', 'Best Of')
    ideas = session_data.get('ideas', [])
    
    if not ideas:
        print("❌ No ideas found in session data")
        return None
    
    # Get the first (latest) ideas entry
    latest_ideas = ideas[0]['ideas']
    segments = latest_ideas.get('segments', [])
    
    print(f"🎧 Creating quick mix for Episode {episode_number} - Theme: {theme}")
    print(f"📝 Found {len(segments)} segments to extract")
    
    # Load the podcast audio
    podcast_path = Path(__file__).parent / 'audio' / f'NA-{episode_number}-2025-07-06-Final.mp3'
    if not podcast_path.exists():
        print(f"❌ Podcast file not found: {podcast_path}")
        return None
    
    print(f"📁 Loading podcast: {podcast_path}")
    try:
        podcast = AudioSegment.from_mp3(str(podcast_path))
        print(f"✅ Loaded podcast: {len(podcast)/1000:.1f} seconds ({len(podcast)/60000:.1f} minutes)")
    except Exception as e:
        print(f"❌ Error loading podcast: {e}")
        return None
    
    # Create the mix with just podcast segments and simple transitions
    mix_segments = []
    
    # Add a simple intro silence
    intro_silence = AudioSegment.silent(duration=1000)  # 1 second silence
    mix_segments.append(intro_silence)
    
    # Extract and add podcast segments
    for i, segment in enumerate(segments):
        name = segment.get('name', f'Segment {i+1}')
        timestamp = segment.get('timestamp', '0:00:00')
        duration = segment.get('duration', 15)
        description = segment.get('description', '')
        
        print(f"🎙️  Extracting: {name} at {timestamp} ({duration}s) - {description}")
        
        # Convert timestamp to milliseconds
        start_ms = timestamp_to_seconds(timestamp) * 1000
        end_ms = start_ms + (duration * 1000)
        
        # Extract the segment
        if start_ms < len(podcast) and end_ms <= len(podcast):
            segment_audio = podcast[start_ms:end_ms]
            
            # Add a short fade in/out for smooth transitions
            segment_audio = segment_audio.fade_in(500).fade_out(500)
            mix_segments.append(segment_audio)
            
            # Add a short transition between segments (except after last segment)
            if i < len(segments) - 1:
                transition = AudioSegment.silent(duration=500)  # 0.5 second silence
                mix_segments.append(transition)
        else:
            print(f"⚠️  Warning: Segment {name} timestamp {timestamp} is beyond podcast duration")
    
    if not mix_segments:
        print("❌ No segments could be extracted")
        return None
    
    # Combine all segments
    print("🔄 Combining segments...")
    final_mix = sum(mix_segments)
    
    # Apply some overall audio processing
    final_mix = final_mix.normalize()
    
    # Set output path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')
    output_path = Path(__file__).parent / 'output' / f'NA_EP{episode_number}_{safe_theme}_{timestamp}_POC.mp3'
    output_path.parent.mkdir(exist_ok=True)
    
    # Export the final mix
    print(f"💾 Exporting mix to: {output_path}")
    try:
        final_mix.export(str(output_path), format='mp3', bitrate='192k')
        
        # Create a metadata file
        metadata = {
            'episode_number': episode_number,
            'theme': theme,
            'segments': segments,
            'created_at': datetime.now().isoformat(),
            'duration_seconds': len(final_mix) / 1000,
            'segments_count': len(segments),
            'mix_file': str(output_path),
            'type': 'POC_mix'
        }
        
        metadata_path = output_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ POC Mix created successfully!")
        print(f"📁 Audio file: {output_path}")
        print(f"📋 Metadata: {metadata_path}")
        print(f"⏱️  Duration: {len(final_mix)/1000:.1f} seconds")
        print(f"🎵 Segments: {len(segments)}")
        
        return str(output_path)
        
    except Exception as e:
        print(f"❌ Error exporting mix: {e}")
        return None

def main():
    # Use the session ID from your frontend
    session_id = "531b1f5e-4169-4ce6-99f2-e5e865437bf5"
    
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    
    print(f"🎯 Creating quick POC mix from session: {session_id}")
    
    # Fetch session data
    session_data = get_session_data(session_id)
    if not session_data:
        print("❌ Could not fetch session data")
        return
    
    print(f"✅ Session data retrieved:")
    print(f"   Episode: {session_data.get('episode_number')}")
    print(f"   Theme: {session_data.get('theme')}")
    print(f"   Ideas: {len(session_data.get('ideas', []))}")
    
    # Create the quick POC mix
    print("\n🎵 Starting quick mix generation...")
    output_file = create_quick_mix(session_data)
    
    if output_file:
        print(f"\n🎉 SUCCESS! Your No Agenda POC mix is ready!")
        print(f"📁 File: {output_file}")
        print(f"\n🎧 Play your mix:")
        print(f"   open '{output_file}'")
        print(f"\n📱 Or drag and drop into your audio player!")
        print(f"\n💡 This is a POC with just the segments. Use mix_generator.py for full AI music integration.")
    else:
        print("❌ POC mix generation failed")

if __name__ == '__main__':
    main()
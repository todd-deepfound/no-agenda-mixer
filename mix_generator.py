#!/usr/bin/env python3
"""
No Agenda Mix Generator
Creates actual audio mixes from frontend session data using the downloaded podcast and FAL.ai music
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
import requests
from pydub import AudioSegment
import tempfile

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

def load_fal_api_key():
    """Load FAL.ai API key from config"""
    config_path = Path(__file__).parent / 'config' / '.env'
    if config_path.exists():
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('FAL_API_KEY='):
                    return line.split('=', 1)[1].strip()
    return None

def generate_real_music_with_fal(prompt, duration=30):
    """Generate real music using FAL.ai API"""
    api_key = load_fal_api_key()
    if not api_key:
        print("Warning: FAL_API_KEY not found, skipping real music generation")
        return None
    
    try:
        print(f"🎵 Generating music with FAL.ai: {prompt[:50]}...")
        
        headers = {
            'Authorization': f'Key {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'prompt': prompt,
            'duration': duration
        }
        
        response = requests.post(
            'https://fal.run/fal-ai/stable-audio',
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            audio_url = result.get('audio_file', {}).get('url')
            
            if audio_url:
                print(f"✅ Music generated successfully: {audio_url}")
                
                # Download the audio file
                audio_response = requests.get(audio_url)
                if audio_response.status_code == 200:
                    # Save to temp file and load with pydub
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        temp_file.write(audio_response.content)
                        temp_path = temp_file.name
                    
                    try:
                        music_audio = AudioSegment.from_wav(temp_path)
                        os.unlink(temp_path)  # Clean up temp file
                        return music_audio
                    except Exception as e:
                        print(f"Error loading generated audio: {e}")
                        os.unlink(temp_path)
                        return None
                else:
                    print(f"Failed to download audio file: {audio_response.status_code}")
                    return None
            else:
                print("No audio URL in response")
                return None
        else:
            print(f"FAL.ai API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling FAL.ai: {e}")
        return None

def create_mix_from_session_data(session_data, output_path=None):
    """Create an audio mix from frontend session data"""
    
    # Extract session info
    episode_number = session_data.get('episode_number', 1779)
    theme = session_data.get('theme', 'Best Of')
    ideas = session_data.get('ideas', [])
    music_generations = session_data.get('music_generations', [])
    
    if not ideas:
        print("❌ No ideas found in session data")
        return None
    
    # Get the first (latest) ideas entry
    latest_ideas = ideas[0]['ideas']
    segments = latest_ideas.get('segments', [])
    music_prompts = latest_ideas.get('music_prompts', [])
    
    print(f"🎧 Creating mix for Episode {episode_number} - Theme: {theme}")
    print(f"📝 Found {len(segments)} segments to extract")
    print(f"🎵 Found {len(music_prompts)} music prompts")
    
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
    
    # Create the mix
    mix_segments = []
    
    # Generate intro music if we have music prompts
    intro_music = None
    if music_prompts and len(music_prompts) > 0:
        intro_music = generate_real_music_with_fal(music_prompts[0], duration=10)
        if intro_music:
            print("🎵 Adding intro music...")
            mix_segments.append(intro_music[:10000])  # 10 seconds
    
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
            
            # Add transition music between segments (except after last segment)
            if i < len(segments) - 1 and len(music_prompts) > 1:
                transition_music = generate_real_music_with_fal(
                    f"Short transition music, {theme.lower()} style, 5 seconds", 
                    duration=5
                )
                if transition_music:
                    mix_segments.append(transition_music[:5000])  # 5 seconds
                else:
                    # Add a short silence as transition
                    mix_segments.append(AudioSegment.silent(duration=1000))  # 1 second
        else:
            print(f"⚠️  Warning: Segment {name} timestamp {timestamp} is beyond podcast duration")
    
    # Generate outro music
    if music_prompts and len(music_prompts) > 2:
        outro_music = generate_real_music_with_fal(music_prompts[2], duration=15)
        if outro_music:
            print("🎵 Adding outro music...")
            mix_segments.append(outro_music[:15000])  # 15 seconds
    
    if not mix_segments:
        print("❌ No segments could be extracted")
        return None
    
    # Combine all segments
    print("🔄 Combining segments...")
    final_mix = sum(mix_segments)
    
    # Apply some overall audio processing
    # Normalize the audio levels
    final_mix = final_mix.normalize()
    
    # Set output path if not provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_path = Path(__file__).parent / 'output' / f'NA_Episode_{episode_number}_{safe_theme}_{timestamp}.mp3'
        output_path.parent.mkdir(exist_ok=True)
    
    # Export the final mix
    print(f"💾 Exporting mix to: {output_path}")
    try:
        final_mix.export(str(output_path), format='mp3', bitrate='192k')
        
        # Create a metadata file with mix information
        metadata = {
            'episode_number': episode_number,
            'theme': theme,
            'segments': segments,
            'music_prompts': music_prompts,
            'created_at': datetime.now().isoformat(),
            'duration_seconds': len(final_mix) / 1000,
            'segments_count': len(segments),
            'mix_file': str(output_path)
        }
        
        metadata_path = output_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Mix created successfully!")
        print(f"📁 Audio file: {output_path}")
        print(f"📋 Metadata: {metadata_path}")
        print(f"⏱️  Duration: {len(final_mix)/1000:.1f} seconds")
        print(f"🎵 Segments: {len(segments)}")
        
        return str(output_path)
        
    except Exception as e:
        print(f"❌ Error exporting mix: {e}")
        return None

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python mix_generator.py <session_data.json>")
        print("       python mix_generator.py '<session_json_string>'")
        sys.exit(1)
    
    input_arg = sys.argv[1]
    
    # Try to load as file first, then as JSON string
    try:
        if os.path.isfile(input_arg):
            with open(input_arg, 'r') as f:
                session_data = json.load(f)
        else:
            session_data = json.loads(input_arg)
    except Exception as e:
        print(f"❌ Error loading session data: {e}")
        sys.exit(1)
    
    # Create the mix
    output_file = create_mix_from_session_data(session_data)
    if output_file:
        print(f"\n🎉 Mix generation complete! Play with:")
        print(f"   open '{output_file}'")
    else:
        print("❌ Mix generation failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
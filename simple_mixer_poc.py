#!/usr/bin/env python3
"""
Simple Mixer POC: Actually create a basic mix
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import openai
from pydub import AudioSegment
import random

# Load environment
load_dotenv('config/.env')

# Initialize GROK client
client = openai.OpenAI(
    api_key=os.getenv('GROK_API_KEY'),
    base_url=os.getenv('GROK_API_URL', 'https://api.x.ai/v1')
)

class SimpleMixerPOC:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.audio_dir = self.base_dir / 'audio'
        self.output_dir = self.base_dir / 'output'
        self.clips_dir = self.base_dir / 'clips'
        
        # Episode 1779 audio file
        self.episode_file = self.audio_dir / 'NA-1779-2025-07-06-Final.mp3'
        
    def get_mix_plan_from_ai(self):
        """Get a simple mix plan from GROK"""
        print("🤖 Asking GROK for a creative mix plan...")
        
        prompt = """Create a simple 60-second mix plan for No Agenda Episode 1779.
        
        Return JSON with 5 segments:
        {
          "mix_title": "Creative title",
          "description": "What makes this mix special",
          "segments": [
            {
              "name": "Segment name",
              "start_time": "MM:SS",
              "duration": 10,
              "effect": "none|fade|echo|speed",
              "reason": "Why this is funny/interesting"
            }
          ]
        }
        
        Focus on:
        - Opening with energy (like "In the morning!")
        - Include something funny in the middle
        - End with a memorable moment
        
        Use random timestamps spread throughout a 3-hour show.
        Keep each segment 5-15 seconds.
        """
        
        response = client.chat.completions.create(
            model=os.getenv('GROK_MODEL', 'grok-3-latest'),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.8
        )
        
        plan = json.loads(response.choices[0].message.content)
        print(f"\n✨ Mix Title: {plan['mix_title']}")
        print(f"📝 Description: {plan['description']}\n")
        
        return plan
    
    def extract_segment(self, full_audio, start_time, duration, effect=None):
        """Extract a segment from the full audio"""
        # Convert MM:SS to milliseconds
        parts = start_time.split(':')
        start_ms = (int(parts[0]) * 60 + int(parts[1])) * 1000
        end_ms = start_ms + (duration * 1000)
        
        # Extract segment
        segment = full_audio[start_ms:end_ms]
        
        # Apply simple effects
        if effect == 'fade':
            segment = segment.fade_in(500).fade_out(500)
        elif effect == 'echo':
            # Simple echo effect
            echo = segment - 10  # Reduce volume
            segment = segment.overlay(echo, position=200)
        elif effect == 'speed':
            # Speed up slightly
            segment = segment._spawn(segment.raw_data, overrides={
                "frame_rate": int(segment.frame_rate * 1.2)
            }).set_frame_rate(segment.frame_rate)
        
        return segment
    
    def create_simple_mix(self):
        """Create a simple mix based on AI suggestions"""
        print("🎵 Creating Simple Mix POC\n")
        
        # Get mix plan from AI
        plan = self.get_mix_plan_from_ai()
        
        # Load the full episode
        print("📂 Loading episode audio...")
        if not self.episode_file.exists():
            print("❌ Error: Episode file not found!")
            print(f"   Looking for: {self.episode_file}")
            return None
            
        full_audio = AudioSegment.from_mp3(self.episode_file)
        print(f"✅ Loaded {len(full_audio) / 1000 / 60:.1f} minutes of audio\n")
        
        # Extract segments
        segments = []
        for i, seg_info in enumerate(plan['segments']):
            print(f"🎯 Extracting segment {i+1}: {seg_info['name']}")
            print(f"   Time: {seg_info['start_time']} | Duration: {seg_info['duration']}s")
            print(f"   Reason: {seg_info['reason']}")
            
            try:
                segment = self.extract_segment(
                    full_audio,
                    seg_info['start_time'],
                    seg_info['duration'],
                    seg_info.get('effect')
                )
                segments.append(segment)
                print("   ✅ Extracted successfully\n")
            except Exception as e:
                print(f"   ❌ Error: {e}\n")
                # Use a random segment as fallback
                random_start = random.randint(0, len(full_audio) - 10000)
                segment = full_audio[random_start:random_start + 10000]
                segments.append(segment)
        
        # Combine segments
        print("🎛️ Combining segments...")
        if not segments:
            print("❌ No segments to combine!")
            return None
            
        final_mix = segments[0]
        for segment in segments[1:]:
            # Add 0.5 second crossfade between segments
            final_mix = final_mix.append(segment, crossfade=500)
        
        # Save the mix
        output_file = self.output_dir / f"{plan['mix_title'].replace(' ', '_')}_POC.mp3"
        print(f"\n💾 Saving mix to: {output_file}")
        
        final_mix.export(
            output_file,
            format="mp3",
            bitrate="192k",
            tags={
                'title': plan['mix_title'],
                'artist': 'No Agenda AI Mixer POC',
                'album': 'Episode 1779',
                'comment': plan['description']
            }
        )
        
        duration = len(final_mix) / 1000
        print(f"✅ Mix created! Duration: {duration:.1f} seconds")
        print(f"\n🎧 Ready to play: {output_file}")
        
        # Save the plan for reference
        plan_file = self.output_dir / f"{plan['mix_title'].replace(' ', '_')}_plan.json"
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2)
        print(f"📋 Mix plan saved: {plan_file}")
        
        return output_file

def main():
    """Run the simple mixer POC"""
    mixer = SimpleMixerPOC()
    
    try:
        output_file = mixer.create_simple_mix()
        
        if output_file and output_file.exists():
            print("\n🎉 SUCCESS! Your mix is ready!")
            print("\nTo play it:")
            print(f"   afplay {output_file}  # Mac")
            print(f"   mpg123 {output_file}  # Linux")
            print(f"   start {output_file}   # Windows")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
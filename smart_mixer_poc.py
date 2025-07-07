#!/usr/bin/env python3
"""
Smart Mixer POC: Fetches actual show info and creates targeted mixes
"""
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import openai
from pydub import AudioSegment
from bs4 import BeautifulSoup
import re

# Load environment
load_dotenv('config/.env')

# Initialize GROK client
client = openai.OpenAI(
    api_key=os.getenv('GROK_API_KEY'),
    base_url=os.getenv('GROK_API_URL', 'https://api.x.ai/v1')
)

class SmartMixerPOC:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.audio_dir = self.base_dir / 'audio'
        self.output_dir = self.base_dir / 'output'
        self.clips_dir = self.base_dir / 'clips'
        self.transcripts_dir = self.base_dir / 'transcripts'
        
        # Episode 1779 audio file
        self.episode_file = self.audio_dir / 'NA-1779-2025-07-06-Final.mp3'
        
    def fetch_show_info(self, episode=1779):
        """Fetch actual show information from No Agenda website"""
        print("🌐 Fetching show info from noagendashow.net...")
        
        url = f"https://www.noagendashow.net/listen/{episode}"
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract show title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else f"Episode {episode}"
            
            # Extract description or summary
            desc_elem = soup.find('meta', {'name': 'description'})
            description = desc_elem.get('content', '') if desc_elem else ''
            
            # Look for any transcript or segment info
            segments = []
            # Try to find any div with transcript-like content
            content_divs = soup.find_all(['div', 'section', 'article'])
            for div in content_divs[:10]:  # Limit to first 10 to avoid too much
                text = div.get_text(strip=True)
                if len(text) > 100 and len(text) < 1000:
                    segments.append(text[:200] + "...")
            
            show_info = {
                'title': title,
                'description': description,
                'segments_preview': segments[:3],
                'url': url
            }
            
            # Save to cache
            cache_file = self.transcripts_dir / f"episode_{episode}_info.json"
            with open(cache_file, 'w') as f:
                json.dump(show_info, f, indent=2)
            
            print(f"✅ Found: {title}")
            return show_info
            
        except Exception as e:
            print(f"⚠️ Could not fetch show info: {e}")
            # Return mock data
            return {
                'title': f'No Agenda Episode {episode}',
                'description': 'The Best Podcast in the Universe',
                'segments_preview': [
                    'Discussion about current events and media deconstruction',
                    'Analysis of news narratives and propaganda',
                    'Humor and insights from Adam Curry and John C. Dvorak'
                ]
            }
    
    def analyze_with_ai(self, show_info, theme=None):
        """Use GROK to create a smart mix plan based on actual show info"""
        print(f"\n🤖 Creating {theme or 'best-of'} mix with GROK...")
        
        context = f"""
        Show: {show_info['title']}
        Description: {show_info['description']}
        
        Content preview:
        {chr(10).join(show_info['segments_preview'])}
        """
        
        prompt = f"""Based on this No Agenda show information, create a creative mix plan.
        
        {context}
        
        Theme: {theme or "Best funny and memorable moments"}
        
        Create a JSON plan for a 90-second mix with:
        {{
          "mix_title": "Creative punny title",
          "tagline": "One-line description",
          "vibe": "overall feeling/genre",
          "segments": [
            {{
              "name": "Descriptive name",
              "timestamp": "HH:MM:SS",
              "duration": 5-20,
              "type": "intro|quote|joke|rant|transition|outro",
              "effect": "none|reverb|echo|pitch|speed",
              "description": "What happens in this segment"
            }}
          ],
          "transitions": "How segments flow together",
          "creative_notes": "Special effects or mixing ideas"
        }}
        
        Be creative! Think about:
        - Building energy throughout
        - Using recurring show elements (In the morning!, etc.)
        - Creating callbacks to earlier segments
        - Ending with impact
        
        Use varied timestamps throughout a 3-hour show.
        """
        
        response = client.chat.completions.create(
            model=os.getenv('GROK_MODEL', 'grok-3-latest'),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.85
        )
        
        return json.loads(response.choices[0].message.content)
    
    def create_smart_mix(self, theme=None):
        """Create a smart mix using real show information"""
        print("🎵 Smart Mixer POC - Creating Intelligent Mix\n")
        
        # Fetch actual show info
        show_info = self.fetch_show_info(1779)
        
        # Get AI mix plan
        mix_plan = self.analyze_with_ai(show_info, theme)
        
        print(f"\n🎨 Mix: {mix_plan['mix_title']}")
        print(f"💭 {mix_plan['tagline']}")
        print(f"🎸 Vibe: {mix_plan['vibe']}")
        print(f"📝 Notes: {mix_plan.get('creative_notes', 'Standard mix')}\n")
        
        # Load audio
        if not self.episode_file.exists():
            print("❌ Episode audio not found!")
            return None
            
        print("📂 Loading episode audio...")
        full_audio = AudioSegment.from_mp3(self.episode_file)
        
        # Process segments
        segments = []
        for i, seg in enumerate(mix_plan['segments']):
            print(f"🎯 Segment {i+1}/{len(mix_plan['segments'])}: {seg['name']}")
            print(f"   Type: {seg['type']} | Effect: {seg['effect']}")
            print(f"   {seg['description']}")
            
            try:
                # Convert timestamp
                ts = seg['timestamp']
                parts = ts.split(':')
                if len(parts) == 3:
                    start_ms = (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
                else:
                    start_ms = (int(parts[0]) * 60 + int(parts[1])) * 1000
                
                duration_ms = seg['duration'] * 1000
                
                # Extract segment
                clip = full_audio[start_ms:start_ms + duration_ms]
                
                # Apply effects
                if seg['effect'] == 'reverb':
                    # Simple reverb simulation
                    reverb = clip - 12
                    clip = clip.overlay(reverb, position=50)
                elif seg['effect'] == 'echo':
                    echo = clip - 10
                    clip = clip.overlay(echo, position=250)
                elif seg['effect'] == 'pitch':
                    # Pitch shift (simple speed change)
                    clip = clip._spawn(clip.raw_data, overrides={
                        "frame_rate": int(clip.frame_rate * 1.1)
                    }).set_frame_rate(clip.frame_rate)
                elif seg['effect'] == 'speed':
                    clip = clip._spawn(clip.raw_data, overrides={
                        "frame_rate": int(clip.frame_rate * 1.3)
                    }).set_frame_rate(clip.frame_rate)
                
                # Type-specific processing
                if seg['type'] == 'intro':
                    clip = clip.fade_in(1000)
                elif seg['type'] == 'outro':
                    clip = clip.fade_out(2000)
                elif seg['type'] == 'transition':
                    clip = clip.fade_in(500).fade_out(500)
                
                segments.append(clip)
                print("   ✅ Processed\n")
                
            except Exception as e:
                print(f"   ⚠️ Error: {e}, using random segment\n")
                # Fallback to random segment
                random_start = len(full_audio) // 2
                segments.append(full_audio[random_start:random_start + 10000])
        
        # Mix it all together
        print("🎛️ Creating final mix...")
        if not segments:
            print("❌ No segments to mix!")
            return None
            
        final_mix = segments[0]
        
        # Smart transitions based on plan
        transition_style = mix_plan.get('transitions', 'crossfade')
        for segment in segments[1:]:
            if 'smooth' in transition_style.lower():
                final_mix = final_mix.append(segment, crossfade=800)
            elif 'hard' in transition_style.lower():
                final_mix = final_mix + segment
            elif 'overlap' in transition_style.lower():
                final_mix = final_mix.overlay(segment, position=len(final_mix) - 500)
            else:
                final_mix = final_mix.append(segment, crossfade=500)
        
        # Save the mix
        filename = mix_plan['mix_title'].replace(' ', '_').replace(':', '')
        output_file = self.output_dir / f"{filename}_smart.mp3"
        
        print(f"💾 Saving: {output_file}")
        final_mix.export(
            output_file,
            format="mp3",
            bitrate="192k",
            tags={
                'title': mix_plan['mix_title'],
                'artist': 'No Agenda AI Smart Mixer',
                'album': show_info['title'],
                'comment': mix_plan['tagline']
            }
        )
        
        # Save the plan
        plan_file = self.output_dir / f"{filename}_smart_plan.json"
        with open(plan_file, 'w') as f:
            json.dump({
                'show_info': show_info,
                'mix_plan': mix_plan,
                'theme': theme
            }, f, indent=2)
        
        duration = len(final_mix) / 1000
        print(f"\n✅ Smart mix created! Duration: {duration:.1f} seconds")
        print(f"🎧 Play: afplay \"{output_file}\"")
        
        return output_file

def main():
    """Run smart mixer with different themes"""
    mixer = SmartMixerPOC()
    
    # Let user choose theme
    print("🎨 Smart No Agenda Mixer - Theme Selection\n")
    print("1. Best Of (default)")
    print("2. Conspiracy Corner")
    print("3. Media Meltdown")
    print("4. Donation Nation")
    print("5. Custom theme")
    
    choice = input("\nSelect theme (1-5) or press Enter for default: ").strip()
    
    theme_map = {
        '2': 'conspiracy theories and tin foil hat moments',
        '3': 'media criticism and M5M mockery',
        '4': 'donation segments and producer shoutouts',
        '5': input("Enter custom theme: ") if choice == '5' else None
    }
    
    theme = theme_map.get(choice)
    
    try:
        output = mixer.create_smart_mix(theme)
        if output:
            print("\n🎉 Success! Your smart mix is ready!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
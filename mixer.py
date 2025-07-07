#!/usr/bin/env python3
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment
from bs4 import BeautifulSoup
import openai
from typing import List, Dict, Tuple
import argparse
import re

class NoAgendaMixer:
    def __init__(self):
        load_dotenv('config/.env')
        self.grok_api_key = os.getenv('GROK_API_KEY')
        self.grok_api_url = os.getenv('GROK_API_URL', 'https://api.x.ai/v1')
        self.grok_model = os.getenv('GROK_MODEL', 'grok-beta')
        
        if not self.grok_api_key:
            raise ValueError("GROK_API_KEY not found in config/.env")
        
        self.client = openai.OpenAI(
            api_key=self.grok_api_key,
            base_url=self.grok_api_url
        )
        
        self.base_dir = Path(__file__).parent
        self.audio_dir = self.base_dir / 'audio'
        self.transcripts_dir = self.base_dir / 'transcripts'
        self.clips_dir = self.base_dir / 'clips'
        self.output_dir = self.base_dir / 'output'
        
        for dir in [self.audio_dir, self.transcripts_dir, self.clips_dir, self.output_dir]:
            dir.mkdir(exist_ok=True)
    
    def fetch_transcript(self, episode_number: int) -> Dict:
        """Fetch transcript from No Agenda show website"""
        url = f"https://www.noagendashow.net/listen/{episode_number}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract transcript data
        transcript_data = {
            'episode': episode_number,
            'segments': []
        }
        
        # Look for transcript sections
        transcript_sections = soup.find_all(['div', 'section'], class_=re.compile('transcript|segment'))
        
        for section in transcript_sections:
            text = section.get_text(strip=True)
            if text:
                transcript_data['segments'].append({
                    'text': text,
                    'timestamp': self._extract_timestamp(section)
                })
        
        # Save transcript
        transcript_file = self.transcripts_dir / f"episode_{episode_number}.json"
        with open(transcript_file, 'w') as f:
            json.dump(transcript_data, f, indent=2)
        
        return transcript_data
    
    def _extract_timestamp(self, element) -> str:
        """Extract timestamp from HTML element"""
        # Look for timestamp patterns
        timestamp_pattern = r'(\d{1,2}:\d{2}(?::\d{2})?)'
        text = str(element)
        match = re.search(timestamp_pattern, text)
        return match.group(1) if match else "00:00"
    
    def analyze_with_grok(self, transcript: Dict) -> List[Dict]:
        """Use GROK AI to identify funny/interesting segments"""
        segments_text = "\n\n".join([f"[{seg.get('timestamp', '00:00')}] {seg['text']}" 
                                     for seg in transcript['segments']])
        
        prompt = """Analyze this No Agenda show transcript and identify the funniest, most interesting, 
        or most memorable segments that would make great clips for an end-of-show mix. 
        
        Look for:
        - Funny jokes or observations
        - Memorable quotes
        - Musical moments or jingles
        - Running gags or callbacks
        - Particularly insightful commentary
        
        Return a JSON array of segments with:
        - timestamp: when it occurs
        - duration: suggested clip length in seconds (5-60)
        - description: what makes it interesting
        - type: "funny", "insightful", "musical", "quote", "callback"
        
        Transcript:
        """ + segments_text[:10000]  # Limit for API
        
        response = self.client.chat.completions.create(
            model=self.grok_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            return result.get('segments', [])
        except:
            return []
    
    def extract_clips(self, audio_file: Path, segments: List[Dict]) -> List[Path]:
        """Extract audio clips based on identified segments"""
        audio = AudioSegment.from_mp3(audio_file)
        extracted_clips = []
        
        for i, segment in enumerate(segments):
            timestamp = segment.get('timestamp', '00:00')
            duration = segment.get('duration', 10)
            
            # Convert timestamp to milliseconds
            parts = timestamp.split(':')
            if len(parts) == 2:
                start_ms = (int(parts[0]) * 60 + int(parts[1])) * 1000
            else:
                start_ms = (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
            
            end_ms = start_ms + (duration * 1000)
            
            # Extract clip
            clip = audio[start_ms:end_ms]
            
            # Save clip
            clip_file = self.clips_dir / f"clip_{i}_{segment.get('type', 'unknown')}.mp3"
            clip.export(clip_file, format="mp3")
            extracted_clips.append(clip_file)
        
        return extracted_clips
    
    def create_mix(self, clips: List[Path], episode_number: int) -> Path:
        """Create final audio mix from clips"""
        if not clips:
            raise ValueError("No clips to mix")
        
        # Start with first clip
        mix = AudioSegment.from_mp3(clips[0])
        
        # Add transitions between clips
        for clip_path in clips[1:]:
            clip = AudioSegment.from_mp3(clip_path)
            
            # Add 0.5 second crossfade
            mix = mix.append(clip, crossfade=500)
        
        # Save final mix
        output_file = self.output_dir / f"NA_{episode_number}_mix.mp3"
        mix.export(output_file, format="mp3", bitrate="192k")
        
        return output_file
    
    def process_episode(self, episode_number: int):
        """Main processing pipeline"""
        print(f"Processing No Agenda Episode {episode_number}")
        
        # Check if audio exists
        audio_files = list(self.audio_dir.glob(f"*{episode_number}*.mp3"))
        if not audio_files:
            print(f"Error: No audio file found for episode {episode_number}")
            return
        
        audio_file = audio_files[0]
        print(f"Using audio file: {audio_file}")
        
        # Fetch transcript
        print("Fetching transcript...")
        transcript = self.fetch_transcript(episode_number)
        
        if not transcript['segments']:
            print("Warning: No transcript segments found")
            return
        
        # Analyze with GROK
        print("Analyzing with GROK AI...")
        interesting_segments = self.analyze_with_grok(transcript)
        
        if not interesting_segments:
            print("No interesting segments identified")
            return
        
        print(f"Found {len(interesting_segments)} interesting segments")
        
        # Extract clips
        print("Extracting audio clips...")
        clips = self.extract_clips(audio_file, interesting_segments)
        
        # Create mix
        print("Creating final mix...")
        output_file = self.create_mix(clips, episode_number)
        
        print(f"Mix created: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Create No Agenda show mixes')
    parser.add_argument('--episode', type=int, default=1779, help='Episode number')
    args = parser.parse_args()
    
    mixer = NoAgendaMixer()
    mixer.process_episode(args.episode)

if __name__ == "__main__":
    main()
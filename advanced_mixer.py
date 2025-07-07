#!/usr/bin/env python3
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment
import openai
from typing import List, Dict, Tuple
import argparse
from mixer import NoAgendaMixer
from clip_searcher import ClipGenieSearcher
from show_data_fetcher import ShowDataFetcher

class AdvancedNoAgendaMixer(NoAgendaMixer):
    def __init__(self):
        super().__init__()
        self.clip_searcher = ClipGenieSearcher()
        self.show_fetcher = ShowDataFetcher()
    
    def create_creative_mix(self, episode_number: int, theme: str = None):
        """Create a themed creative mix using AI suggestions"""
        print(f"Creating creative mix for episode {episode_number}")
        if theme:
            print(f"Theme: {theme}")
        
        # Get episode data
        episode_data = self.show_fetcher.fetch_episode_data(episode_number)
        
        # Get transcript
        transcript = self.fetch_transcript(episode_number)
        
        # Get AI suggestions for creative mix
        mix_plan = self._get_creative_mix_plan(transcript, episode_data, theme)
        
        # Collect clips based on plan
        clips = self._collect_clips_for_mix(mix_plan, episode_number)
        
        # Create the mix with creative transitions
        output_file = self._create_creative_mix(clips, mix_plan, episode_number, theme)
        
        print(f"Creative mix created: {output_file}")
        return output_file
    
    def _get_creative_mix_plan(self, transcript: Dict, episode_data: Dict, theme: str = None) -> Dict:
        """Use GROK to create a creative mix plan"""
        context = f"""
        Episode transcript segments: {len(transcript.get('segments', []))}
        Available clips: {len(episode_data.get('clips', []))}
        Theme: {theme or 'Best of show - funny and memorable moments'}
        
        Transcript preview:
        {json.dumps(transcript.get('segments', [])[:5], indent=2)}
        
        Available clips:
        {json.dumps([c['title'] for c in episode_data.get('clips', [])][:10], indent=2)}
        """
        
        prompt = f"""Create a creative audio mix plan for No Agenda show. 
        
        Context:
        {context}
        
        Create a JSON plan with:
        - title: Creative title for the mix
        - description: What makes this mix special
        - segments: Array of segments to include
          - source: "transcript" or "clip" or "search"
          - query: Search query if source is "search"
          - timestamp: For transcript sources
          - clip_name: For clip sources
          - duration: Seconds (5-60)
          - transition: Type of transition to next segment
          - effect: Optional audio effect (reverb, echo, pitch, etc.)
        - total_duration: Target duration in seconds (120-300)
        
        Be creative! Think about:
        - Building a narrative arc
        - Using callbacks and running gags
        - Creating rhythm with pacing
        - Surprising juxtapositions
        - Musical elements and jingles
        """
        
        response = self.client.chat.completions.create(
            model=self.grok_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            # Fallback plan
            return {
                "title": "No Agenda Mix",
                "description": "AI-curated highlights",
                "segments": [],
                "total_duration": 180
            }
    
    def _collect_clips_for_mix(self, mix_plan: Dict, episode_number: int) -> List[Tuple[Path, Dict]]:
        """Collect all clips needed for the mix"""
        clips = []
        
        for segment in mix_plan.get('segments', []):
            source = segment.get('source')
            
            if source == 'transcript':
                # Extract from main audio
                audio_file = list(self.audio_dir.glob(f"*{episode_number}*.mp3"))[0]
                clip_path = self._extract_single_clip(audio_file, segment)
                clips.append((clip_path, segment))
            
            elif source == 'clip':
                # Use existing clip
                clip_name = segment.get('clip_name')
                # Download if needed
                clip_url = self._find_clip_url(clip_name, episode_number)
                if clip_url:
                    clip_path = self.show_fetcher.download_clip(clip_url, self.clips_dir)
                    clips.append((clip_path, segment))
            
            elif source == 'search':
                # Search for related clips
                query = segment.get('query', '')
                search_results = self.clip_searcher.search_clips(query, limit=1)
                if search_results:
                    # Download first result
                    clip_url = search_results[0].get('url')
                    if clip_url:
                        clip_path = self.show_fetcher.download_clip(clip_url, self.clips_dir)
                        clips.append((clip_path, segment))
        
        return clips
    
    def _extract_single_clip(self, audio_file: Path, segment: Dict) -> Path:
        """Extract a single clip from audio file"""
        audio = AudioSegment.from_mp3(audio_file)
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
        
        # Apply effects if specified
        effect = segment.get('effect')
        if effect == 'reverb':
            # Simple reverb effect (would need more sophisticated implementation)
            clip = clip + clip.fade_out(1000).fade_in(1000) - 10
        elif effect == 'echo':
            clip = clip.overlay(clip - 10, position=200)
        elif effect == 'pitch':
            # Pitch shift would require librosa or similar
            pass
        
        # Save clip
        clip_file = self.clips_dir / f"extract_{start_ms}_{effect or 'clean'}.mp3"
        clip.export(clip_file, format="mp3")
        
        return clip_file
    
    def _create_creative_mix(self, clips: List[Tuple[Path, Dict]], mix_plan: Dict, 
                           episode_number: int, theme: str = None) -> Path:
        """Create final mix with creative transitions"""
        if not clips:
            raise ValueError("No clips to mix")
        
        # Start with first clip
        mix = AudioSegment.from_mp3(clips[0][0])
        
        for i, (clip_path, segment) in enumerate(clips[1:], 1):
            clip = AudioSegment.from_mp3(clip_path)
            transition = segment.get('transition', 'crossfade')
            
            if transition == 'crossfade':
                mix = mix.append(clip, crossfade=500)
            elif transition == 'hard_cut':
                mix = mix + clip
            elif transition == 'fade':
                mix = mix.fade_out(500) + clip.fade_in(500)
            elif transition == 'overlap':
                # Overlap last second
                mix = mix.overlay(clip, position=len(mix) - 1000)
            else:
                mix = mix.append(clip, crossfade=300)
        
        # Add intro/outro if specified
        title = mix_plan.get('title', f'NA {episode_number} Mix')
        
        # Save final mix
        theme_suffix = f"_{theme.replace(' ', '_')}" if theme else ""
        output_file = self.output_dir / f"NA_{episode_number}_creative{theme_suffix}.mp3"
        
        # Export with metadata
        mix.export(
            output_file, 
            format="mp3", 
            bitrate="192k",
            tags={
                'title': title,
                'artist': 'No Agenda AI Mixer',
                'album': f'No Agenda Episode {episode_number}',
                'comment': mix_plan.get('description', '')
            }
        )
        
        return output_file
    
    def _find_clip_url(self, clip_name: str, episode_number: int) -> str:
        """Find URL for a named clip"""
        episode_data = self.show_fetcher.fetch_episode_data(episode_number)
        for clip in episode_data.get('clips', []):
            if clip_name.lower() in clip['title'].lower():
                return clip['url']
        return None

def main():
    parser = argparse.ArgumentParser(description='Create advanced No Agenda show mixes')
    parser.add_argument('--episode', type=int, default=1779, help='Episode number')
    parser.add_argument('--theme', type=str, help='Theme for the mix (e.g., "conspiracy theories", "funny moments")')
    parser.add_argument('--mode', choices=['basic', 'creative'], default='creative', help='Mix mode')
    args = parser.parse_args()
    
    if args.mode == 'basic':
        mixer = NoAgendaMixer()
        mixer.process_episode(args.episode)
    else:
        mixer = AdvancedNoAgendaMixer()
        mixer.create_creative_mix(args.episode, args.theme)

if __name__ == "__main__":
    main()
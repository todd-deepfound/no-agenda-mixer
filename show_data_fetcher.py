#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
from typing import Dict, List

class ShowDataFetcher:
    def __init__(self):
        self.base_url = "http://adam.curry.com/html"
        self.cache_dir = Path(__file__).parent / 'transcripts'
        self.cache_dir.mkdir(exist_ok=True)
    
    def fetch_episode_data(self, episode_number: int) -> Dict:
        """Fetch complete episode data including clips, docs, and art"""
        # Find the episode page
        episode_url = self._find_episode_url(episode_number)
        if not episode_url:
            print(f"Episode {episode_number} not found")
            return {}
        
        response = requests.get(episode_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        episode_data = {
            'episode': episode_number,
            'url': episode_url,
            'clips': [],
            'documents': [],
            'art': [],
            'shownotes': ''
        }
        
        # Extract clips
        clips_section = soup.find('div', id='tabclips-and-docs')
        if clips_section:
            clips = clips_section.find_all('a', href=re.compile(r'\.(mp3|m4a|wav)'))
            for clip in clips:
                episode_data['clips'].append({
                    'title': clip.get_text(strip=True),
                    'url': clip['href']
                })
        
        # Extract documents
        docs = soup.find_all('a', href=re.compile(r'\.(pdf|doc|txt)'))
        for doc in docs:
            episode_data['documents'].append({
                'title': doc.get_text(strip=True),
                'url': doc['href']
            })
        
        # Extract art
        art_section = soup.find('div', class_='art-section')
        if art_section:
            images = art_section.find_all('img')
            for img in images:
                episode_data['art'].append({
                    'alt': img.get('alt', ''),
                    'url': img['src']
                })
        
        # Extract shownotes
        shownotes_section = soup.find('div', class_='shownotes')
        if shownotes_section:
            episode_data['shownotes'] = shownotes_section.get_text(strip=True)
        
        # Cache the data
        cache_file = self.cache_dir / f"episode_{episode_number}_data.json"
        with open(cache_file, 'w') as f:
            json.dump(episode_data, f, indent=2)
        
        return episode_data
    
    def _find_episode_url(self, episode_number: int) -> str:
        """Find the URL for a specific episode"""
        # Pattern for No Agenda episode URLs
        search_url = f"{self.base_url}/NoAgendaEpisode{episode_number}"
        
        # Try direct URL first
        response = requests.head(search_url + ".html", allow_redirects=True)
        if response.status_code == 200:
            return response.url
        
        # Search for variations
        patterns = [
            f"NoAgendaEpisode{episode_number}-*.html",
            f"NoAgendaEpisode{episode_number}*.html"
        ]
        
        # Would need to implement directory listing or use a known index
        # For now, construct based on known pattern
        return f"{self.base_url}/NoAgendaEpisode{episode_number}-placeholder.html"
    
    def get_episode_clips(self, episode_number: int) -> List[Dict]:
        """Get just the clips for an episode"""
        data = self.fetch_episode_data(episode_number)
        return data.get('clips', [])
    
    def download_clip(self, clip_url: str, output_dir: Path) -> Path:
        """Download a clip from the show notes"""
        filename = clip_url.split('/')[-1]
        output_path = output_dir / filename
        
        if not output_path.exists():
            response = requests.get(clip_url, stream=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        return output_path

if __name__ == "__main__":
    import sys
    episode = int(sys.argv[1]) if len(sys.argv) > 1 else 1779
    
    fetcher = ShowDataFetcher()
    data = fetcher.fetch_episode_data(episode)
    
    print(f"Episode {episode} data:")
    print(f"- Clips: {len(data.get('clips', []))}")
    print(f"- Documents: {len(data.get('documents', []))}")
    print(f"- Art: {len(data.get('art', []))}")
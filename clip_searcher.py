#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict

class ClipGenieSearcher:
    def __init__(self):
        self.base_url = "https://noagenda.clipgenie.com"
        self.session = requests.Session()
    
    def search_clips(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for clips on ClipGenie"""
        search_url = f"{self.base_url}/search"
        params = {
            'q': query,
            'limit': limit
        }
        
        try:
            response = self.session.get(search_url, params=params)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            clips = []
            # Parse search results
            clip_elements = soup.find_all(['div', 'article'], class_=re.compile('clip|result'))
            
            for clip_elem in clip_elements[:limit]:
                clip_data = self._parse_clip_element(clip_elem)
                if clip_data:
                    clips.append(clip_data)
            
            return clips
        except Exception as e:
            print(f"Error searching clips: {e}")
            return []
    
    def _parse_clip_element(self, element) -> Dict:
        """Parse individual clip element"""
        clip = {}
        
        # Extract title
        title_elem = element.find(['h2', 'h3', 'a'], class_=re.compile('title|name'))
        if title_elem:
            clip['title'] = title_elem.get_text(strip=True)
        
        # Extract URL
        link_elem = element.find('a', href=True)
        if link_elem:
            clip['url'] = link_elem['href']
            if not clip['url'].startswith('http'):
                clip['url'] = self.base_url + clip['url']
        
        # Extract episode info
        episode_elem = element.find(text=re.compile(r'Episode \d+'))
        if episode_elem:
            clip['episode'] = episode_elem.strip()
        
        # Extract duration
        duration_elem = element.find(text=re.compile(r'\d+:\d+'))
        if duration_elem:
            clip['duration'] = duration_elem.strip()
        
        return clip if 'title' in clip else None
    
    def get_popular_clips(self, episode: int = None) -> List[Dict]:
        """Get popular clips, optionally filtered by episode"""
        url = f"{self.base_url}/popular"
        if episode:
            url += f"?episode={episode}"
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            clips = []
            # Similar parsing logic as search_clips
            return clips
        except Exception as e:
            print(f"Error fetching popular clips: {e}")
            return []

def find_related_clips(topic: str, episode: int = None) -> List[Dict]:
    """Find clips related to a topic"""
    searcher = ClipGenieSearcher()
    
    # Search for topic
    clips = searcher.search_clips(topic)
    
    # If episode specified, filter or search within episode
    if episode:
        episode_clips = [c for c in clips if str(episode) in c.get('episode', '')]
        if not episode_clips:
            # Try episode-specific search
            clips = searcher.search_clips(f"{topic} episode {episode}")
    
    return clips

if __name__ == "__main__":
    # Example usage
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "funny"
    clips = find_related_clips(query)
    
    print(f"Found {len(clips)} clips for '{query}':")
    for clip in clips:
        print(f"- {clip.get('title', 'Unknown')} ({clip.get('duration', 'N/A')})")
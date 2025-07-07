#!/usr/bin/env python3
"""
No Agenda Mixer Web App - Flask Application for AWS Lambda
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
import uuid
import traceback

from flask import Flask, render_template, request, jsonify, send_file, url_for
from flask_cors import CORS
from dotenv import load_dotenv
import boto3
import openai
import requests
from bs4 import BeautifulSoup
import fal_client
from pythonjsonlogger import jsonlogger
from secrets_manager import load_secrets_to_env

# Configure structured logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Load environment
load_dotenv()

# Load secrets from AWS Secrets Manager if in Lambda
load_secrets_to_env()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/outputs'
app.config['LOGS_FOLDER'] = 'logs'
app.config['DATA_FOLDER'] = 'data'

# S3 bucket for persistent storage
S3_BUCKET = os.getenv('S3_BUCKET', 'no-agenda-mixer')
s3_client = boto3.client('s3') if os.getenv('AWS_REGION') else None

# Initialize AI clients
grok_client = openai.OpenAI(
    api_key=os.getenv('GROK_API_KEY'),
    base_url=os.getenv('GROK_API_URL', 'https://api.x.ai/v1')
)

# Fal.ai configuration
fal_client.api_key = os.getenv('FAL_API_KEY')

# Create necessary directories
for folder in ['logs', 'data', 'static/audio']:
    os.makedirs(folder, exist_ok=True)

class MixSession:
    """Track all data for a mix creation session"""
    def __init__(self, session_id=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.utcnow().isoformat()
        self.episode_number = None
        self.theme = None
        self.ideas = []
        self.clips = []
        self.music_generations = []
        self.mix_plans = []
        self.final_mixes = []
        self.logs = []
        self.metadata = {}
    
    def log(self, level, message, data=None):
        """Add to session log"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'data': data or {}
        }
        self.logs.append(log_entry)
        logger.log(getattr(logging, level.upper()), message, extra={
            'session_id': self.session_id,
            **log_entry
        })
    
    def add_idea(self, idea_type, content, metadata=None):
        """Add a creative idea"""
        idea = {
            'id': str(uuid.uuid4()),
            'type': idea_type,
            'content': content,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat()
        }
        self.ideas.append(idea)
        self.log('info', f'Added {idea_type} idea', idea)
        return idea
    
    def add_clip(self, clip_data):
        """Add a clip reference"""
        clip = {
            'id': str(uuid.uuid4()),
            'created_at': datetime.utcnow().isoformat(),
            **clip_data
        }
        self.clips.append(clip)
        self.log('info', f'Added clip: {clip.get("name", "Unnamed")}', clip)
        return clip
    
    def add_music_generation(self, prompt, result):
        """Add AI-generated music"""
        music = {
            'id': str(uuid.uuid4()),
            'prompt': prompt,
            'result': result,
            'created_at': datetime.utcnow().isoformat()
        }
        self.music_generations.append(music)
        self.log('info', 'Generated AI music', music)
        return music
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at,
            'episode_number': self.episode_number,
            'theme': self.theme,
            'ideas': self.ideas,
            'clips': self.clips,
            'music_generations': self.music_generations,
            'mix_plans': self.mix_plans,
            'final_mixes': self.final_mixes,
            'logs': self.logs,
            'metadata': self.metadata
        }
    
    def save(self):
        """Save session data"""
        filename = f"session_{self.session_id}.json"
        filepath = Path(app.config['DATA_FOLDER']) / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        # Also save to S3 if available
        if s3_client:
            try:
                s3_client.put_object(
                    Bucket=S3_BUCKET,
                    Key=f"sessions/{filename}",
                    Body=json.dumps(self.to_dict()),
                    ContentType='application/json'
                )
            except Exception as e:
                logger.error(f"Failed to save to S3: {e}")

# Session storage
sessions = {}

def get_session(session_id=None):
    """Get or create session"""
    if session_id and session_id in sessions:
        return sessions[session_id]
    
    session = MixSession(session_id)
    sessions[session.session_id] = session
    return session

@app.route('/')
def index():
    """Main interface"""
    return render_template('index.html')

@app.route('/api/start_session', methods=['POST'])
def start_session():
    """Start a new mix session"""
    data = request.json
    session = get_session()
    
    session.episode_number = data.get('episode_number', 1779)
    session.theme = data.get('theme', 'Best Of')
    session.metadata = {
        'user_agent': request.headers.get('User-Agent'),
        'ip': request.remote_addr
    }
    
    session.log('info', 'Session started', {
        'episode': session.episode_number,
        'theme': session.theme
    })
    
    return jsonify({
        'session_id': session.session_id,
        'status': 'started'
    })

@app.route('/api/generate_ideas/<session_id>', methods=['POST'])
def generate_ideas(session_id):
    """Generate mix ideas using GROK"""
    session = get_session(session_id)
    data = request.json
    
    try:
        # Fetch episode info
        episode_info = fetch_episode_info(session.episode_number)
        session.metadata['episode_info'] = episode_info
        
        # Generate various types of ideas
        idea_types = [
            {
                'type': 'mix_concept',
                'prompt': f"""Create 3 creative mix concepts for No Agenda Episode {session.episode_number}.
                Theme: {session.theme}
                Episode info: {json.dumps(episode_info, indent=2)}
                
                For each concept include:
                - Title
                - Concept description
                - Key audio elements
                - Musical style/genre
                - Target duration
                """
            },
            {
                'type': 'segment_ideas',
                'prompt': f"""Suggest 10 specific segments from Episode {session.episode_number} that would work well in a mix.
                
                For each segment:
                - Descriptive name
                - Why it's interesting
                - Estimated timestamp (spread throughout 3 hours)
                - Suggested audio effect
                - How to transition to/from it
                """
            },
            {
                'type': 'music_prompts',
                'prompt': f"""Create 5 AI music generation prompts that would complement No Agenda Episode {session.episode_number}.
                Theme: {session.theme}
                
                Each prompt should:
                - Be specific about style, tempo, mood
                - Incorporate show elements (catchphrases, themes)
                - Be 1-2 sentences
                - Work as transitions or background music
                """
            }
        ]
        
        for idea_request in idea_types:
            session.log('info', f'Generating {idea_request["type"]} ideas')
            
            response = grok_client.chat.completions.create(
                model=os.getenv('GROK_MODEL', 'grok-3-latest'),
                messages=[{"role": "user", "content": idea_request['prompt']}],
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            session.add_idea(idea_request['type'], content, {
                'prompt': idea_request['prompt'],
                'model': response.model
            })
        
        session.save()
        
        return jsonify({
            'status': 'success',
            'ideas_count': len(session.ideas),
            'session': session.to_dict()
        })
        
    except Exception as e:
        session.log('error', f'Failed to generate ideas: {str(e)}', {
            'traceback': traceback.format_exc()
        })
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_music/<session_id>', methods=['POST'])
def generate_music(session_id):
    """Generate AI music using Fal.ai"""
    session = get_session(session_id)
    data = request.json
    
    prompt = data.get('prompt', 'upbeat electronic music with podcast vibes')
    duration = data.get('duration', 30)
    
    try:
        session.log('info', f'Generating music: {prompt}')
        
        # Call Fal.ai music generator
        result = fal_client.run(
            "cassetteai/music-generator",
            arguments={
                "prompt": prompt,
                "duration": duration,
                "model": "large"
            }
        )
        
        # Save the generated music
        if result and 'audio_url' in result:
            music_data = session.add_music_generation(prompt, result)
            
            # Download and save locally
            audio_response = requests.get(result['audio_url'])
            filename = f"music_{music_data['id']}.mp3"
            filepath = Path('static/audio') / filename
            
            with open(filepath, 'wb') as f:
                f.write(audio_response.content)
            
            music_data['local_path'] = str(filepath)
            session.save()
            
            return jsonify({
                'status': 'success',
                'music': music_data,
                'url': url_for('static', filename=f'audio/{filename}')
            })
        else:
            raise Exception("No audio URL in response")
            
    except Exception as e:
        session.log('error', f'Failed to generate music: {str(e)}', {
            'traceback': traceback.format_exc()
        })
        return jsonify({'error': str(e)}), 500

@app.route('/api/create_mix_plan/<session_id>', methods=['POST'])
def create_mix_plan(session_id):
    """Create a detailed mix plan"""
    session = get_session(session_id)
    data = request.json
    
    try:
        # Compile all session data for context
        context = {
            'episode': session.episode_number,
            'theme': session.theme,
            'ideas': [idea['content'] for idea in session.ideas],
            'music_prompts': [m['prompt'] for m in session.music_generations],
            'selected_segments': data.get('selected_segments', [])
        }
        
        prompt = f"""Create a detailed mix plan based on this session data:
        {json.dumps(context, indent=2)}
        
        Return a JSON mix plan with:
        {{
          "title": "Creative mix title",
          "description": "What makes this mix special",
          "duration": 120,
          "segments": [
            {{
              "order": 1,
              "type": "show_clip|ai_music|transition",
              "source": "episode|generated|library",
              "timestamp": "HH:MM:SS",
              "duration": 10,
              "content": "Description",
              "effects": ["reverb", "fade"],
              "transition_to_next": "crossfade|cut|overlap"
            }}
          ],
          "production_notes": "Technical notes for mixing",
          "creative_vision": "Overall artistic vision"
        }}
        
        Be specific about timing and transitions. Include both show clips and AI music.
        """
        
        response = grok_client.chat.completions.create(
            model=os.getenv('GROK_MODEL', 'grok-3-latest'),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        mix_plan = json.loads(response.choices[0].message.content)
        mix_plan['id'] = str(uuid.uuid4())
        mix_plan['created_at'] = datetime.utcnow().isoformat()
        
        session.mix_plans.append(mix_plan)
        session.log('info', 'Created mix plan', mix_plan)
        session.save()
        
        return jsonify({
            'status': 'success',
            'mix_plan': mix_plan
        })
        
    except Exception as e:
        session.log('error', f'Failed to create mix plan: {str(e)}', {
            'traceback': traceback.format_exc()
        })
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>')
def get_session_data(session_id):
    """Get complete session data"""
    session = get_session(session_id)
    return jsonify(session.to_dict())

@app.route('/sessions')
def list_sessions():
    """List all sessions"""
    session_files = Path(app.config['DATA_FOLDER']).glob('session_*.json')
    sessions_list = []
    
    for file in sorted(session_files, key=lambda x: x.stat().st_mtime, reverse=True):
        with open(file) as f:
            data = json.load(f)
            sessions_list.append({
                'session_id': data['session_id'],
                'created_at': data['created_at'],
                'episode': data.get('episode_number'),
                'theme': data.get('theme'),
                'ideas_count': len(data.get('ideas', [])),
                'clips_count': len(data.get('clips', [])),
                'music_count': len(data.get('music_generations', []))
            })
    
    return render_template('sessions.html', sessions=sessions_list)

@app.route('/session/<session_id>')
def view_session(session_id):
    """View detailed session data"""
    session = get_session(session_id)
    return render_template('session_detail.html', session=session.to_dict())

def fetch_episode_info(episode_number):
    """Fetch episode information"""
    try:
        url = f"https://www.noagendashow.net/listen/{episode_number}"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else f"Episode {episode_number}"
        
        return {
            'episode': episode_number,
            'title': title_text,
            'url': url,
            'fetched_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to fetch episode info: {e}")
        return {
            'episode': episode_number,
            'title': f'Episode {episode_number}',
            'error': str(e)
        }

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

# For local development
if __name__ == '__main__':
    app.run(debug=True, port=5000)
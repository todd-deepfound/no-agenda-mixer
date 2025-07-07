#!/usr/bin/env python3
"""
No Agenda Mixer Web App - Minimal Working Version
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Try to load secrets if in Lambda
if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
    try:
        from secrets_manager import load_secrets_to_env
        load_secrets_to_env()
    except Exception as e:
        logger.error(f"Failed to load secrets: {e}")

app = Flask(__name__)
CORS(app)

# In-memory session storage
sessions = {}

@app.route('/')
def index():
    """API root"""
    return jsonify({
        'message': 'No Agenda Mixer API',
        'version': '1.0',
        'endpoints': {
            'GET /': 'This endpoint',
            'POST /api/start_session': 'Start a new mix session',
            'POST /api/generate_ideas/<session_id>': 'Generate mix ideas',
            'GET /api/session/<session_id>': 'Get session data',
            'GET /health': 'Health check'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'has_grok_key': bool(os.getenv('GROK_API_KEY')),
        'has_fal_key': bool(os.getenv('FAL_API_KEY'))
    })

@app.route('/api/start_session', methods=['POST'])
def start_session():
    """Start a new mix session"""
    try:
        data = request.get_json() or {}
        
        session_id = str(uuid.uuid4())
        session = {
            'session_id': session_id,
            'created_at': datetime.utcnow().isoformat(),
            'episode_number': data.get('episode_number', 1779),
            'theme': data.get('theme', 'Best Of'),
            'ideas': [],
            'status': 'started'
        }
        
        sessions[session_id] = session
        
        logger.info(f"Created session: {session_id}")
        
        return jsonify({
            'session_id': session_id,
            'status': 'started',
            'episode': session['episode_number'],
            'theme': session['theme']
        })
        
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>')
def get_session(session_id):
    """Get session data"""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify(sessions[session_id])

@app.route('/api/generate_ideas/<session_id>', methods=['POST'])
def generate_ideas(session_id):
    """Generate mix ideas"""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        # For now, return mock ideas
        mock_ideas = [
            {
                'type': 'mix_concept',
                'content': 'Best of Episode 1779: A high-energy compilation of the funniest moments',
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'type': 'segment_ideas',
                'content': '1. Opening "In the morning!" montage\n2. Conspiracy theory supercut\n3. Media criticism highlights',
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        
        sessions[session_id]['ideas'].extend(mock_ideas)
        
        return jsonify({
            'status': 'success',
            'ideas_count': len(mock_ideas),
            'session': sessions[session_id]
        })
        
    except Exception as e:
        logger.error(f"Error generating ideas: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
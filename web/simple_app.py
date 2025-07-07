import json
import os
from datetime import datetime
import uuid

# Global session storage (in a real app, use DynamoDB or S3)
sessions = {}

def get_music_prompt_for_theme(theme):
    """Generate music prompts based on theme"""
    prompts = {
        'Best Of': 'Upbeat electronic podcast intro music with energetic synth melody, 128 BPM, perfect for highlighting the best moments',
        'Conspiracy Corner': 'Dark ambient electronic music with mysterious undertones, glitch effects, and conspiracy theory vibes, 100 BPM',
        'Media Meltdown': 'Chaotic breakbeat electronic music with news broadcast samples, media criticism energy, and distortion effects, 140 BPM',
        'Donation Nation': 'Celebratory fanfare music with cash register sounds, applause, and triumphant horn sections, 120 BPM',
        'Musical Mayhem': 'Experimental electronic collage with vocal chops, random beats, and unpredictable sound design, 130 BPM',
        'Custom': 'Creative podcast background music with modern electronic elements, suitable for audio mixing, 125 BPM'
    }
    
    return prompts.get(theme, prompts['Custom'])

def generate_music_with_fal(prompt):
    """Generate music using FAL.ai API"""
    try:
        # Get FAL API key from environment (loaded from secrets)
        fal_key = os.getenv('FAL_API_KEY')
        if not fal_key:
            print("FAL_API_KEY not available")
            raise Exception("FAL_API_KEY not configured")
        
        import requests
        
        print(f"Generating music with FAL.ai: {prompt}")
        
        # FAL.ai API call using the correct endpoint
        headers = {
            'Authorization': f'Key {fal_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'prompt': prompt,
            'duration': 30
        }
        
        # Use the correct FAL.ai endpoint for music generation
        response = requests.post(
            'https://fal.run/fal-ai/stable-audio',
            headers=headers,
            json=payload,
            timeout=120  # Increased timeout for music generation
        )
        
        print(f"FAL.ai response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"FAL.ai success: {result}")
            
            return {
                'id': str(uuid.uuid4()),
                'prompt': prompt,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'completed',
                'audio_url': result.get('audio_url') or result.get('audio', {}).get('url'),
                'duration': 30,
                'fal_response': result
            }
        else:
            error_text = response.text
            print(f"FAL.ai API error: {response.status_code} - {error_text}")
            raise Exception(f"FAL.ai API error: {response.status_code} - {error_text}")
            
    except Exception as e:
        print(f"Error calling FAL.ai: {e}")
        raise e

def generate_ideas_with_grok(episode_number, theme):
    """Generate mix ideas using GROK AI"""
    try:
        # Get GROK API key from environment (loaded from secrets)
        grok_key = os.getenv('GROK_API_KEY')
        if not grok_key:
            print("GROK_API_KEY not available")
            raise Exception("GROK_API_KEY not configured")
        
        import requests
        
        print(f"Generating ideas with GROK for Episode {episode_number}, Theme: {theme}")
        
        # GROK AI API call
        headers = {
            'Authorization': f'Bearer {grok_key}',
            'Content-Type': 'application/json'
        }
        
        prompt = f"""Create creative mix ideas for No Agenda Episode {episode_number} with theme "{theme}".
        
        Generate 3 types of ideas:
        1. Mix Concept: Overall creative vision for the mix
        2. Segment Ideas: 5-6 specific segments with timestamps (spread throughout 3-hour show)
        3. Music Prompts: 3 AI music prompts that would complement this theme
        
        Be specific, creative, and capture the No Agenda podcast vibe. Include timestamps like 1:22:30 format.
        
        Return as JSON:
        {{
            "mix_concept": "...",
            "segments": [
                {{"name": "...", "timestamp": "HH:MM:SS", "duration": 15, "description": "..."}},
                ...
            ],
            "music_prompts": ["...", "...", "..."]
        }}
        """
        
        payload = {
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'model': os.getenv('GROK_MODEL', 'grok-3-latest'),
            'response_format': {'type': 'json_object'},
            'temperature': 0.8
        }
        
        response = requests.post(
            f"{os.getenv('GROK_API_URL', 'https://api.x.ai/v1')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"GROK response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            ideas = json.loads(content)
            
            print(f"GROK success: Generated ideas")
            
            return {
                'id': str(uuid.uuid4()),
                'episode_number': episode_number,
                'theme': theme,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'completed',
                'ideas': ideas,
                'grok_response': result
            }
        else:
            error_text = response.text
            print(f"GROK API error: {response.status_code} - {error_text}")
            raise Exception(f"GROK API error: {response.status_code} - {error_text}")
            
    except Exception as e:
        print(f"Error calling GROK: {e}")
        raise e

def load_secrets():
    """Load secrets from AWS Secrets Manager"""
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        try:
            import boto3
            secrets_client = boto3.client('secretsmanager')
            
            secret_response = secrets_client.get_secret_value(
                SecretId='no-agenda-mixer/api-keys'
            )
            
            secrets = json.loads(secret_response['SecretString'])
            
            # Set environment variables
            for key, value in secrets.items():
                os.environ[key] = value
                print(f"Loaded secret: {key}")
                
        except Exception as e:
            print(f"Failed to load secrets: {e}")

def lambda_handler(event, context):
    """Simple Lambda handler for testing"""
    
    try:
        # Load secrets from AWS Secrets Manager
        load_secrets()
        
        # Log the event
        print(f"Event: {json.dumps(event)}")
        
        # Handle CORS preflight requests
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': ''
            }
        
        # Simple routing
        path = event.get('path', '/')
        method = event.get('httpMethod', 'GET')
        
        if path == '/' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'No Agenda Mixer API is running!',
                    'version': '1.0',
                    'endpoints': [
                        'GET /',
                        'GET /health',
                        'POST /api/start_session',
                        'POST /api/generate_ideas/{session_id}',
                        'GET /api/session/{session_id}'
                    ]
                })
            }
    
        elif path == '/health' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'healthy',
                    'timestamp': '2025-07-06T20:00:00Z',
                    'has_grok_key': bool(os.getenv('GROK_API_KEY')),
                    'has_fal_key': bool(os.getenv('FAL_API_KEY'))
                })
            }
    
        elif path == '/api/start_session' and method == 'POST':
        # Parse body
        try:
            body = json.loads(event.get('body', '{}'))
        except:
            body = {}
        
        session_id = str(uuid.uuid4())
        
        # Create session object
        session = {
            'session_id': session_id,
            'created_at': datetime.utcnow().isoformat(),
            'episode_number': body.get('episode_number', 1779),
            'theme': body.get('theme', 'Best Of'),
            'status': 'started',
            'ideas': [],
            'music_generations': [],
            'clips': [],
            'logs': []
        }
        
        # Store session
        sessions[session_id] = session
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'session_id': session_id,
                'status': 'started',
                'episode': session['episode_number'],
                'theme': session['theme']
            })
        }
    
        elif path.startswith('/api/session/') and method == 'GET':
        # Extract session ID from path
        session_id = path.split('/')[-1]
        
        if session_id in sessions:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(sessions[session_id])
            }
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Session not found'})
            }
    
        elif path.startswith('/api/generate_music/') and method == 'POST':
        # Extract session ID from path
        session_id = path.split('/')[-1]
        
        try:
            body = json.loads(event.get('body', '{}'))
        except:
            body = {}
        
        # For testing, use default values if session not found
        if session_id not in sessions:
            theme = "Media Meltdown"
            print(f"Session {session_id} not found, using default theme: {theme}")
        else:
            theme = sessions[session_id]['theme']
        
        prompt = body.get('prompt') or get_music_prompt_for_theme(theme)
        
        # Generate real music with FAL.ai
        try:
            music_generation = generate_music_with_fal(prompt)
        except Exception as e:
            # Return error instead of mock
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Music generation failed: {str(e)}',
                    'prompt': prompt
                })
            }
        
        # Store if session exists
        if session_id in sessions:
            sessions[session_id]['music_generations'].append(music_generation)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'success',
                'music': music_generation
            })
        }
    
        elif path.startswith('/api/generate_ideas/') and method == 'POST':
        # Extract session ID from path
        session_id = path.split('/')[-1]
        
        # For testing, use default values if session not found
        if session_id not in sessions:
            episode_number = 1779
            theme = "Media Meltdown"
            print(f"Session {session_id} not found, using defaults: Episode {episode_number}, Theme: {theme}")
        else:
            session = sessions[session_id]
            episode_number = session['episode_number']
            theme = session['theme']
        
        # Generate real ideas with GROK
        try:
            print(f"Starting GROK idea generation for Episode {episode_number}, Theme: {theme}")
            ideas_generation = generate_ideas_with_grok(episode_number, theme)
            print(f"GROK idea generation completed successfully")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"GROK idea generation error: {str(e)}")
            print(f"Full traceback: {error_details}")
            
            # Return error instead of mock
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Ideas generation failed: {str(e)}',
                    'episode': episode_number,
                    'theme': theme,
                    'traceback': error_details
                })
            }
        
        # Store if session exists
        if session_id in sessions:
            sessions[session_id]['ideas'].append(ideas_generation)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'success',
                'ideas': ideas_generation
            })
        }
    
        # Default 404
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Not found',
                'path': path,
                'method': method
            })
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Lambda handler error: {str(e)}")
        print(f"Full traceback: {error_details}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}',
                'traceback': error_details
            })
        }
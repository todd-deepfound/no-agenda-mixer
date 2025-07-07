import json
import os
from datetime import datetime
import uuid

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
            'model': os.getenv('GROK_MODEL', 'grok-2-1212'),
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
    """Simple Lambda handler for testing APIs"""
    
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
        
        if path == '/health' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'has_grok_key': bool(os.getenv('GROK_API_KEY')),
                    'has_fal_key': bool(os.getenv('FAL_API_KEY'))
                })
            }
        
        elif path == '/test/grok' and method == 'POST':
            # Test GROK AI directly - simple version
            try:
                import requests
                
                grok_key = os.getenv('GROK_API_KEY')
                if not grok_key:
                    raise Exception("GROK_API_KEY not available")
                
                headers = {
                    'Authorization': f'Bearer {grok_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'messages': [
                        {'role': 'user', 'content': 'Hello! Generate a simple test response for No Agenda Episode 1779.'}
                    ],
                    'model': 'grok-2-1212',
                    'temperature': 0.7
                }
                
                response = requests.post(
                    'https://api.x.ai/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'statusCode': 200,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'status': 'success',
                            'grok_response': result
                        })
                    }
                else:
                    return {
                        'statusCode': 500,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'error': f'GROK API error: {response.status_code}',
                            'response_text': response.text
                        })
                    }
                    
            except Exception as e:
                import traceback
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    })
                }
        
        elif path == '/test/fal' and method == 'POST':
            # Test FAL.ai directly - simple version
            try:
                import requests
                
                fal_key = os.getenv('FAL_API_KEY')
                if not fal_key:
                    raise Exception("FAL_API_KEY not available")
                
                prompt = "Chaotic breakbeat electronic music with news broadcast samples, media criticism energy, and distortion effects, 140 BPM"
                
                headers = {
                    'Authorization': f'Key {fal_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'prompt': prompt,
                    'duration': 30
                }
                
                response = requests.post(
                    'https://fal.run/fal-ai/stable-audio',
                    headers=headers,
                    json=payload,
                    timeout=120  # Music generation takes longer
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract the audio URL from FAL.ai response
                    audio_url = result.get('audio_file', {}).get('url') if 'audio_file' in result else result.get('audio_url')
                    
                    return {
                        'statusCode': 200,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'status': 'success',
                            'fal_response': result,
                            'prompt': prompt,
                            'audio_url': audio_url,
                            'duration': 30
                        })
                    }
                else:
                    return {
                        'statusCode': 500,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'error': f'FAL.ai API error: {response.status_code}',
                            'response_text': response.text,
                            'prompt': prompt
                        })
                    }
                    
            except Exception as e:
                import traceback
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    })
                }
        
        # Default response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'API Test Endpoints',
                'endpoints': [
                    'GET /health',
                    'POST /test/grok',
                    'POST /test/fal'
                ]
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
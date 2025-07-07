#!/usr/bin/env python3
"""
Production Professional No Agenda Audio Mixer
Real audio processing with S3 integration for AWS Lambda
"""

import json
import os
import sys
import tempfile
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

# Import our custom modules
from audio_processor import ProfessionalAudioProcessor
from s3_manager import S3Manager
from metrics_handler import ProcessingMetrics, track_processing_metrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionMixer:
    """Production-ready professional audio mixer"""
    
    def __init__(self):
        self.s3_manager = S3Manager()
        self.audio_processor = None
        self.session_id = None
        
        # Ensure S3 bucket exists
        self.s3_manager.ensure_bucket_exists()
    
    def create_professional_mix_production(self, episode_url: str, theme: str = "Best Of", 
                                         target_duration: int = 300, session_id: str = None) -> Optional[Dict[str, Any]]:
        """Create professional mix with full production pipeline"""
        metrics = ProcessingMetrics()
        metrics.start_timer("total_processing")
        
        try:
            self.session_id = session_id or str(uuid.uuid4())
            logger.info(f"Creating production mix - Session: {self.session_id}, Theme: {theme}")
            
            # Initialize audio processor
            self.audio_processor = ProfessionalAudioProcessor()
            
            # Step 1: Load and analyze audio
            logger.info("Step 1: Loading and analyzing audio")
            metrics.start_timer("audio_download")
            audio_data, sr = self.audio_processor.load_audio_from_url(episode_url)
            metrics.end_timer("audio_download")
            
            if audio_data is None:
                metrics.track_error("audio_load", "Failed to load audio from URL")
                return self._error_response("Failed to load audio from URL")
            
            # Step 2: Advanced audio analysis
            logger.info("Step 2: Performing advanced audio analysis")
            metrics.start_timer("audio_analysis")
            analysis = self.audio_processor.analyze_audio_advanced(audio_data, sr)
            metrics.end_timer("audio_analysis")
            
            if analysis.get('analysis_type') == 'failed':
                metrics.track_error("audio_analysis", analysis.get('error', 'Unknown'))
                return self._error_response(f"Audio analysis failed: {analysis.get('error')}")
            
            # Step 3: Intelligent segment selection
            logger.info("Step 3: Selecting optimal segments")
            target_segments = min(5, max(3, target_duration // 60))  # 1 segment per minute roughly
            segments = self.audio_processor.intelligent_segment_selection(
                analysis, target_segments=target_segments
            )
            
            if not segments:
                return self._error_response("No suitable segments found")
            
            logger.info(f"Selected {len(segments)} segments for mixing")
            
            # Step 4: Create professional mix
            logger.info("Step 4: Creating professional mix")
            metrics.start_timer("mix_creation")
            mix_file_path = self.audio_processor.create_professional_mix(
                audio_data, sr, segments, theme
            )
            metrics.end_timer("mix_creation")
            
            if not mix_file_path or not os.path.exists(mix_file_path):
                metrics.track_error("mix_creation", "Failed to create mix file")
                return self._error_response("Failed to create mix file")
            
            # Step 5: Stream to S3 and generate download URL
            logger.info("Step 5: Streaming to S3 and generating download URL")
            
            # Extract episode number from URL (basic extraction)
            episode_number = self._extract_episode_number(episode_url)
            
            # Stream directly to S3 without saving to disk
            import io
            mix_key = f"mixes/{episode_number}/{theme.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.mp3"
            
            try:
                # Export to BytesIO buffer
                with io.BytesIO() as buf:
                    # Get file size before streaming
                    file_size = os.path.getsize(mix_file_path)
                    
                    # Read the mix file and stream to S3
                    with open(mix_file_path, 'rb') as f:
                        self.s3_manager.s3_client.upload_fileobj(
                            f, 
                            self.s3_manager.bucket_name, 
                            mix_key,
                            ExtraArgs={'ContentType': 'audio/mpeg'}
                        )
                    
                    logger.info(f"Streamed mix to S3: {mix_key}")
                
                # Generate presigned URL
                presigned_url = self.s3_manager.generate_presigned_url(mix_key, expiration=86400)
                
                if not presigned_url:
                    return self._error_response("Failed to generate download URL")
                
                upload_result = {
                    's3_key': mix_key,
                    'download_url': presigned_url,
                    'bucket': self.s3_manager.bucket_name,
                    'file_size': file_size
                }
                
            except Exception as e:
                logger.error(f"S3 streaming failed: {e}")
                return self._error_response(f"Failed to upload mix to S3: {str(e)}")
            
            # Step 6: Prepare response with all metadata
            logger.info("Step 6: Preparing response")
            
            # Track final metrics
            metrics.end_timer("total_processing")
            metrics.track_mix_creation(theme, len(segments), 
                                     analysis.get('duration', 0), 
                                     upload_result.get('file_size', 0))
            
            # Emit metrics to CloudWatch
            metrics.emit_metrics()
            
            response = {
                'status': 'success',
                'session_id': self.session_id,
                'mix_metadata': {
                    'theme': theme,
                    'episode_number': episode_number,
                    'duration_target': target_duration,
                    'segments_count': len(segments),
                    'processing_type': 'professional_production',
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'created_at': datetime.now().isoformat(),
                    'sample_rate': sr
                },
                'download': {
                    'url': upload_result['download_url'],
                    's3_key': upload_result['s3_key'],
                    'bucket': upload_result['bucket'],
                    'expires_in_hours': 24
                },
                'analysis': {
                    'audio_duration': analysis.get('duration', 0),
                    'segments_selected': len(segments),
                    'selection_method': segments[0].get('selection_method', 'unknown') if segments else 'none',
                    'average_confidence': sum(s.get('confidence', 0) for s in segments) / len(segments) if segments else 0,
                    'tempo': analysis.get('tempo', 0),
                    'energy_score': analysis.get('rms_energy_mean', 0)
                },
                'segments': [
                    {
                        'name': seg['name'],
                        'start_time': seg['timestamp'],
                        'duration': seg.get('duration', 20),
                        'confidence': seg.get('confidence', 0),
                        'description': seg.get('description', '')
                    }
                    for seg in segments
                ],
                'processing_chain': self.audio_processor.processing_chains.get(theme, {}).get('description', ''),
                'message': f'Professional mix created successfully with {len(segments)} segments'
            }
            
            logger.info(f"Production mix completed successfully: {upload_result['s3_key']}")
            return response
            
        except Exception as e:
            logger.error(f"Production mix creation failed: {e}")
            metrics.track_error("production_pipeline", str(e))
            metrics.emit_metrics()
            return self._error_response(f"Mix creation failed: {str(e)}")
        finally:
            # Cleanup
            if self.audio_processor:
                self.audio_processor.cleanup()
    
    def _extract_episode_number(self, url: str) -> int:
        """Extract episode number from URL"""
        try:
            # Look for NA-XXXX pattern
            import re
            match = re.search(r'NA-?(\d+)', url)
            if match:
                return int(match.group(1))
            
            # Fallback: look for any 4-digit number
            match = re.search(r'(\d{4})', url)
            if match:
                return int(match.group(1))
            
            # Default fallback
            return 9999
            
        except Exception:
            return 9999
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'status': 'error',
            'message': message,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'processing_type': 'professional_production'
        }
    
    def get_mix_history(self, episode_number: int = None) -> Dict[str, Any]:
        """Get history of created mixes"""
        try:
            mixes = self.s3_manager.list_mixes(episode_number)
            return {
                'status': 'success',
                'mixes': mixes,
                'count': len(mixes),
                'episode_filter': episode_number
            }
        except Exception as e:
            logger.error(f"Failed to get mix history: {e}")
            return self._error_response(f"Failed to get mix history: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the production mixer"""
        try:
            # Check S3 connectivity
            bucket_accessible = self.s3_manager.ensure_bucket_exists()
            
            # Check audio processing capabilities
            import librosa
            import pydub
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    's3_bucket': bucket_accessible,
                    'librosa_available': True,
                    'pydub_available': True,
                    'ffmpeg_available': self._check_ffmpeg()
                },
                'processing_type': 'professional_production',
                'themes_available': list(ProfessionalAudioProcessor().processing_chains.keys())
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available"""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

def lambda_handler(event, context):
    """AWS Lambda handler for production professional mixing"""
    try:
        logger.info("Production professional mixer Lambda handler started")
        
        # Handle CORS preflight
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
        
        # Parse request
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '')
        
        mixer = ProductionMixer()
        
        # Route requests
        if path.endswith('/health') or 'health' in path:
            result = mixer.health_check()
        elif path.endswith('/history') or 'history' in path:
            # Parse query parameters for episode filter
            query_params = event.get('queryStringParameters') or {}
            episode_number = query_params.get('episode')
            if episode_number:
                episode_number = int(episode_number)
            result = mixer.get_mix_history(episode_number)
        else:
            # Main mixing endpoint
            body = json.loads(event.get('body', '{}'))
            
            episode_url = body.get('episode_url', 'https://op3.dev/e/mp3s.nashownotes.com/NA-1779-2025-07-06-Final.mp3')
            theme = body.get('theme', 'Best Of')
            target_duration = body.get('target_duration', 180)  # 3 minutes default
            session_id = body.get('session_id')
            
            logger.info(f"Processing request: {episode_url}, {theme}, {target_duration}s")
            
            result = mixer.create_professional_mix_production(
                episode_url, theme, target_duration, session_id
            )
        
        # Return response
        status_code = 200 if result.get('status') == 'success' else 500
        if result.get('status') == 'error' and 'not found' in result.get('message', '').lower():
            status_code = 404
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps(result, indent=2)
        }
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'error',
                'message': str(e),
                'type': 'lambda_error',
                'timestamp': datetime.now().isoformat()
            })
        }

if __name__ == '__main__':
    """Command line usage for testing"""
    mixer = ProductionMixer()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'health':
        result = mixer.health_check()
        print(json.dumps(result, indent=2))
    else:
        episode_url = "https://op3.dev/e/mp3s.nashownotes.com/NA-1779-2025-07-06-Final.mp3"
        theme = sys.argv[1] if len(sys.argv) > 1 else "Best Of"
        
        result = mixer.create_professional_mix_production(episode_url, theme, 120)
        
        if result.get('status') == 'success':
            print(f"🎉 Professional production mix created!")
            print(f"📁 S3 Key: {result['download']['s3_key']}")
            print(f"🔗 Download: {result['download']['url']}")
            print(f"📊 Segments: {result['analysis']['segments_selected']}")
            print(f"💾 Size: {result['mix_metadata']['file_size_mb']} MB")
        else:
            print(f"❌ Mix creation failed: {result.get('message')}")
            print(json.dumps(result, indent=2))
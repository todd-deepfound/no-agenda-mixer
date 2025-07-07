#!/usr/bin/env python3
"""
Professional No Agenda Audio Mixer - Server Side
High-end audio processing for creating professional podcast mixes
Uses pedalboard for professional effects, librosa for analysis, soundfile for I/O
"""

import json
import os
import sys
import requests
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Professional audio libraries
try:
    from pedalboard import Pedalboard, Compressor, EQ, Reverb, HighpassFilter, LowpassFilter, Gain, Limiter
    import soundfile as sf
    import librosa
    import numpy as np
    from pydub import AudioSegment
    import ffmpeg
except ImportError as e:
    print(f"Missing audio library: {e}")
    print("Install with: pip install pedalboard librosa soundfile pydub ffmpeg-python")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfessionalAudioMixer:
    """Professional-grade audio mixer for No Agenda podcasts"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.temp_dir = None
        
        # Professional mixing chains for different themes
        self.mixing_chains = {
            'Best Of': Pedalboard([
                HighpassFilter(cutoff_frequency_hz=80),
                EQ(frequency_hz=200, gain_db=2, q=0.7),  # Warmth
                EQ(frequency_hz=3000, gain_db=1.5, q=1.2),  # Presence
                Compressor(threshold_db=-18, ratio=3, attack_ms=5, release_ms=100),
                Reverb(room_size=0.2, damping=0.5, wet_level=0.1),
                Limiter(threshold_db=-0.5, release_ms=50)
            ]),
            
            'Media Meltdown': Pedalboard([
                HighpassFilter(cutoff_frequency_hz=100),
                EQ(frequency_hz=800, gain_db=-2, q=1.5),  # Reduce mud
                EQ(frequency_hz=4000, gain_db=3, q=1.8),  # Aggressive presence
                Compressor(threshold_db=-14, ratio=4, attack_ms=2, release_ms=50),
                Gain(gain_db=2),  # Hot signal
                Limiter(threshold_db=-0.1, release_ms=25)
            ]),
            
            'Conspiracy Corner': Pedalboard([
                HighpassFilter(cutoff_frequency_hz=60),
                LowpassFilter(cutoff_frequency_hz=8000),  # Dark tone
                EQ(frequency_hz=120, gain_db=1.5, q=0.8),  # Low end
                EQ(frequency_hz=2500, gain_db=-1, q=1.0),  # Reduce harshness
                Compressor(threshold_db=-20, ratio=2.5, attack_ms=10, release_ms=200),
                Reverb(room_size=0.4, damping=0.8, wet_level=0.15),  # Mysterious space
                Limiter(threshold_db=-1.0, release_ms=100)
            ]),
            
            'Donation Nation': Pedalboard([
                HighpassFilter(cutoff_frequency_hz=85),
                EQ(frequency_hz=150, gain_db=2.5, q=0.6),  # Fullness
                EQ(frequency_hz=3500, gain_db=2.8, q=1.1),  # Clarity
                EQ(frequency_hz=8000, gain_db=1.2, q=0.9),  # Air
                Compressor(threshold_db=-16, ratio=2.8, attack_ms=3, release_ms=80),
                Reverb(room_size=0.25, damping=0.4, wet_level=0.12),
                Limiter(threshold_db=-0.3, release_ms=40)
            ]),
            
            'Musical Mayhem': Pedalboard([
                HighpassFilter(cutoff_frequency_hz=90),
                EQ(frequency_hz=100, gain_db=1.8, q=0.9),  # Punch
                EQ(frequency_hz=1200, gain_db=-0.5, q=1.2),
                EQ(frequency_hz=5000, gain_db=2.2, q=1.5),  # Sparkle
                Compressor(threshold_db=-15, ratio=3.5, attack_ms=1, release_ms=60),
                Reverb(room_size=0.35, damping=0.3, wet_level=0.18),  # Creative space
                Limiter(threshold_db=-0.2, release_ms=30)
            ])
        }
    
    def setup_temp_directory(self) -> str:
        """Setup temporary directory for audio processing"""
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix='no_agenda_mixer_')
        return self.temp_dir
    
    def cleanup_temp_directory(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def download_podcast_episode(self, episode_url: str) -> Optional[str]:
        """Download podcast episode to temporary file"""
        try:
            temp_dir = self.setup_temp_directory()
            temp_file = os.path.join(temp_dir, f"episode_{uuid.uuid4().hex[:8]}.mp3")
            
            logger.info(f"Downloading episode from: {episode_url}")
            response = requests.get(episode_url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded episode to: {temp_file}")
            return temp_file
            
        except Exception as e:
            logger.error(f"Failed to download episode: {e}")
            return None
    
    def convert_to_wav(self, input_file: str) -> Optional[str]:
        """Convert any audio format to WAV using FFmpeg"""
        try:
            temp_dir = self.setup_temp_directory()
            output_file = os.path.join(temp_dir, f"converted_{uuid.uuid4().hex[:8]}.wav")
            
            logger.info(f"Converting {input_file} to WAV format")
            
            (ffmpeg
                .input(input_file)
                .output(output_file, 
                       acodec='pcm_s24le',  # 24-bit PCM
                       ar=self.sample_rate,  # Sample rate
                       ac=2)  # Stereo
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))
            
            logger.info(f"Converted to: {output_file}")
            return output_file
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg conversion failed: {e.stderr.decode() if e.stderr else str(e)}")
            return None
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return None
    
    def load_audio_professional(self, file_path: str) -> Tuple[Optional[np.ndarray], int]:
        """Load audio using professional-grade libraries"""
        try:
            # First convert to WAV if needed
            if not file_path.lower().endswith('.wav'):
                wav_file = self.convert_to_wav(file_path)
                if not wav_file:
                    return None, 0
                file_path = wav_file
            
            # Load with SoundFile for professional quality
            audio_data, sample_rate = sf.read(file_path, dtype='float32')
            
            # Convert to mono if stereo (for analysis)
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            logger.info(f"Loaded audio: {len(audio_data)/sample_rate:.1f}s at {sample_rate}Hz")
            return audio_data, sample_rate
            
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            return None, 0
    
    def analyze_audio_content(self, audio: np.ndarray, sr: int) -> Dict:
        """Analyze audio content using Librosa for intelligent segment selection"""
        try:
            logger.info("Analyzing audio content...")
            
            # Tempo and beat analysis
            tempo, beats = librosa.beat.beat_track(y=audio, sr=sr, units='time')
            
            # Onset detection (for finding speech segments)
            onsets = librosa.onset.onset_detect(y=audio, sr=sr, units='time')
            
            # Energy analysis (for finding dynamic segments)
            hop_length = 512
            energy = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
            energy_times = librosa.frames_to_time(np.arange(len(energy)), sr=sr, hop_length=hop_length)
            
            # Spectral features for content analysis
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            
            # Find high-energy segments (likely interesting content)
            energy_threshold = np.percentile(energy, 75)  # Top 25% energy
            high_energy_segments = []
            
            for i, e in enumerate(energy):
                if e > energy_threshold:
                    time_pos = energy_times[i]
                    high_energy_segments.append({
                        'time': time_pos,
                        'energy': float(e),
                        'spectral_centroid': float(spectral_centroids[i])
                    })
            
            analysis = {
                'duration': len(audio) / sr,
                'tempo': float(tempo),
                'beats': beats.tolist(),
                'onsets': onsets.tolist(),
                'high_energy_segments': high_energy_segments,
                'avg_energy': float(np.mean(energy)),
                'avg_spectral_centroid': float(np.mean(spectral_centroids))
            }
            
            logger.info(f"Analysis complete: {tempo:.1f} BPM, {len(onsets)} onsets, {len(high_energy_segments)} high-energy segments")
            return analysis
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return {}
    
    def intelligent_segment_selection(self, audio: np.ndarray, sr: int, analysis: Dict, 
                                    target_segments: int = 5) -> List[Dict]:
        """Intelligently select interesting segments from audio analysis"""
        try:
            duration = len(audio) / sr
            high_energy_segments = analysis.get('high_energy_segments', [])
            onsets = analysis.get('onsets', [])
            
            # If we have high-energy segments, use them
            if high_energy_segments:
                # Sort by energy and take diverse segments
                sorted_segments = sorted(high_energy_segments, key=lambda x: x['energy'], reverse=True)
                
                selected_segments = []
                min_gap = duration / (target_segments * 2)  # Minimum gap between segments
                
                for segment in sorted_segments:
                    if len(selected_segments) >= target_segments:
                        break
                    
                    time_pos = segment['time']
                    
                    # Check if this segment is far enough from existing ones
                    too_close = any(abs(time_pos - s['timestamp']) < min_gap for s in selected_segments)
                    
                    if not too_close:
                        selected_segments.append({
                            'name': f'High Energy Segment {len(selected_segments) + 1}',
                            'timestamp': time_pos,
                            'duration': 15 + (segment['energy'] * 10),  # Dynamic duration based on energy
                            'description': f'High energy content (Energy: {segment["energy"]:.2f})',
                            'confidence': segment['energy']
                        })
                
                if selected_segments:
                    # Sort by timestamp
                    selected_segments.sort(key=lambda x: x['timestamp'])
                    return selected_segments
            
            # Fallback: Use onset-based segmentation
            if onsets:
                segment_duration = duration / target_segments
                selected_segments = []
                
                for i in range(target_segments):
                    start_time = i * segment_duration
                    
                    # Find nearest onset
                    nearest_onset = min(onsets, key=lambda x: abs(x - start_time))
                    
                    selected_segments.append({
                        'name': f'Onset Segment {i + 1}',
                        'timestamp': nearest_onset,
                        'duration': 12 + np.random.randint(6, 18),  # 12-24 second segments
                        'description': f'Content segment at onset',
                        'confidence': 0.7
                    })
                
                return selected_segments
            
            # Last resort: Equal time division
            logger.warning("Using fallback segmentation")
            return self.create_fallback_segments(duration, target_segments)
            
        except Exception as e:
            logger.error(f"Intelligent segmentation failed: {e}")
            return self.create_fallback_segments(duration if 'duration' in locals() else 3600, target_segments)
    
    def create_fallback_segments(self, duration: float, target_segments: int) -> List[Dict]:
        """Create fallback segments when analysis fails"""
        segments = []
        segment_duration = duration / (target_segments + 1)
        
        for i in range(target_segments):
            start_time = (i + 0.5) * segment_duration
            segments.append({
                'name': f'Segment {i + 1}',
                'timestamp': start_time,
                'duration': 15,
                'description': f'Content segment {i + 1}',
                'confidence': 0.5
            })
        
        return segments
    
    def extract_and_process_segment(self, audio: np.ndarray, sr: int, 
                                  start_time: float, duration: float, theme: str) -> np.ndarray:
        """Extract and professionally process an audio segment"""
        try:
            start_sample = int(start_time * sr)
            end_sample = int((start_time + duration) * sr)
            
            # Extract segment
            segment = audio[start_sample:end_sample]
            
            # Apply professional mixing chain for the theme
            mixing_chain = self.mixing_chains.get(theme, self.mixing_chains['Best Of'])
            
            # Convert to stereo for processing
            if len(segment.shape) == 1:
                segment_stereo = np.column_stack([segment, segment])
            else:
                segment_stereo = segment
            
            # Apply professional effects
            processed = mixing_chain(segment_stereo, sr)
            
            # Add professional fades
            fade_samples = int(0.1 * sr)  # 100ms fades
            if len(processed) > fade_samples * 2:
                # Fade in
                fade_in = np.linspace(0, 1, fade_samples)
                processed[:fade_samples] *= fade_in[:, np.newaxis]
                
                # Fade out
                fade_out = np.linspace(1, 0, fade_samples)
                processed[-fade_samples:] *= fade_out[:, np.newaxis]
            
            return processed
            
        except Exception as e:
            logger.error(f"Segment processing failed: {e}")
            return np.array([])
    
    def generate_music_with_fal(self, prompt: str, duration: int = 30) -> Optional[np.ndarray]:
        """Generate AI music using FAL.ai API"""
        try:
            # Get API key from environment or config
            api_key = os.getenv('FAL_API_KEY')
            if not api_key:
                logger.warning("FAL_API_KEY not found, skipping music generation")
                return None
            
            logger.info(f"Generating music: {prompt[:50]}...")
            
            headers = {
                'Authorization': f'Key {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'prompt': prompt,
                'duration': duration
            }
            
            response = requests.post(
                'https://fal.run/fal-ai/stable-audio',
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                audio_url = result.get('audio_file', {}).get('url')
                
                if audio_url:
                    # Download and load the generated music
                    audio_response = requests.get(audio_url, timeout=60)
                    if audio_response.status_code == 200:
                        temp_dir = self.setup_temp_directory()
                        temp_music_file = os.path.join(temp_dir, f"music_{uuid.uuid4().hex[:8]}.wav")
                        
                        with open(temp_music_file, 'wb') as f:
                            f.write(audio_response.content)
                        
                        # Load with professional quality
                        music_data, music_sr = sf.read(temp_music_file, dtype='float32')
                        
                        # Resample if needed
                        if music_sr != self.sample_rate:
                            music_data = librosa.resample(music_data, orig_sr=music_sr, target_sr=self.sample_rate)
                        
                        logger.info("Music generation successful")
                        return music_data
            
            logger.warning(f"Music generation failed: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Music generation error: {e}")
            return None
    
    def create_professional_mix(self, episode_url: str, theme: str = "Best Of", 
                              target_duration: int = 300) -> Optional[str]:
        """Create a professional mix from a podcast episode"""
        try:
            logger.info(f"Creating professional mix - Theme: {theme}")
            
            # Download episode
            episode_file = self.download_podcast_episode(episode_url)
            if not episode_file:
                return None
            
            # Load and analyze audio
            audio, sr = self.load_audio_professional(episode_file)
            if audio is None:
                return None
            
            # Analyze content
            analysis = self.analyze_audio_content(audio, sr)
            
            # Intelligent segment selection
            segments = self.intelligent_segment_selection(audio, sr, analysis)
            
            logger.info(f"Selected {len(segments)} segments for mixing")
            
            # Process segments
            mix_segments = []
            total_duration = 0
            
            # Generate intro music
            intro_music = self.generate_music_with_fal(
                f"Professional podcast intro music, {theme.lower()} style, energetic, 10 seconds",
                duration=10
            )
            
            if intro_music is not None:
                mix_segments.append(intro_music)
                total_duration += len(intro_music) / self.sample_rate
            
            # Process each segment
            for i, segment in enumerate(segments):
                if total_duration >= target_duration:
                    break
                
                logger.info(f"Processing segment {i+1}: {segment['name']}")
                
                processed_segment = self.extract_and_process_segment(
                    audio, sr, segment['timestamp'], segment['duration'], theme
                )
                
                if len(processed_segment) > 0:
                    mix_segments.append(processed_segment)
                    total_duration += len(processed_segment) / self.sample_rate
                    
                    # Add transition music between segments
                    if i < len(segments) - 1 and total_duration < target_duration - 30:
                        transition_music = self.generate_music_with_fal(
                            f"Short transition music, {theme.lower()} style, 5 seconds",
                            duration=5
                        )
                        
                        if transition_music is not None:
                            mix_segments.append(transition_music)
                            total_duration += len(transition_music) / self.sample_rate
            
            # Generate outro music
            outro_music = self.generate_music_with_fal(
                f"Professional podcast outro music, {theme.lower()} style, conclusive, 15 seconds",
                duration=15
            )
            
            if outro_music is not None:
                mix_segments.append(outro_music)
            
            # Combine all segments
            if not mix_segments:
                logger.error("No segments to mix")
                return None
            
            # Concatenate with professional crossfades
            final_mix = self.crossfade_segments(mix_segments)
            
            # Apply final mastering
            final_mix = self.apply_mastering_chain(final_mix, theme)
            
            # Export final mix
            output_path = self.export_final_mix(final_mix, theme)
            
            logger.info(f"Professional mix created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Mix creation failed: {e}")
            return None
        finally:
            self.cleanup_temp_directory()
    
    def crossfade_segments(self, segments: List[np.ndarray], crossfade_duration: float = 0.5) -> np.ndarray:
        """Professional crossfading between segments"""
        if not segments:
            return np.array([])
        
        if len(segments) == 1:
            return segments[0]
        
        crossfade_samples = int(crossfade_duration * self.sample_rate)
        result = segments[0]
        
        for i in range(1, len(segments)):
            current_segment = segments[i]
            
            if len(result) > crossfade_samples and len(current_segment) > crossfade_samples:
                # Create crossfade
                overlap_end = result[-crossfade_samples:]
                overlap_start = current_segment[:crossfade_samples]
                
                # Apply crossfade curves
                fade_out = np.linspace(1, 0, crossfade_samples)
                fade_in = np.linspace(0, 1, crossfade_samples)
                
                if len(overlap_end.shape) == 2:
                    fade_out = fade_out[:, np.newaxis]
                    fade_in = fade_in[:, np.newaxis]
                
                crossfaded = overlap_end * fade_out + overlap_start * fade_in
                
                # Combine segments
                result = np.concatenate([
                    result[:-crossfade_samples],
                    crossfaded,
                    current_segment[crossfade_samples:]
                ])
            else:
                # Simple concatenation if segments are too short
                result = np.concatenate([result, current_segment])
        
        return result
    
    def apply_mastering_chain(self, audio: np.ndarray, theme: str) -> np.ndarray:
        """Apply final mastering processing"""
        try:
            # Final mastering chain
            mastering_chain = Pedalboard([
                EQ(frequency_hz=30, gain_db=-6, q=0.7),  # Sub cleanup
                Compressor(threshold_db=-8, ratio=2, attack_ms=10, release_ms=100),  # Bus compression
                EQ(frequency_hz=10000, gain_db=1, q=0.8),  # Air
                Limiter(threshold_db=-0.1, release_ms=50)  # Final limiting
            ])
            
            return mastering_chain(audio, self.sample_rate)
            
        except Exception as e:
            logger.error(f"Mastering failed: {e}")
            return audio
    
    def export_final_mix(self, audio: np.ndarray, theme: str) -> str:
        """Export the final mix with professional quality"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
            
            # Create output directory
            output_dir = Path(__file__).parent.parent / 'output'
            output_dir.mkdir(exist_ok=True)
            
            output_path = output_dir / f'Professional_NoAgenda_{safe_theme}_{timestamp}.wav'
            
            # Export with professional quality (24-bit WAV)
            sf.write(str(output_path), audio, self.sample_rate, subtype='PCM_24')
            
            # Also create MP3 version for convenience
            mp3_path = output_path.with_suffix('.mp3')
            (ffmpeg
                .input(str(output_path))
                .output(str(mp3_path), acodec='libmp3lame', audio_bitrate='320k')
                .overwrite_output()
                .run(capture_stdout=True))
            
            return str(mp3_path)
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return ""

def lambda_handler(event, context):
    """AWS Lambda handler for professional mixing"""
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        episode_url = body.get('episode_url', 'https://op3.dev/e/mp3s.nashownotes.com/NA-1779-2025-07-06-Final.mp3')
        theme = body.get('theme', 'Best Of')
        target_duration = body.get('target_duration', 300)
        
        # Create professional mixer
        mixer = ProfessionalAudioMixer()
        
        # Create mix
        output_path = mixer.create_professional_mix(episode_url, theme, target_duration)
        
        if output_path:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'success',
                    'mix_path': output_path,
                    'theme': theme,
                    'message': 'Professional mix created successfully'
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
                    'status': 'error',
                    'message': 'Mix creation failed'
                })
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
                'message': str(e)
            })
        }

if __name__ == '__main__':
    """Command line usage for testing"""
    mixer = ProfessionalAudioMixer()
    
    episode_url = "https://op3.dev/e/mp3s.nashownotes.com/NA-1779-2025-07-06-Final.mp3"
    theme = sys.argv[1] if len(sys.argv) > 1 else "Best Of"
    
    output_path = mixer.create_professional_mix(episode_url, theme)
    
    if output_path:
        print(f"🎉 Professional mix created: {output_path}")
        print(f"🎧 Play with: open '{output_path}'")
    else:
        print("❌ Mix creation failed")
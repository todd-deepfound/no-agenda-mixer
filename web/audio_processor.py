#!/usr/bin/env python3
"""
Professional Audio Processor for No Agenda Mixer
Real audio processing using PyDub, Librosa, and FFmpeg
"""

import os
import tempfile
import logging
import subprocess
import json
import io
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime
import concurrent.futures

# Real audio processing libraries
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from pydub.silence import detect_nonsilent

logger = logging.getLogger(__name__)

class ProfessionalAudioProcessor:
    """Advanced audio processing for podcast mixing"""
    
    def __init__(self, sample_rate: int = 44100, temp_dir: str = None):
        self.sample_rate = sample_rate
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix='noagenda_audio_')
        
        # Professional processing chains for different themes
        self.processing_chains = {
            'Best Of': {
                'eq_low_gain': 2.0,      # Boost low frequencies
                'eq_mid_gain': 1.5,      # Slight mid boost
                'eq_high_gain': 1.2,     # Gentle high boost
                'compression_ratio': 3.0, # Moderate compression
                'compression_threshold': -18.0,
                'reverb_room_size': 0.2,
                'reverb_wet': 0.1,
                'limiter_threshold': -0.5,
                'description': 'Warm, polished broadcast sound'
            },
            'Media Meltdown': {
                'eq_low_gain': 1.5,
                'eq_mid_gain': 2.5,      # Aggressive mid boost
                'eq_high_gain': 2.0,     # Hot highs
                'compression_ratio': 4.0, # Heavy compression
                'compression_threshold': -15.0,
                'reverb_room_size': 0.1,
                'reverb_wet': 0.05,
                'limiter_threshold': -0.3,
                'description': 'Aggressive, in-your-face processing'
            },
            'Conspiracy Corner': {
                'eq_low_gain': 0.8,      # Reduce lows for mystery
                'eq_mid_gain': 1.2,
                'eq_high_gain': 0.9,     # Darker sound
                'compression_ratio': 2.5,
                'compression_threshold': -20.0,
                'reverb_room_size': 0.4, # More spacious
                'reverb_wet': 0.2,
                'limiter_threshold': -0.7,
                'description': 'Dark, mysterious atmosphere'
            },
            'Donation Nation': {
                'eq_low_gain': 2.2,      # Full bottom end
                'eq_mid_gain': 1.8,
                'eq_high_gain': 1.5,     # Bright and celebratory
                'compression_ratio': 3.5,
                'compression_threshold': -16.0,
                'reverb_room_size': 0.3,
                'reverb_wet': 0.12,
                'limiter_threshold': -0.4,
                'description': 'Full, celebratory sound'
            },
            'Musical Mayhem': {
                'eq_low_gain': 1.8,
                'eq_mid_gain': 1.3,
                'eq_high_gain': 1.6,     # Musical clarity
                'compression_ratio': 2.8,
                'compression_threshold': -17.0,
                'reverb_room_size': 0.25,
                'reverb_wet': 0.18,     # More reverb for music
                'limiter_threshold': -0.6,
                'description': 'Optimized for musical content'
            }
        }
    
    def load_audio_from_url(self, url: str) -> Optional[Tuple[np.ndarray, int]]:
        """Download and load audio file from URL"""
        try:
            import requests
            
            temp_file = os.path.join(self.temp_dir, f"download_{os.urandom(4).hex()}.mp3")
            
            logger.info(f"Downloading audio from {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, stream=True, timeout=300, headers=headers)
            response.raise_for_status()
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Load with librosa for analysis
            audio_data, sr = librosa.load(temp_file, sr=self.sample_rate)
            logger.info(f"Loaded audio: {len(audio_data)/sr:.1f}s at {sr}Hz")
            
            return audio_data, sr
            
        except Exception as e:
            logger.error(f"Failed to load audio from URL: {e}")
            return None
    
    def load_audio_segment(self, file_path: str) -> Optional[AudioSegment]:
        """Load audio file as PyDub AudioSegment"""
        try:
            audio = AudioSegment.from_file(file_path)
            logger.info(f"Loaded AudioSegment: {len(audio)/1000:.1f}s")
            return audio
        except Exception as e:
            logger.error(f"Failed to load AudioSegment: {e}")
            return None
    
    def analyze_audio_advanced(self, audio_data: np.ndarray, sr: int) -> Dict:
        """Advanced audio analysis using Librosa"""
        try:
            logger.info("Starting advanced audio analysis")
            
            # Basic properties
            duration = len(audio_data) / sr
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_data)[0]
            
            # Energy and rhythm analysis
            hop_length = 512
            frame_length = 2048
            
            # RMS energy
            rms = librosa.feature.rms(y=audio_data, frame_length=frame_length, hop_length=hop_length)[0]
            
            # Tempo detection
            tempo, beats = librosa.beat.beat_track(y=audio_data, sr=sr)
            
            # Mel-frequency cepstral coefficients
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sr, n_mfcc=13)
            
            # Find high-energy segments
            energy_threshold = np.percentile(rms, 75)  # Top 25% energy
            high_energy_frames = np.where(rms > energy_threshold)[0]
            
            # Convert frames to time segments
            times = librosa.frames_to_time(high_energy_frames, sr=sr, hop_length=hop_length)
            
            # Group consecutive frames into segments
            segments = []
            if len(times) > 0:
                segment_start = times[0]
                prev_time = times[0]
                
                for time in times[1:]:
                    if time - prev_time > 2.0:  # Gap of 2+ seconds
                        # End current segment
                        segments.append({
                            'start_time': segment_start,
                            'end_time': prev_time,
                            'duration': prev_time - segment_start,
                            'energy_score': float(np.mean(rms[
                                librosa.time_to_frames(segment_start, sr=sr, hop_length=hop_length):
                                librosa.time_to_frames(prev_time, sr=sr, hop_length=hop_length)
                            ]))
                        })
                        segment_start = time
                    prev_time = time
                
                # Add final segment
                if prev_time > segment_start:
                    segments.append({
                        'start_time': segment_start,
                        'end_time': prev_time,
                        'duration': prev_time - segment_start,
                        'energy_score': float(np.mean(rms[
                            librosa.time_to_frames(segment_start, sr=sr, hop_length=hop_length):
                            librosa.time_to_frames(prev_time, sr=sr, hop_length=hop_length)
                        ]))
                    })
            
            analysis = {
                'duration': duration,
                'sample_rate': sr,
                'tempo': float(tempo),
                'spectral_centroid_mean': float(np.mean(spectral_centroids)),
                'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
                'zero_crossing_rate_mean': float(np.mean(zero_crossing_rate)),
                'rms_energy_mean': float(np.mean(rms)),
                'rms_energy_std': float(np.std(rms)),
                'high_energy_segments': segments,
                'mfcc_features': mfccs.tolist() if mfccs.size < 1000 else mfccs[:, :100].tolist(),
                'analysis_type': 'advanced'
            }
            
            logger.info(f"Advanced analysis complete: {len(segments)} high-energy segments found")
            return analysis
            
        except Exception as e:
            logger.error(f"Advanced audio analysis failed: {e}")
            return {'analysis_type': 'failed', 'error': str(e)}
    
    def intelligent_segment_selection(self, analysis: Dict, target_segments: int = 5, 
                                    min_duration: float = 10.0, max_duration: float = 30.0) -> List[Dict]:
        """Intelligent segment selection based on audio analysis"""
        try:
            high_energy_segments = analysis.get('high_energy_segments', [])
            duration = analysis.get('duration', 3600)
            
            # Filter segments by duration
            valid_segments = [
                seg for seg in high_energy_segments 
                if min_duration <= seg['duration'] <= max_duration
            ]
            
            if len(valid_segments) >= target_segments:
                # Sort by energy score and select top segments
                valid_segments.sort(key=lambda x: x['energy_score'], reverse=True)
                selected = valid_segments[:target_segments]
                
                # Add metadata
                for i, seg in enumerate(selected):
                    seg.update({
                        'name': f'High Energy Segment {i + 1}',
                        'timestamp': seg['start_time'],
                        'description': f'Energy score: {seg["energy_score"]:.3f}',
                        'confidence': 0.9,
                        'selection_method': 'energy_based'
                    })
                
            else:
                # Fallback: create evenly distributed segments
                selected = self.create_distributed_segments(duration, target_segments, min_duration)
            
            # Sort by timestamp
            selected.sort(key=lambda x: x['timestamp'])
            return selected
            
        except Exception as e:
            logger.error(f"Segment selection failed: {e}")
            return self.create_distributed_segments(
                analysis.get('duration', 3600), target_segments, min_duration
            )
    
    def create_distributed_segments(self, duration: float, count: int, min_duration: float) -> List[Dict]:
        """Create evenly distributed segments as fallback"""
        segments = []
        segment_gap = duration / (count + 1)
        
        for i in range(count):
            start_time = (i + 1) * segment_gap - min_duration / 2
            start_time = max(0, min(duration - min_duration, start_time))
            
            segments.append({
                'name': f'Distributed Segment {i + 1}',
                'timestamp': start_time,
                'duration': min_duration,
                'description': f'Evenly distributed segment {i + 1}',
                'confidence': 0.6,
                'selection_method': 'distributed'
            })
        
        return segments
    
    def apply_professional_processing(self, audio: AudioSegment, theme: str) -> AudioSegment:
        """Apply professional audio processing chain"""
        try:
            settings = self.processing_chains.get(theme, self.processing_chains['Best Of'])
            
            logger.info(f"Applying {theme} processing chain")
            
            # Step 1: Normalize input
            processed = normalize(audio)
            
            # Step 2: EQ simulation using high/low pass filters and gain adjustments
            # Low frequency adjustment
            if settings['eq_low_gain'] != 1.0:
                low_gain_db = 20 * np.log10(settings['eq_low_gain'])
                processed = processed.low_pass_filter(3000).apply_gain(low_gain_db) + \
                           processed.high_pass_filter(3000)
            
            # High frequency adjustment  
            if settings['eq_high_gain'] != 1.0:
                high_gain_db = 20 * np.log10(settings['eq_high_gain'])
                processed = processed.high_pass_filter(2000).apply_gain(high_gain_db) + \
                           processed.low_pass_filter(2000)
            
            # Step 3: Dynamic range compression
            processed = compress_dynamic_range(
                processed,
                threshold=settings['compression_threshold'],
                ratio=settings['compression_ratio'],
                attack=5.0,  # ms
                release=50.0  # ms
            )
            
            # Step 4: Final limiting to prevent clipping
            if processed.max_dBFS > settings['limiter_threshold']:
                limit_gain = settings['limiter_threshold'] - processed.max_dBFS
                processed = processed.apply_gain(limit_gain)
            
            # Step 5: Final normalize
            processed = normalize(processed)
            
            logger.info(f"Applied {theme} processing: {settings['description']}")
            return processed
            
        except Exception as e:
            logger.error(f"Professional processing failed: {e}")
            return audio
    
    def create_professional_mix(self, audio_data: np.ndarray, sr: int, segments: List[Dict], 
                              theme: str = "Best Of") -> Optional[str]:
        """Create professional mix from segments"""
        try:
            logger.info(f"Creating professional mix with {len(segments)} segments")
            
            # Convert numpy array to temporary file for PyDub
            temp_input = os.path.join(self.temp_dir, "input_audio.wav")
            sf.write(temp_input, audio_data, sr)
            
            # Load as AudioSegment
            full_audio = AudioSegment.from_file(temp_input)
            
            mix_segments = []
            
            # Add intro (silence for now, could be AI-generated music)
            intro = AudioSegment.silent(duration=2000)  # 2 seconds
            mix_segments.append(intro)
            
            # Process each segment
            for i, segment in enumerate(segments):
                logger.info(f"Processing segment {i+1}: {segment['name']}")
                
                # Extract segment
                start_ms = int(segment['timestamp'] * 1000)
                duration_ms = int(segment.get('duration', 20) * 1000)
                end_ms = start_ms + duration_ms
                
                if start_ms < len(full_audio) and end_ms <= len(full_audio):
                    segment_audio = full_audio[start_ms:end_ms]
                    
                    # Apply professional processing
                    processed_segment = self.apply_professional_processing(segment_audio, theme)
                    
                    # Add crossfades
                    if len(mix_segments) > 1:
                        # Crossfade with previous segment
                        processed_segment = processed_segment.fade_in(500)
                    
                    processed_segment = processed_segment.fade_out(500)
                    
                    mix_segments.append(processed_segment)
                    
                    # Add gap between segments
                    if i < len(segments) - 1:
                        gap = AudioSegment.silent(duration=1000)  # 1 second
                        mix_segments.append(gap)
            
            # Add outro
            outro = AudioSegment.silent(duration=3000)  # 3 seconds
            mix_segments.append(outro)
            
            # Combine all segments
            if not mix_segments:
                logger.error("No segments to mix")
                return None
            
            logger.info("Combining segments...")
            final_mix = sum(mix_segments)
            
            # Apply final master processing
            final_mix = self.apply_professional_processing(final_mix, theme)
            
            # Export
            output_path = self.export_professional_mix(final_mix, theme)
            logger.info(f"Professional mix created: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Professional mix creation failed: {e}")
            return None
    
    def export_professional_mix(self, audio: AudioSegment, theme: str) -> str:
        """Export the final mix with professional settings"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
            
            output_path = os.path.join(
                self.temp_dir, 
                f'Professional_NoAgenda_{safe_theme}_{timestamp}.mp3'
            )
            
            # Export with high quality settings
            audio.export(
                output_path, 
                format='mp3',
                bitrate='320k',  # High quality
                parameters=[
                    '-ar', str(self.sample_rate),  # Sample rate
                    '-ac', '2',  # Stereo
                    '-q:a', '0'  # Best quality
                ]
            )
            
            logger.info(f"Exported professional mix: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return ""
    
    def stream_export_professional_mix(self, audio: AudioSegment, theme: str, s3_manager, episode_number: int) -> Optional[Dict]:
        """Stream export directly to S3 without temp files"""
        try:
            import io
            import uuid
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
            
            # Create S3 key
            mix_key = f"mixes/{episode_number}/Professional_NoAgenda_{safe_theme}_{timestamp}.mp3"
            
            # Stream to S3 using BytesIO buffer
            with io.BytesIO() as buf:
                # Export to buffer
                audio.export(
                    buf, 
                    format='mp3',
                    bitrate='320k',  # High quality
                    parameters=[
                        '-ar', str(self.sample_rate),  # Sample rate
                        '-ac', '2',  # Stereo
                        '-q:a', '0'  # Best quality
                    ]
                )
                
                # Get buffer size
                buf.seek(0, 2)  # Seek to end
                file_size = buf.tell()
                buf.seek(0)  # Reset to beginning
                
                # Upload to S3
                s3_manager.s3_client.upload_fileobj(
                    buf,
                    s3_manager.bucket_name,
                    mix_key,
                    ExtraArgs={'ContentType': 'audio/mpeg'}
                )
                
                logger.info(f"Streamed professional mix to S3: {mix_key}")
                
                # Generate presigned URL
                download_url = s3_manager.generate_presigned_url(mix_key, expiration=86400)
                
                return {
                    's3_key': mix_key,
                    'download_url': download_url,
                    'bucket': s3_manager.bucket_name,
                    'file_size': file_size
                }
                
        except Exception as e:
            logger.error(f"Stream export failed: {e}")
            return None
    
    def batch_process_segments(self, audio_data: np.ndarray, sr: int, 
                             segments: List[Dict], theme: str) -> List[AudioSegment]:
        """Process multiple segments in parallel"""
        try:
            # Save audio to temp file for PyDub
            temp_input = os.path.join(self.temp_dir, "batch_input.wav")
            sf.write(temp_input, audio_data, sr)
            full_audio = AudioSegment.from_file(temp_input)
            
            def process_single_segment(segment_info):
                i, segment = segment_info
                try:
                    start_ms = int(segment['timestamp'] * 1000)
                    duration_ms = int(segment.get('duration', 20) * 1000)
                    end_ms = start_ms + duration_ms
                    
                    if start_ms < len(full_audio) and end_ms <= len(full_audio):
                        segment_audio = full_audio[start_ms:end_ms]
                        processed = self.apply_professional_processing(segment_audio, theme)
                        return (i, processed)
                    return (i, None)
                except Exception as e:
                    logger.error(f"Failed to process segment {i}: {e}")
                    return (i, None)
            
            # Process segments in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(process_single_segment, enumerate(segments)))
            
            # Sort results by index and filter out None values
            processed_segments = []
            for i, processed in sorted(results):
                if processed:
                    processed_segments.append(processed)
            
            return processed_segments
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return []
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Utility functions
def create_audio_processor(sample_rate: int = 44100) -> ProfessionalAudioProcessor:
    """Create configured audio processor"""
    return ProfessionalAudioProcessor(sample_rate=sample_rate)

def quick_analyze_audio(url: str) -> Optional[Dict]:
    """Quick audio analysis utility"""
    processor = create_audio_processor()
    try:
        audio_data, sr = processor.load_audio_from_url(url)
        if audio_data is not None:
            return processor.analyze_audio_advanced(audio_data, sr)
        return None
    finally:
        processor.cleanup()
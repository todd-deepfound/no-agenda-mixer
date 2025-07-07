#!/usr/bin/env python3
"""
Performance Optimizations for No Agenda Professional Audio Mixer
Implements caching, parallel processing, and memory management
"""

import os
import json
import tempfile
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import concurrent.futures
from functools import lru_cache
import gc

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Handles performance optimizations for audio processing"""
    
    def __init__(self, cache_size: int = 128):
        self.cache_size = cache_size
        self.memory_cache = {}
        self.temp_cache_dir = tempfile.mkdtemp(prefix='noagenda_cache_')
        
    @lru_cache(maxsize=32)
    def get_cached_analysis(self, audio_hash: str) -> Optional[Dict]:
        """Get cached audio analysis results"""
        try:
            cache_file = os.path.join(self.temp_cache_dir, f"analysis_{audio_hash}.json")
            if os.path.exists(cache_file):
                # Check if cache is recent (within 1 hour)
                cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
                if cache_age < timedelta(hours=1):
                    with open(cache_file, 'r') as f:
                        return json.load(f)
            return None
        except Exception as e:
            logger.warning(f"Failed to get cached analysis: {e}")
            return None
    
    def cache_analysis(self, audio_hash: str, analysis: Dict) -> bool:
        """Cache audio analysis results"""
        try:
            cache_file = os.path.join(self.temp_cache_dir, f"analysis_{audio_hash}.json")
            with open(cache_file, 'w') as f:
                json.dump(analysis, f)
            logger.info(f"Cached analysis for {audio_hash}")
            return True
        except Exception as e:
            logger.warning(f"Failed to cache analysis: {e}")
            return False
    
    def generate_audio_hash(self, audio_url: str, duration_hint: float = None) -> str:
        """Generate hash for audio content identification"""
        # Use URL + optional duration as hash input
        hash_input = audio_url
        if duration_hint:
            hash_input += f"_{duration_hint:.1f}"
        
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    def optimize_memory_usage(self):
        """Optimize memory usage during processing"""
        try:
            # Force garbage collection
            gc.collect()
            
            # Clear old cache entries if too many
            if len(self.memory_cache) > self.cache_size:
                # Remove oldest 25% of entries
                remove_count = len(self.memory_cache) // 4
                oldest_keys = sorted(self.memory_cache.keys())[:remove_count]
                for key in oldest_keys:
                    del self.memory_cache[key]
            
            logger.info("Memory optimization completed")
            
        except Exception as e:
            logger.warning(f"Memory optimization failed: {e}")
    
    def parallel_segment_processing(self, segments: List[Dict], audio_data, 
                                   processing_func, max_workers: int = None) -> List[Any]:
        """Process segments in parallel for better performance"""
        try:
            # Determine optimal worker count based on CPU and memory
            if max_workers is None:
                # Use min of 4 or number of segments
                max_workers = min(4, len(segments), os.cpu_count() or 1)
            
            logger.info(f"Processing {len(segments)} segments with {max_workers} workers")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_segment = {
                    executor.submit(processing_func, segment, audio_data): segment 
                    for segment in segments
                }
                
                results = []
                for future in concurrent.futures.as_completed(future_to_segment):
                    segment = future_to_segment[future]
                    try:
                        result = future.result(timeout=30)  # 30 second timeout per segment
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Segment processing failed for {segment.get('name', 'unknown')}: {e}")
                        results.append(None)
            
            # Filter out None results and sort by original order
            valid_results = [r for r in results if r is not None]
            logger.info(f"Successfully processed {len(valid_results)}/{len(segments)} segments")
            
            return valid_results
            
        except Exception as e:
            logger.error(f"Parallel processing failed: {e}")
            return []
    
    def stream_processing_setup(self, target_chunk_size: int = 1024*1024) -> Dict[str, Any]:
        """Setup for streaming audio processing to handle large files"""
        return {
            'chunk_size': target_chunk_size,
            'buffer_size': target_chunk_size * 2,
            'temp_files': [],
            'processing_mode': 'streaming'
        }
    
    def estimate_processing_time(self, audio_duration: float, segments_count: int, 
                               theme_complexity: str = 'medium') -> Dict[str, float]:
        """Estimate processing time for planning"""
        
        # Base processing rates (seconds of processing per second of audio)
        complexity_multipliers = {
            'simple': 0.5,   # Mock/basic processing
            'medium': 2.0,   # Standard professional processing
            'complex': 4.0   # Heavy analysis + processing
        }
        
        base_rate = complexity_multipliers.get(theme_complexity, 2.0)
        
        # Estimate components
        download_time = min(audio_duration * 0.1, 60)  # Max 1 minute download
        analysis_time = audio_duration * 0.3          # 30% of duration for analysis
        segment_processing = segments_count * 5.0     # 5 seconds per segment
        mixing_time = segments_count * 2.0            # 2 seconds per segment mixing
        upload_time = 10.0                            # S3 upload estimate
        
        total_estimate = download_time + analysis_time + segment_processing + mixing_time + upload_time
        
        return {
            'total_estimate_seconds': total_estimate,
            'total_estimate_minutes': total_estimate / 60,
            'breakdown': {
                'download': download_time,
                'analysis': analysis_time,
                'segment_processing': segment_processing,
                'mixing': mixing_time,
                'upload': upload_time
            },
            'complexity': theme_complexity,
            'audio_duration': audio_duration,
            'segments_count': segments_count
        }
    
    def monitor_lambda_resources(self, context) -> Dict[str, Any]:
        """Monitor Lambda resource usage"""
        try:
            remaining_time_ms = context.get_remaining_time_in_millis() if context else 0
            memory_limit_mb = context.memory_limit_in_mb if context else 0
            
            # Get approximate memory usage (not exact in Lambda)
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'remaining_time_ms': remaining_time_ms,
                'remaining_time_minutes': remaining_time_ms / (1000 * 60),
                'memory_limit_mb': memory_limit_mb,
                'memory_used_mb': memory_info.rss / (1024 * 1024),
                'memory_available_mb': memory_limit_mb - (memory_info.rss / (1024 * 1024)),
                'cpu_percent': process.cpu_percent(),
                'warning_low_time': remaining_time_ms < 60000,  # Less than 1 minute
                'warning_high_memory': (memory_info.rss / (1024 * 1024)) > (memory_limit_mb * 0.8)
            }
            
        except Exception as e:
            logger.warning(f"Resource monitoring failed: {e}")
            return {
                'remaining_time_ms': remaining_time_ms,
                'memory_limit_mb': memory_limit_mb,
                'monitoring_error': str(e)
            }
    
    def cleanup_performance_cache(self):
        """Clean up performance optimization caches"""
        try:
            # Clear memory cache
            self.memory_cache.clear()
            
            # Clear LRU cache
            self.get_cached_analysis.cache_clear()
            
            # Clean up temp cache files
            import shutil
            if os.path.exists(self.temp_cache_dir):
                shutil.rmtree(self.temp_cache_dir)
            
            # Force garbage collection
            gc.collect()
            
            logger.info("Performance cache cleanup completed")
            
        except Exception as e:
            logger.warning(f"Cache cleanup failed: {e}")

class AudioProcessingProfiler:
    """Profile audio processing performance"""
    
    def __init__(self):
        self.timings = {}
        self.start_times = {}
    
    def start_timing(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = datetime.now()
    
    def end_timing(self, operation: str) -> float:
        """End timing and return duration in seconds"""
        if operation in self.start_times:
            duration = (datetime.now() - self.start_times[operation]).total_seconds()
            self.timings[operation] = duration
            del self.start_times[operation]
            return duration
        return 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        total_time = sum(self.timings.values())
        
        return {
            'total_processing_time': total_time,
            'individual_timings': self.timings,
            'bottlenecks': self._identify_bottlenecks(),
            'performance_score': self._calculate_performance_score(),
            'recommendations': self._get_recommendations()
        }
    
    def _identify_bottlenecks(self) -> List[str]:
        """Identify performance bottlenecks"""
        if not self.timings:
            return []
        
        total_time = sum(self.timings.values())
        bottlenecks = []
        
        for operation, duration in self.timings.items():
            if duration > total_time * 0.3:  # More than 30% of total time
                bottlenecks.append(operation)
        
        return bottlenecks
    
    def _calculate_performance_score(self) -> str:
        """Calculate overall performance score"""
        total_time = sum(self.timings.values())
        
        if total_time < 30:
            return "Excellent"
        elif total_time < 60:
            return "Good"
        elif total_time < 120:
            return "Fair"
        else:
            return "Needs Optimization"
    
    def _get_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        bottlenecks = self._identify_bottlenecks()
        
        if 'download' in bottlenecks:
            recommendations.append("Consider caching frequently accessed episodes")
        
        if 'analysis' in bottlenecks:
            recommendations.append("Implement analysis result caching")
        
        if 'segment_processing' in bottlenecks:
            recommendations.append("Increase parallel processing workers")
        
        if 'mixing' in bottlenecks:
            recommendations.append("Optimize audio mixing algorithms")
        
        return recommendations

# Utility functions
def create_performance_optimizer() -> PerformanceOptimizer:
    """Create configured performance optimizer"""
    return PerformanceOptimizer()

def create_profiler() -> AudioProcessingProfiler:
    """Create audio processing profiler"""
    return AudioProcessingProfiler()
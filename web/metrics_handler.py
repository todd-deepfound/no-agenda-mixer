#!/usr/bin/env python3
"""
Metrics Handler for No Agenda Mixer Production
Emits CloudWatch EMF metrics for monitoring
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class MetricsEmitter:
    """Emit metrics in CloudWatch EMF format"""
    
    def __init__(self, namespace: str = "NoAgendaMixer"):
        self.namespace = namespace
        self.metrics = {}
        self.properties = {}
        self.dimensions = {}
    
    def add_metric(self, name: str, value: float, unit: str = "None"):
        """Add a metric to emit"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "Value": value,
            "Unit": unit
        })
    
    def add_property(self, name: str, value: Any):
        """Add a property to the metrics"""
        self.properties[name] = value
    
    def add_dimension(self, name: str, value: str):
        """Add a dimension to the metrics"""
        self.dimensions[name] = value
    
    def emit(self) -> Dict[str, Any]:
        """Emit metrics in EMF format"""
        metric_definitions = []
        for metric_name, metric_values in self.metrics.items():
            for metric in metric_values:
                metric_definitions.append({
                    "Name": metric_name,
                    "Unit": metric["Unit"]
                })
        
        emf_output = {
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [{
                    "Namespace": self.namespace,
                    "Dimensions": [list(self.dimensions.keys())] if self.dimensions else [],
                    "Metrics": metric_definitions
                }]
            }
        }
        
        # Add dimensions
        emf_output.update(self.dimensions)
        
        # Add metric values
        for metric_name, metric_values in self.metrics.items():
            if metric_values:
                emf_output[metric_name] = metric_values[0]["Value"]
        
        # Add properties
        emf_output.update(self.properties)
        
        # Print to stdout for CloudWatch to capture
        print(json.dumps(emf_output))
        
        return emf_output

class ProcessingMetrics:
    """Track and emit processing metrics"""
    
    def __init__(self):
        self.start_times = {}
        self.emitter = MetricsEmitter()
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """End timing and emit metric"""
        if operation in self.start_times:
            duration_ms = (time.time() - self.start_times[operation]) * 1000
            self.emitter.add_metric(f"{operation}_ms", duration_ms, "Milliseconds")
            del self.start_times[operation]
            return duration_ms
        return 0
    
    def track_mix_creation(self, theme: str, segments_count: int, 
                          audio_duration: float, file_size_bytes: int):
        """Track mix creation metrics"""
        self.emitter.add_dimension("Theme", theme)
        self.emitter.add_metric("segments_processed", segments_count, "Count")
        self.emitter.add_metric("audio_duration_seconds", audio_duration, "Seconds")
        self.emitter.add_metric("file_size_mb", file_size_bytes / (1024 * 1024), "Megabytes")
        self.emitter.add_property("theme", theme)
        self.emitter.add_property("segments_count", segments_count)
    
    def track_error(self, error_type: str, error_message: str):
        """Track error metrics"""
        self.emitter.add_metric("error_count", 1, "Count")
        self.emitter.add_property("error_type", error_type)
        self.emitter.add_property("error_message", error_message[:200])  # Truncate long messages
    
    def track_api_latency(self, api_name: str, latency_ms: float):
        """Track external API latency"""
        self.emitter.add_metric(f"{api_name}_latency_ms", latency_ms, "Milliseconds")
    
    def emit_metrics(self):
        """Emit all collected metrics"""
        return self.emitter.emit()

def lambda_handler(event, context):
    """Lambda handler for metrics endpoint"""
    try:
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
        
        # Get current metrics from CloudWatch Insights
        metrics_summary = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'description': 'Metrics are emitted to CloudWatch in EMF format',
                'namespace': 'NoAgendaMixer',
                'dimensions': ['Theme', 'Stage', 'Function'],
                'available_metrics': [
                    'transcribe_ms',
                    'mix_ms',
                    'bytes_uploaded',
                    'segments_processed',
                    'audio_duration_seconds',
                    'file_size_mb',
                    'error_count',
                    'api_latency_ms'
                ],
                'cloudwatch_insights_query': '''
                    fields @timestamp, theme, segments_processed, mix_ms, file_size_mb
                    | filter @type = "REPORT"
                    | stats avg(mix_ms) as avg_mix_time,
                            count() as total_mixes,
                            sum(segments_processed) as total_segments
                    by bin(5m)
                '''
            },
            'recent_stats': {
                'note': 'Run CloudWatch Insights query for detailed metrics',
                'dashboard_url': f'https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights'
            }
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(metrics_summary, indent=2)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

# Example usage in main processing function:
def track_processing_metrics(metrics: ProcessingMetrics, operation: str):
    """Decorator to track operation metrics"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            metrics.start_timer(operation)
            try:
                result = func(*args, **kwargs)
                metrics.end_timer(operation)
                return result
            except Exception as e:
                metrics.end_timer(operation)
                metrics.track_error(operation, str(e))
                raise
        return wrapper
    return decorator
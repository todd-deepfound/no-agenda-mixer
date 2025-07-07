#!/usr/bin/env python3
"""
S3 Manager for No Agenda Professional Audio Mixer
Handles file uploads, downloads, and presigned URL generation
"""

import boto3
import json
import os
import tempfile
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class S3Manager:
    """Handles S3 operations for audio files and mix outputs"""
    
    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or os.environ.get('S3_BUCKET', 'noagenda-mixer-storage')
        self.s3_client = boto3.client('s3')
        
        # S3 prefixes for organization
        self.prefixes = {
            'episodes': 'raw/episodes/',
            'clips': 'processed/clips/',
            'mixes': 'output/mixes/',
            'temp': 'temp/'
        }
    
    def ensure_bucket_exists(self) -> bool:
        """Ensure the S3 bucket exists, create if necessary"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket {self.bucket_name} exists")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created S3 bucket {self.bucket_name}")
                    return True
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    return False
            else:
                logger.error(f"Error checking bucket: {e}")
                return False
    
    def upload_file(self, local_path: str, s3_key: str, content_type: str = None) -> bool:
        """Upload a file to S3"""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_file(
                local_path, 
                self.bucket_name, 
                s3_key,
                ExtraArgs=extra_args
            )
            logger.info(f"Uploaded {local_path} to s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """Download a file from S3"""
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download {s3_key}: {e}")
            return False
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 86400) -> Optional[str]:
        """Generate a presigned URL for downloading a file"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            logger.info(f"Generated presigned URL for {s3_key}")
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            return None
    
    def upload_mix_file(self, local_path: str, episode_number: int, theme: str) -> Optional[Dict[str, Any]]:
        """Upload a mix file and return metadata"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
            
            # Create S3 key
            s3_key = f"{self.prefixes['mixes']}NA{episode_number}/{safe_theme}_{timestamp}.mp3"
            
            # Upload file
            if self.upload_file(local_path, s3_key, 'audio/mpeg'):
                # Generate presigned URL
                download_url = self.generate_presigned_url(s3_key)
                
                return {
                    's3_key': s3_key,
                    'download_url': download_url,
                    'bucket': self.bucket_name,
                    'episode_number': episode_number,
                    'theme': theme,
                    'timestamp': timestamp,
                    'file_size': os.path.getsize(local_path)
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to upload mix file: {e}")
            return None
    
    def upload_episode_cache(self, local_path: str, episode_url: str) -> Optional[str]:
        """Upload an episode file to cache for reuse"""
        try:
            # Extract episode number from URL or use hash
            import hashlib
            url_hash = hashlib.md5(episode_url.encode()).hexdigest()[:8]
            s3_key = f"{self.prefixes['episodes']}cached_{url_hash}.mp3"
            
            if self.upload_file(local_path, s3_key, 'audio/mpeg'):
                return s3_key
            return None
            
        except Exception as e:
            logger.error(f"Failed to upload episode cache: {e}")
            return None
    
    def download_episode_cache(self, episode_url: str, local_path: str) -> bool:
        """Download cached episode if available"""
        try:
            import hashlib
            url_hash = hashlib.md5(episode_url.encode()).hexdigest()[:8]
            s3_key = f"{self.prefixes['episodes']}cached_{url_hash}.mp3"
            
            return self.download_file(s3_key, local_path)
            
        except Exception as e:
            logger.error(f"Failed to download episode cache: {e}")
            return False
    
    def stream_upload(self, file_obj, s3_key: str, content_type: str = None) -> bool:
        """Upload file object directly to S3 without saving to disk"""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            logger.info(f"Streamed upload to s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to stream upload to {s3_key}: {e}")
            return False
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        try:
            from datetime import timezone
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefixes['temp']
            )
            
            if 'Contents' in response:
                delete_keys = []
                for obj in response['Contents']:
                    if obj['LastModified'] < cutoff_time:
                        delete_keys.append({'Key': obj['Key']})
                
                if delete_keys:
                    self.s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={'Objects': delete_keys}
                    )
                    logger.info(f"Cleaned up {len(delete_keys)} temporary files")
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
    
    def get_mix_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a mix file"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {})
            }
        except Exception as e:
            logger.error(f"Failed to get metadata for {s3_key}: {e}")
            return None
    
    def list_mixes(self, episode_number: int = None) -> list:
        """List available mixes, optionally filtered by episode"""
        try:
            prefix = self.prefixes['mixes']
            if episode_number:
                prefix += f"NA{episode_number}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            mixes = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    mixes.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'download_url': self.generate_presigned_url(obj['Key'])
                    })
            
            return mixes
            
        except Exception as e:
            logger.error(f"Failed to list mixes: {e}")
            return []

# Utility functions for Lambda environment
def get_s3_manager() -> S3Manager:
    """Get configured S3Manager instance"""
    bucket_name = os.environ.get('S3_BUCKET', 'noagenda-mixer-storage')
    return S3Manager(bucket_name)

def upload_temp_file_to_s3(temp_file_path: str, filename: str) -> Optional[Dict[str, Any]]:
    """Quick utility to upload temp file to S3"""
    s3_manager = get_s3_manager()
    s3_key = f"{s3_manager.prefixes['temp']}{filename}"
    
    if s3_manager.upload_file(temp_file_path, s3_key, 'audio/mpeg'):
        return {
            's3_key': s3_key,
            'download_url': s3_manager.generate_presigned_url(s3_key),
            'bucket': s3_manager.bucket_name
        }
    return None
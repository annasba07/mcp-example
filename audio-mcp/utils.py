import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import base64

logger = logging.getLogger(__name__)

class AudioUtils:
    """Utility functions for audio processing"""
    
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma']
    
    @staticmethod
    def validate_audio_file(file_path: str) -> bool:
        """Validate if file exists and has supported audio format"""
        if not os.path.exists(file_path):
            return False
            
        file_ext = Path(file_path).suffix.lower()
        return file_ext in AudioUtils.SUPPORTED_FORMATS
    
    @staticmethod
    def get_temp_filepath(suffix: str = '.wav') -> str:
        """Generate a temporary file path with given suffix"""
        temp_dir = tempfile.gettempdir()
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, dir=temp_dir)
        temp_file.close()
        return temp_file.name
    
    @staticmethod
    def decode_base64_audio(audio_data: str, output_path: str) -> str:
        """Decode base64 audio data and save to file"""
        try:
            audio_bytes = base64.b64decode(audio_data)
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            return output_path
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            raise ValueError(f"Invalid base64 audio data: {e}")
    
    @staticmethod
    def encode_audio_to_base64(file_path: str) -> str:
        """Encode audio file to base64 string"""
        try:
            with open(file_path, 'rb') as f:
                audio_bytes = f.read()
            return base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode audio to base64: {e}")
            raise ValueError(f"Failed to encode audio file: {e}")
    
    @staticmethod
    def cleanup_temp_file(file_path: str) -> None:
        """Safely remove temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    @staticmethod
    def get_audio_metadata(file_path: str) -> Dict[str, Any]:
        """Extract basic metadata from audio file"""
        try:
            from mutagen import File
            
            audio_file = File(file_path)
            if audio_file is None:
                return {"error": "Unable to read audio file"}
            
            info = audio_file.info
            metadata = {
                "duration": info.length if hasattr(info, 'length') else 0,
                "bitrate": info.bitrate if hasattr(info, 'bitrate') else 0,
                "sample_rate": info.bitrate if hasattr(info, 'bitrate') else 0,
                "channels": info.channels if hasattr(info, 'channels') else 0,
                "format": Path(file_path).suffix.lower()[1:],
                "file_size": os.path.getsize(file_path)
            }
            
            # Add tags if available
            if audio_file.tags:
                tags = {}
                for key, value in audio_file.tags.items():
                    tags[key] = str(value[0]) if isinstance(value, list) else str(value)
                metadata["tags"] = tags
            
            return metadata
            
        except ImportError:
            logger.warning("mutagen not installed, returning basic metadata")
            return {
                "file_size": os.path.getsize(file_path),
                "format": Path(file_path).suffix.lower()[1:],
                "error": "mutagen not installed for detailed metadata"
            }
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            return {"error": str(e)}
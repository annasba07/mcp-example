import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import tempfile
import asyncio
from pydub import AudioSegment
from .utils import AudioUtils

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Core audio processing functionality"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.temp_files: List[str] = []
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
        
        logger.info(f"AudioProcessor initialized with temp_dir: {self.temp_dir}")
    
    def _register_temp_file(self, file_path: str) -> str:
        """Register a temporary file for cleanup"""
        self.temp_files.append(file_path)
        return file_path
    
    def cleanup(self):
        """Clean up all temporary files"""
        for file_path in self.temp_files:
            AudioUtils.cleanup_temp_file(file_path)
        self.temp_files.clear()
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive audio file information"""
        if not AudioUtils.validate_audio_file(file_path):
            return {"error": "Invalid or unsupported audio file"}
        
        try:
            # Get metadata using mutagen
            metadata = AudioUtils.get_audio_metadata(file_path)
            
            # Get additional info using pydub
            audio = AudioSegment.from_file(file_path)
            
            info = {
                "file_path": file_path,
                "duration_seconds": len(audio) / 1000.0,
                "duration_formatted": AudioUtils.format_duration(len(audio) / 1000.0),
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "format": Path(file_path).suffix.lower()[1:],
                "file_size_bytes": os.path.getsize(file_path),
                "file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2),
                "frame_count": len(audio),
                "sample_width": audio.sample_width,
                "max_possible_amplitude": audio.max_possible_amplitude
            }
            
            # Merge with metadata
            info.update(metadata)
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            return {"error": str(e)}
    
    def convert_format(self, input_path: str, output_format: str, quality: str = "medium") -> Dict[str, Any]:
        """Convert audio file to different format"""
        if not AudioUtils.validate_audio_file(input_path):
            return {"error": "Invalid or unsupported input audio file"}
        
        if not output_format.startswith('.'):
            output_format = f".{output_format}"
        
        if output_format.lower() not in AudioUtils.SUPPORTED_FORMATS:
            return {"error": f"Unsupported output format: {output_format}"}
        
        try:
            # Load audio
            audio = AudioSegment.from_file(input_path)
            
            # Generate output path
            input_name = Path(input_path).stem
            output_path = os.path.join(self.temp_dir, f"{input_name}_converted{output_format}")
            output_path = self._register_temp_file(output_path)
            
            # Set quality parameters
            export_params = {}
            if output_format.lower() == '.mp3':
                if quality == "high":
                    export_params["bitrate"] = "320k"
                elif quality == "medium":
                    export_params["bitrate"] = "192k"
                elif quality == "low":
                    export_params["bitrate"] = "128k"
            
            # Export with format
            audio.export(output_path, format=output_format[1:], **export_params)
            
            # Get info about converted file
            result = {
                "status": "success",
                "output_path": output_path,
                "input_format": Path(input_path).suffix.lower()[1:],
                "output_format": output_format[1:],
                "quality": quality,
                "original_size_mb": round(os.path.getsize(input_path) / (1024 * 1024), 2),
                "converted_size_mb": round(os.path.getsize(output_path) / (1024 * 1024), 2)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            return {"error": str(e)}
    
    def trim_audio(self, input_path: str, start_seconds: float, end_seconds: Optional[float] = None) -> Dict[str, Any]:
        """Trim audio file to specified time range"""
        if not AudioUtils.validate_audio_file(input_path):
            return {"error": "Invalid or unsupported audio file"}
        
        try:
            audio = AudioSegment.from_file(input_path)
            duration = len(audio) / 1000.0
            
            # Validate time range
            if start_seconds < 0 or start_seconds >= duration:
                return {"error": f"Invalid start time. Must be between 0 and {duration:.2f} seconds"}
            
            if end_seconds is not None and (end_seconds <= start_seconds or end_seconds > duration):
                return {"error": f"Invalid end time. Must be between {start_seconds:.2f} and {duration:.2f} seconds"}
            
            # Convert to milliseconds
            start_ms = int(start_seconds * 1000)
            end_ms = int(end_seconds * 1000) if end_seconds is not None else len(audio)
            
            # Trim audio
            trimmed_audio = audio[start_ms:end_ms]
            
            # Generate output path
            input_name = Path(input_path).stem
            input_ext = Path(input_path).suffix
            output_path = os.path.join(self.temp_dir, f"{input_name}_trimmed{input_ext}")
            output_path = self._register_temp_file(output_path)
            
            # Export trimmed audio
            trimmed_audio.export(output_path, format=input_ext[1:])
            
            result = {
                "status": "success",
                "output_path": output_path,
                "original_duration": AudioUtils.format_duration(duration),
                "trimmed_duration": AudioUtils.format_duration(len(trimmed_audio) / 1000.0),
                "start_time": AudioUtils.format_duration(start_seconds),
                "end_time": AudioUtils.format_duration(end_seconds) if end_seconds else "end of file"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error trimming audio: {e}")
            return {"error": str(e)}
    
    def merge_audio(self, input_paths: List[str], output_format: str = "wav") -> Dict[str, Any]:
        """Merge multiple audio files into one"""
        if not input_paths:
            return {"error": "No input files provided"}
        
        # Validate all input files
        for path in input_paths:
            if not AudioUtils.validate_audio_file(path):
                return {"error": f"Invalid or unsupported audio file: {path}"}
        
        try:
            # Load and combine audio files
            combined_audio = AudioSegment.empty()
            file_info = []
            
            for i, path in enumerate(input_paths):
                audio = AudioSegment.from_file(path)
                combined_audio += audio
                
                file_info.append({
                    "file": Path(path).name,
                    "duration": AudioUtils.format_duration(len(audio) / 1000.0),
                    "position": i + 1
                })
            
            # Generate output path
            if not output_format.startswith('.'):
                output_format = f".{output_format}"
            
            output_path = os.path.join(self.temp_dir, f"merged_audio{output_format}")
            output_path = self._register_temp_file(output_path)
            
            # Export merged audio
            combined_audio.export(output_path, format=output_format[1:])
            
            result = {
                "status": "success",
                "output_path": output_path,
                "merged_files": file_info,
                "total_files": len(input_paths),
                "total_duration": AudioUtils.format_duration(len(combined_audio) / 1000.0),
                "output_format": output_format[1:]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error merging audio files: {e}")
            return {"error": str(e)}
    
    async def transcribe_audio(self, file_path: str, model: str = "base") -> Dict[str, Any]:
        """Transcribe audio to text using Whisper (if available)"""
        if not AudioUtils.validate_audio_file(file_path):
            return {"error": "Invalid or unsupported audio file"}
        
        try:
            import whisper
            
            # Load model
            logger.info(f"Loading Whisper model: {model}")
            whisper_model = whisper.load_model(model)
            
            # Transcribe
            logger.info(f"Transcribing audio file: {file_path}")
            result = whisper_model.transcribe(file_path)
            
            response = {
                "status": "success",
                "transcript": result["text"],
                "language": result.get("language", "unknown"),
                "model_used": model,
                "file_path": file_path
            }
            
            # Add segments if available
            if "segments" in result:
                segments = []
                for segment in result["segments"]:
                    segments.append({
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": segment["text"]
                    })
                response["segments"] = segments
            
            return response
            
        except ImportError:
            return {
                "error": "Whisper not installed. Install with: pip install openai-whisper",
                "suggestion": "Run: pip install openai-whisper torch torchaudio"
            }
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return {"error": str(e)}
    
    async def generate_speech(self, text: str, output_format: str = "mp3", voice: str = "default") -> Dict[str, Any]:
        """Generate speech from text using TTS"""
        if not text.strip():
            return {"error": "No text provided"}
        
        try:
            from gtts import gTTS
            
            # Generate output path
            if not output_format.startswith('.'):
                output_format = f".{output_format}"
            
            output_path = os.path.join(self.temp_dir, f"generated_speech{output_format}")
            output_path = self._register_temp_file(output_path)
            
            # Generate speech
            logger.info(f"Generating speech for text: {text[:50]}...")
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save to temporary file first (gTTS saves as mp3)
            temp_mp3 = os.path.join(self.temp_dir, "temp_speech.mp3")
            tts.save(temp_mp3)
            
            # Convert to desired format if needed
            if output_format.lower() != '.mp3':
                audio = AudioSegment.from_mp3(temp_mp3)
                audio.export(output_path, format=output_format[1:])
                os.remove(temp_mp3)
            else:
                os.rename(temp_mp3, output_path)
            
            result = {
                "status": "success",
                "output_path": output_path,
                "text_length": len(text),
                "output_format": output_format[1:],
                "voice": voice
            }
            
            return result
            
        except ImportError:
            return {
                "error": "gTTS not installed. Install with: pip install gTTS",
                "suggestion": "Run: pip install gTTS"
            }
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return {"error": str(e)}
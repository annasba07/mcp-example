import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import tempfile
import asyncio
from pydub import AudioSegment
from utils import AudioUtils

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
    
    async def diarize_speakers(self, file_path: str) -> Dict[str, Any]:
        """Perform speaker diarization to identify who spoke when"""
        if not AudioUtils.validate_audio_file(file_path):
            return {"error": "Invalid or unsupported audio file"}
        
        try:
            from pyannote.audio import Pipeline
            
            # Load the speaker diarization pipeline
            logger.info("Loading speaker diarization pipeline...")
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
            
            # Perform diarization
            logger.info(f"Performing speaker diarization on: {file_path}")
            diarization = pipeline(file_path)
            
            # Process results
            speakers = {}
            segments = []
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_id = f"Speaker_{speaker}"
                
                # Track speaker info
                if speaker_id not in speakers:
                    speakers[speaker_id] = {
                        "total_speaking_time": 0,
                        "segments": 0
                    }
                
                # Add segment
                segment_duration = turn.end - turn.start
                speakers[speaker_id]["total_speaking_time"] += segment_duration
                speakers[speaker_id]["segments"] += 1
                
                segments.append({
                    "start": round(turn.start, 2),
                    "end": round(turn.end, 2),
                    "duration": round(segment_duration, 2),
                    "speaker": speaker_id
                })
            
            # Sort segments by start time
            segments.sort(key=lambda x: x["start"])
            
            # Format speaker summary
            total_duration = max([seg["end"] for seg in segments]) if segments else 0
            
            for speaker_id in speakers:
                speakers[speaker_id]["total_speaking_time"] = round(speakers[speaker_id]["total_speaking_time"], 2)
                speakers[speaker_id]["percentage"] = round(
                    (speakers[speaker_id]["total_speaking_time"] / total_duration) * 100, 1
                ) if total_duration > 0 else 0
            
            result = {
                "status": "success",
                "file_path": file_path,
                "total_duration": round(total_duration, 2),
                "num_speakers": len(speakers),
                "speakers": speakers,
                "segments": segments,
                "total_segments": len(segments)
            }
            
            return result
            
        except ImportError:
            return {
                "error": "pyannote.audio not installed. Install with: pip install pyannote.audio",
                "suggestion": "Run: pip install pyannote.audio torch torchaudio"
            }
        except Exception as e:
            logger.error(f"Error performing speaker diarization: {e}")
            return {"error": str(e)}
    
    async def detect_emotions(self, file_path: str, api_key: str) -> Dict[str, Any]:
        """Detect emotions in audio using Hume AI API"""
        if not AudioUtils.validate_audio_file(file_path):
            return {"error": "Invalid or unsupported audio file"}
        
        if not api_key:
            return {"error": "Hume API key not provided"}
        
        try:
            import httpx
            import base64
            import json
            
            # Read and encode audio file
            with open(file_path, "rb") as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
            
            # Get file extension for mime type
            file_ext = Path(file_path).suffix.lower()
            mime_type_map = {
                '.wav': 'audio/wav',
                '.mp3': 'audio/mpeg',
                '.m4a': 'audio/mp4',
                '.flac': 'audio/flac',
                '.ogg': 'audio/ogg'
            }
            mime_type = mime_type_map.get(file_ext, 'audio/wav')
            
            # Prepare request payload
            payload = {
                "data": audio_data,
                "type": mime_type
            }
            
            headers = {
                "X-Hume-Api-Key": api_key,
                "Content-Type": "application/json"
            }
            
            # Make API request
            logger.info(f"Sending audio to Hume API for emotion detection...")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.hume.ai/v0/batch/jobs",
                    headers=headers,
                    json={
                        "models": {
                            "prosody": {}
                        },
                        "transcription": {
                            "identify_speakers": True
                        },
                        "notify": False,
                        "urls": [],
                        "files": [payload]
                    }
                )
                
                if response.status_code != 200:
                    return {"error": f"Hume API error: {response.status_code} - {response.text}"}
                
                job_data = response.json()
                job_id = job_data.get("job_id")
                
                if not job_id:
                    return {"error": "Failed to get job ID from Hume API"}
                
                # Poll for results
                max_attempts = 30
                for attempt in range(max_attempts):
                    await asyncio.sleep(2)  # Wait 2 seconds between polls
                    
                    status_response = await client.get(
                        f"https://api.hume.ai/v0/batch/jobs/{job_id}",
                        headers=headers
                    )
                    
                    if status_response.status_code != 200:
                        continue
                    
                    status_data = status_response.json()
                    state = status_data.get("state", {}).get("status")
                    
                    if state == "COMPLETED":
                        # Get results
                        results_response = await client.get(
                            f"https://api.hume.ai/v0/batch/jobs/{job_id}/predictions",
                            headers=headers
                        )
                        
                        if results_response.status_code == 200:
                            results = results_response.json()
                            return self._process_hume_results(results, file_path)
                        else:
                            return {"error": f"Failed to get results: {results_response.status_code}"}
                    
                    elif state == "FAILED":
                        return {"error": "Hume API job failed"}
                
                return {"error": "Timeout waiting for Hume API results"}
            
        except ImportError:
            return {
                "error": "httpx not installed. Install with: pip install httpx",
                "suggestion": "Run: pip install httpx"
            }
        except Exception as e:
            logger.error(f"Error detecting emotions: {e}")
            return {"error": str(e)}
    
    def _process_hume_results(self, results: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Process Hume API results into a structured format"""
        try:
            # Extract prosody predictions
            predictions = results[0].get("results", {}).get("predictions", [])
            
            if not predictions:
                return {"error": "No emotion predictions found in results"}
            
            prosody_data = predictions[0].get("models", {}).get("prosody", {}).get("grouped_predictions", [])
            
            if not prosody_data:
                return {"error": "No prosody data found in results"}
            
            # Process emotion segments
            segments = []
            emotion_summary = {}
            
            for group in prosody_data:
                for prediction in group.get("predictions", []):
                    time_data = prediction.get("time", {})
                    emotions = prediction.get("emotions", [])
                    
                    # Get top emotions
                    top_emotions = sorted(emotions, key=lambda x: x["score"], reverse=True)[:5]
                    
                    segment = {
                        "start": time_data.get("begin", 0),
                        "end": time_data.get("end", 0),
                        "duration": time_data.get("end", 0) - time_data.get("begin", 0),
                        "emotions": [
                            {
                                "name": emotion["name"],
                                "score": round(emotion["score"], 4),
                                "confidence": emotion["score"]
                            }
                            for emotion in top_emotions
                        ],
                        "dominant_emotion": top_emotions[0]["name"] if top_emotions else "unknown"
                    }
                    
                    segments.append(segment)
                    
                    # Track emotion summary
                    for emotion in top_emotions:
                        emotion_name = emotion["name"]
                        if emotion_name not in emotion_summary:
                            emotion_summary[emotion_name] = {
                                "total_score": 0,
                                "count": 0,
                                "segments": []
                            }
                        
                        emotion_summary[emotion_name]["total_score"] += emotion["score"]
                        emotion_summary[emotion_name]["count"] += 1
                        emotion_summary[emotion_name]["segments"].append(len(segments) - 1)
            
            # Calculate average scores
            for emotion_name in emotion_summary:
                emotion_summary[emotion_name]["average_score"] = round(
                    emotion_summary[emotion_name]["total_score"] / emotion_summary[emotion_name]["count"], 4
                )
            
            # Sort emotions by average score
            sorted_emotions = sorted(
                emotion_summary.items(),
                key=lambda x: x[1]["average_score"],
                reverse=True
            )
            
            result = {
                "status": "success",
                "file_path": file_path,
                "total_segments": len(segments),
                "segments": segments,
                "emotion_summary": dict(sorted_emotions),
                "dominant_emotions": [emotion[0] for emotion in sorted_emotions[:5]],
                "average_emotion_scores": {
                    emotion[0]: emotion[1]["average_score"]
                    for emotion in sorted_emotions[:10]
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing Hume results: {e}")
            return {"error": f"Error processing emotion results: {str(e)}"}
    
    async def analyze_conversation(self, file_path: str, hume_api_key: Optional[str] = None) -> Dict[str, Any]:
        """Comprehensive conversation analysis combining transcription, diarization, and emotion detection"""
        if not AudioUtils.validate_audio_file(file_path):
            return {"error": "Invalid or unsupported audio file"}
        
        logger.info(f"Starting comprehensive conversation analysis for: {file_path}")
        
        try:
            # Get basic audio info
            audio_info = self.get_audio_info(file_path)
            
            results = {
                "status": "success",
                "file_path": file_path,
                "audio_info": audio_info,
                "analysis_components": []
            }
            
            # 1. Transcription
            logger.info("Starting transcription...")
            transcription_result = await self.transcribe_audio(file_path, "base")
            if "error" not in transcription_result:
                results["transcription"] = transcription_result
                results["analysis_components"].append("transcription")
            else:
                results["transcription_error"] = transcription_result["error"]
            
            # 2. Speaker Diarization
            logger.info("Starting speaker diarization...")
            diarization_result = await self.diarize_speakers(file_path)
            if "error" not in diarization_result:
                results["diarization"] = diarization_result
                results["analysis_components"].append("diarization")
            else:
                results["diarization_error"] = diarization_result["error"]
            
            # 3. Emotion Detection (if API key provided)
            if hume_api_key:
                logger.info("Starting emotion detection...")
                emotion_result = await self.detect_emotions(file_path, hume_api_key)
                if "error" not in emotion_result:
                    results["emotions"] = emotion_result
                    results["analysis_components"].append("emotions")
                else:
                    results["emotions_error"] = emotion_result["error"]
            else:
                results["emotions_error"] = "Hume API key not provided"
            
            # 4. Combine results for insights
            if len(results["analysis_components"]) >= 2:
                results["insights"] = self._generate_conversation_insights(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in conversation analysis: {e}")
            return {"error": str(e)}
    
    def _generate_conversation_insights(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from combined analysis results"""
        insights = {}
        
        try:
            # Speaking time analysis
            if "diarization" in analysis_results:
                diarization = analysis_results["diarization"]
                insights["speaking_distribution"] = {
                    "num_speakers": diarization.get("num_speakers", 0),
                    "most_active_speaker": max(
                        diarization.get("speakers", {}).items(),
                        key=lambda x: x[1]["total_speaking_time"]
                    )[0] if diarization.get("speakers") else None,
                    "speaker_balance": "balanced" if len(diarization.get("speakers", {})) > 1 else "monologue"
                }
            
            # Emotional patterns
            if "emotions" in analysis_results:
                emotions = analysis_results["emotions"]
                insights["emotional_patterns"] = {
                    "dominant_emotion": emotions.get("dominant_emotions", [None])[0],
                    "emotion_variety": len(emotions.get("emotion_summary", {})),
                    "emotional_intensity": max(
                        emotions.get("average_emotion_scores", {}).values()
                    ) if emotions.get("average_emotion_scores") else 0
                }
            
            # Conversation dynamics
            if "transcription" in analysis_results and "diarization" in analysis_results:
                transcription = analysis_results["transcription"]
                diarization = analysis_results["diarization"]
                
                insights["conversation_dynamics"] = {
                    "total_duration": diarization.get("total_duration", 0),
                    "words_per_minute": len(transcription.get("transcript", "").split()) / (
                        diarization.get("total_duration", 1) / 60
                    ) if diarization.get("total_duration") else 0,
                    "turn_taking": diarization.get("total_segments", 0) / diarization.get("num_speakers", 1)
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {"error": f"Error generating insights: {str(e)}"}
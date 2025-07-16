import logging
import os
import asyncio
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP
from pathlib import Path

from audio_processor import AudioProcessor
from utils import AudioUtils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("audio-processing")

# Global audio processor instance
audio_processor = AudioProcessor()

def cleanup_on_exit():
    """Cleanup function to run on server shutdown"""
    logger.info("Cleaning up audio processor...")
    audio_processor.cleanup()

# Register cleanup function
import atexit
atexit.register(cleanup_on_exit)

@mcp.tool()
async def get_audio_info(file_path: str) -> str:
    """Get comprehensive information about an audio file including duration, format, metadata, and technical details"""
    logger.info(f"Getting audio info for: {file_path}")
    
    try:
        info = audio_processor.get_audio_info(file_path)
        
        if "error" in info:
            return f"Error: {info['error']}"
        
        # Format the response nicely
        result = f"""
Audio File Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: {info.get('file_path', 'Unknown')}
Duration: {info.get('duration_formatted', 'Unknown')} ({info.get('duration_seconds', 0):.2f} seconds)
Format: {info.get('format', 'Unknown').upper()}
File Size: {info.get('file_size_mb', 0)} MB

Technical Details:
├── Sample Rate: {info.get('sample_rate', 'Unknown')} Hz
├── Channels: {info.get('channels', 'Unknown')}
├── Sample Width: {info.get('sample_width', 'Unknown')} bytes
└── Frame Count: {info.get('frame_count', 'Unknown')}"""

        # Add metadata if available
        if 'tags' in info and info['tags']:
            result += "\n\nMetadata:\n"
            for key, value in info['tags'].items():
                result += f"├── {key}: {value}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_audio_info: {e}")
        return f"Error getting audio info: {str(e)}"

@mcp.tool()
async def convert_audio_format(
    input_path: str, 
    output_format: str, 
    quality: str = "medium"
) -> str:
    """Convert audio file to a different format with optional quality settings
    
    Args:
        input_path: Path to the input audio file
        output_format: Target format (mp3, wav, flac, ogg, etc.)
        quality: Quality level for lossy formats (low, medium, high)
    """
    logger.info(f"Converting {input_path} to {output_format} format with {quality} quality")
    
    try:
        result = audio_processor.convert_format(input_path, output_format, quality)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        response = f"""
Audio Format Conversion Complete:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Successfully converted audio file

Input: {result['input_format'].upper()} → Output: {result['output_format'].upper()}
Quality: {result['quality']}
Output File: {result['output_path']}

File Size Comparison:
├── Original: {result['original_size_mb']} MB
└── Converted: {result['converted_size_mb']} MB

The converted file has been saved to: {result['output_path']}
"""
        
        return response
        
    except Exception as e:
        logger.error(f"Error in convert_audio_format: {e}")
        return f"Error converting audio format: {str(e)}"

@mcp.tool()
async def trim_audio(
    input_path: str, 
    start_seconds: float, 
    end_seconds: Optional[float] = None
) -> str:
    """Trim audio file to specified time range
    
    Args:
        input_path: Path to the input audio file
        start_seconds: Start time in seconds
        end_seconds: End time in seconds (optional, defaults to end of file)
    """
    logger.info(f"Trimming audio from {start_seconds}s to {end_seconds}s")
    
    try:
        result = audio_processor.trim_audio(input_path, start_seconds, end_seconds)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        response = f"""
Audio Trimming Complete:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Successfully trimmed audio file

Time Range: {result['start_time']} → {result['end_time']}
Original Duration: {result['original_duration']}
Trimmed Duration: {result['trimmed_duration']}

Output File: {result['output_path']}

The trimmed audio has been saved to: {result['output_path']}
"""
        
        return response
        
    except Exception as e:
        logger.error(f"Error in trim_audio: {e}")
        return f"Error trimming audio: {str(e)}"

@mcp.tool()
async def merge_audio_files(
    input_paths: List[str], 
    output_format: str = "wav"
) -> str:
    """Merge multiple audio files into a single file
    
    Args:
        input_paths: List of paths to audio files to merge
        output_format: Format for the output file (wav, mp3, etc.)
    """
    logger.info(f"Merging {len(input_paths)} audio files")
    
    try:
        result = audio_processor.merge_audio(input_paths, output_format)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        response = f"""
Audio Merging Complete:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Successfully merged {result['total_files']} audio files

Total Duration: {result['total_duration']}
Output Format: {result['output_format'].upper()}
Output File: {result['output_path']}

Merged Files:
"""
        
        for file_info in result['merged_files']:
            response += f"├── {file_info['position']}. {file_info['file']} ({file_info['duration']})\n"
        
        response += f"\nThe merged audio has been saved to: {result['output_path']}"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in merge_audio_files: {e}")
        return f"Error merging audio files: {str(e)}"

@mcp.tool()
async def transcribe_audio(
    file_path: str, 
    model: str = "base"
) -> str:
    """Transcribe audio file to text using Whisper AI
    
    Args:
        file_path: Path to the audio file to transcribe
        model: Whisper model to use (tiny, base, small, medium, large)
    """
    logger.info(f"Transcribing audio file: {file_path} with model: {model}")
    
    try:
        result = await audio_processor.transcribe_audio(file_path, model)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        response = f"""
Audio Transcription Complete:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Successfully transcribed audio file

File: {result['file_path']}
Model: {result['model_used']}
Detected Language: {result['language']}

Transcript:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{result['transcript']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Add segments if available
        if 'segments' in result:
            response += "\n\nTimestamped Segments:\n"
            for segment in result['segments']:
                start_time = f"{int(segment['start'] // 60):02d}:{int(segment['start'] % 60):02d}"
                end_time = f"{int(segment['end'] // 60):02d}:{int(segment['end'] % 60):02d}"
                response += f"[{start_time} - {end_time}] {segment['text']}\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in transcribe_audio: {e}")
        return f"Error transcribing audio: {str(e)}"

@mcp.tool()
async def generate_speech(
    text: str, 
    output_format: str = "mp3",
    voice: str = "default"
) -> str:
    """Generate speech from text using text-to-speech
    
    Args:
        text: Text to convert to speech
        output_format: Audio format for output (mp3, wav, etc.)
        voice: Voice to use (currently only 'default' supported)
    """
    logger.info(f"Generating speech for text: {text[:50]}...")
    
    try:
        result = await audio_processor.generate_speech(text, output_format, voice)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        response = f"""
Speech Generation Complete:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Successfully generated speech

Text Length: {result['text_length']} characters
Output Format: {result['output_format'].upper()}
Voice: {result['voice']}
Output File: {result['output_path']}

Generated Text:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The speech audio has been saved to: {result['output_path']}
"""
        
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_speech: {e}")
        return f"Error generating speech: {str(e)}"

@mcp.tool()
async def diarize_speakers(file_path: str) -> str:
    """Identify who spoke when in an audio file using speaker diarization
    
    Args:
        file_path: Path to the audio file to analyze
    """
    logger.info(f"Performing speaker diarization on: {file_path}")
    
    try:
        result = await audio_processor.diarize_speakers(file_path)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        response = f"""
Speaker Diarization Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Successfully identified speakers in audio file

File: {result['file_path']}
Total Duration: {AudioUtils.format_duration(result['total_duration'])}
Number of Speakers: {result['num_speakers']}
Total Segments: {result['total_segments']}

Speaker Summary:
"""
        
        for speaker_id, info in result['speakers'].items():
            response += f"├── {speaker_id}: {AudioUtils.format_duration(info['total_speaking_time'])} ({info['percentage']}% of total)\n"
            response += f"│   └── {info['segments']} speaking segments\n"
        
        response += "\nDetailed Timeline:\n"
        for i, segment in enumerate(result['segments'][:10]):  # Show first 10 segments
            start_time = AudioUtils.format_duration(segment['start'])
            end_time = AudioUtils.format_duration(segment['end'])
            response += f"├── {start_time} - {end_time}: {segment['speaker']}\n"
        
        if len(result['segments']) > 10:
            response += f"└── ... and {len(result['segments']) - 10} more segments\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in diarize_speakers: {e}")
        return f"Error performing speaker diarization: {str(e)}"

@mcp.tool()
async def detect_emotions(file_path: str, hume_api_key: str) -> str:
    """Detect emotions in audio using Hume AI API
    
    Args:
        file_path: Path to the audio file to analyze
        hume_api_key: Hume AI API key for emotion detection
    """
    logger.info(f"Detecting emotions in: {file_path}")
    
    try:
        result = await audio_processor.detect_emotions(file_path, hume_api_key)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        response = f"""
Emotion Detection Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Successfully analyzed emotions in audio file

File: {result['file_path']}
Total Segments: {result['total_segments']}

Top Emotions Detected:
"""
        
        for emotion, score in result['average_emotion_scores'].items():
            response += f"├── {emotion.title()}: {score:.4f}\n"
        
        response += f"\nDominant Emotions: {', '.join(result['dominant_emotions'])}\n"
        
        response += "\nEmotion Timeline (first 10 segments):\n"
        for i, segment in enumerate(result['segments'][:10]):
            start_time = AudioUtils.format_duration(segment['start'])
            end_time = AudioUtils.format_duration(segment['end'])
            dominant = segment['dominant_emotion']
            top_score = segment['emotions'][0]['score'] if segment['emotions'] else 0
            response += f"├── {start_time} - {end_time}: {dominant.title()} ({top_score:.3f})\n"
        
        if len(result['segments']) > 10:
            response += f"└── ... and {len(result['segments']) - 10} more segments\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in detect_emotions: {e}")
        return f"Error detecting emotions: {str(e)}"

@mcp.tool()
async def analyze_conversation(
    file_path: str, 
    hume_api_key: Optional[str] = None
) -> str:
    """Comprehensive conversation analysis combining transcription, speaker diarization, and emotion detection
    
    Args:
        file_path: Path to the audio file to analyze
        hume_api_key: Optional Hume AI API key for emotion detection
    """
    logger.info(f"Starting comprehensive conversation analysis: {file_path}")
    
    try:
        result = await audio_processor.analyze_conversation(file_path, hume_api_key)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        response = f"""
Comprehensive Conversation Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Analysis completed with {len(result['analysis_components'])} components

File: {result['file_path']}
Components: {', '.join(result['analysis_components'])}

"""
        
        # Audio Info Summary
        if 'audio_info' in result:
            audio_info = result['audio_info']
            response += f"📊 Audio Info:\n"
            response += f"├── Duration: {audio_info.get('duration_formatted', 'Unknown')}\n"
            response += f"├── Format: {audio_info.get('format', 'Unknown').upper()}\n"
            response += f"└── Size: {audio_info.get('file_size_mb', 0)} MB\n\n"
        
        # Transcription Summary
        if 'transcription' in result:
            transcript = result['transcription']
            response += f"📝 Transcription:\n"
            response += f"├── Language: {transcript.get('language', 'Unknown')}\n"
            response += f"├── Model: {transcript.get('model_used', 'Unknown')}\n"
            response += f"└── Length: {len(transcript.get('transcript', '').split())} words\n\n"
        
        # Speaker Analysis
        if 'diarization' in result:
            diarization = result['diarization']
            response += f"👥 Speaker Analysis:\n"
            response += f"├── Speakers: {diarization.get('num_speakers', 0)}\n"
            response += f"├── Speaking Segments: {diarization.get('total_segments', 0)}\n"
            
            # Show speaker distribution
            for speaker_id, info in diarization.get('speakers', {}).items():
                response += f"├── {speaker_id}: {info.get('percentage', 0)}% of conversation\n"
            response += "\n"
        
        # Emotion Analysis
        if 'emotions' in result:
            emotions = result['emotions']
            response += f"😊 Emotion Analysis:\n"
            response += f"├── Segments: {emotions.get('total_segments', 0)}\n"
            response += f"├── Top Emotions: {', '.join(emotions.get('dominant_emotions', [])[:3])}\n"
            response += f"└── Emotional Variety: {len(emotions.get('emotion_summary', {}))} emotions detected\n\n"
        
        # Insights
        if 'insights' in result:
            insights = result['insights']
            response += f"🔍 Conversation Insights:\n"
            
            if 'speaking_distribution' in insights:
                speaking = insights['speaking_distribution']
                response += f"├── Most Active: {speaking.get('most_active_speaker', 'Unknown')}\n"
                response += f"├── Balance: {speaking.get('speaker_balance', 'Unknown')}\n"
            
            if 'emotional_patterns' in insights:
                emotional = insights['emotional_patterns']
                response += f"├── Dominant Emotion: {emotional.get('dominant_emotion', 'Unknown')}\n"
                response += f"├── Emotional Intensity: {emotional.get('emotional_intensity', 0):.3f}\n"
            
            if 'conversation_dynamics' in insights:
                dynamics = insights['conversation_dynamics']
                response += f"├── Speaking Rate: {dynamics.get('words_per_minute', 0):.1f} words/minute\n"
                response += f"└── Turn Taking: {dynamics.get('turn_taking', 0):.1f} turns/speaker\n"
        
        # Add errors if any
        errors = []
        if 'transcription_error' in result:
            errors.append(f"Transcription: {result['transcription_error']}")
        if 'diarization_error' in result:
            errors.append(f"Diarization: {result['diarization_error']}")
        if 'emotions_error' in result:
            errors.append(f"Emotions: {result['emotions_error']}")
        
        if errors:
            response += f"\n⚠️ Partial Analysis (some features unavailable):\n"
            for error in errors:
                response += f"├── {error}\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in analyze_conversation: {e}")
        return f"Error analyzing conversation: {str(e)}"

@mcp.tool()
async def list_supported_formats() -> str:
    """List all supported audio formats for input and output"""
    
    formats = AudioUtils.SUPPORTED_FORMATS
    
    response = f"""
Supported Audio Formats:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Input/Output Formats:
"""
    
    for format_ext in formats:
        format_name = format_ext[1:].upper()
        response += f"├── {format_name} ({format_ext})\n"
    
    response += f"""
Total: {len(formats)} formats supported

Notes:
• All formats support conversion between each other
• Quality settings available for lossy formats (MP3, OGG)
• Lossless formats (FLAC, WAV) preserve original quality
• Some formats may require additional system dependencies (FFmpeg)
"""
    
    return response

def main():
    """Main function to run the audio processing MCP server"""
    logger.info("Starting Audio Processing MCP Server...")
    
    # Log available features
    try:
        import whisper
        logger.info("✓ Whisper transcription available")
    except ImportError:
        logger.warning("✗ Whisper transcription not available (install with: pip install openai-whisper)")
    
    try:
        from gtts import gTTS
        logger.info("✓ Text-to-speech available")
    except ImportError:
        logger.warning("✗ Text-to-speech not available (install with: pip install gTTS)")
    
    try:
        from pyannote.audio import Pipeline
        logger.info("✓ Speaker diarization available")
    except ImportError:
        logger.warning("✗ Speaker diarization not available (install with: pip install pyannote.audio)")
    
    try:
        import httpx
        logger.info("✓ Emotion detection API client available")
    except ImportError:
        logger.warning("✗ Emotion detection not available (install with: pip install httpx)")
    
    logger.info("✓ Audio format conversion available")
    logger.info("✓ Audio trimming and merging available")
    logger.info("✓ Audio metadata extraction available")
    
    # Run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
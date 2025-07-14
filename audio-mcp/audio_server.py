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
    
    logger.info("✓ Audio format conversion available")
    logger.info("✓ Audio trimming and merging available")
    logger.info("✓ Audio metadata extraction available")
    
    # Run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
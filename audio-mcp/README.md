# Audio Processing MCP Server

A comprehensive Model Context Protocol (MCP) server for audio processing tasks including transcription, format conversion, trimming, merging, and text-to-speech generation.

## Features

### 🎵 Core Audio Operations
- **Audio Info**: Get comprehensive metadata and technical details
- **Format Conversion**: Convert between MP3, WAV, FLAC, OGG, M4A, AAC, WMA
- **Audio Trimming**: Cut audio segments with precise timing
- **Audio Merging**: Combine multiple audio files into one
- **Format Support**: List all supported audio formats

### 🎤 AI-Powered Features
- **Speech Transcription**: Convert audio to text using OpenAI Whisper
- **Text-to-Speech**: Generate speech from text using Google TTS
- **Timestamped Segments**: Get time-aligned transcription segments
- **Language Detection**: Automatic language detection during transcription

### 🔧 Technical Features
- **Multiple Input Methods**: File paths and base64 encoded audio
- **Quality Control**: Configurable quality settings for lossy formats
- **Temporary File Management**: Automatic cleanup of processing files
- **Comprehensive Metadata**: Extract detailed audio file information
- **Error Handling**: Graceful error handling with helpful messages

## Installation

### Basic Installation
```bash
cd audio-mcp
pip install -r requirements.txt
```

### With AI Features
```bash
# For transcription support
pip install openai-whisper torch torchaudio

# For text-to-speech support
pip install gTTS

# Or install all optional dependencies
pip install -e .[all]
```

### System Dependencies
Some audio formats require FFmpeg:
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Usage

### Starting the Server
```bash
python audio_server.py
```

### With MCP Client
```bash
# From the parent directory
python client/mcp-client/client.py audio-mcp/audio_server.py
```

### Example Interactions

**Get Audio Information:**
```
Query: "What's the duration and format of /path/to/audio.mp3?"
```

**Convert Audio Format:**
```
Query: "Convert /path/to/audio.wav to MP3 format with high quality"
```

**Transcribe Audio:**
```
Query: "Transcribe this meeting recording: /path/to/meeting.mp3"
```

**Generate Speech:**
```
Query: "Convert this text to speech: Hello, this is a test of the text-to-speech feature"
```

**Trim Audio:**
```
Query: "Trim /path/to/podcast.mp3 from 5 minutes to 10 minutes"
```

**Merge Audio Files:**
```
Query: "Merge these files into one: /path/to/intro.mp3, /path/to/main.mp3, /path/to/outro.mp3"
```

## Available Tools

### `get_audio_info(file_path: str)`
Get comprehensive information about an audio file.

### `convert_audio_format(input_path: str, output_format: str, quality: str = "medium")`
Convert audio file to different format with quality control.

### `trim_audio(input_path: str, start_seconds: float, end_seconds: Optional[float] = None)`
Trim audio file to specified time range.

### `merge_audio_files(input_paths: List[str], output_format: str = "wav")`
Merge multiple audio files into single file.

### `transcribe_audio(file_path: str, model: str = "base")`
Transcribe audio to text using Whisper AI.
- Models: `tiny`, `base`, `small`, `medium`, `large`
- Requires: `openai-whisper`

### `generate_speech(text: str, output_format: str = "mp3", voice: str = "default")`
Generate speech from text using TTS.
- Requires: `gTTS`

### `list_supported_formats()`
List all supported audio formats.

## Supported Formats

- **MP3** - Compressed audio
- **WAV** - Uncompressed audio
- **FLAC** - Lossless compression
- **OGG** - Open source compressed
- **M4A** - Apple audio format
- **AAC** - Advanced Audio Codec
- **WMA** - Windows Media Audio

## Quality Settings

For lossy formats (MP3, OGG):
- **low**: 128kbps
- **medium**: 192kbps (default)
- **high**: 320kbps

## Error Handling

The server provides helpful error messages for:
- Unsupported file formats
- Missing dependencies
- Invalid time ranges
- File not found errors
- Permission issues

## Development

### Project Structure
```
audio-mcp/
├── audio_server.py          # Main MCP server
├── audio_processor.py       # Core audio processing
├── utils.py                 # Utility functions
├── requirements.txt         # Core dependencies
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

### Adding New Features
1. Add processing logic to `AudioProcessor` class
2. Create MCP tool wrapper in `audio_server.py`
3. Update documentation and tests

### Testing
```bash
# Test basic functionality
python -c "from audio_processor import AudioProcessor; ap = AudioProcessor(); print('Audio processor initialized successfully')"

# Test with sample audio file
python audio_server.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes with tests
4. Submit a pull request

## License

This project is part of the MCP tutorial series and is available under the MIT License.

---

*This MCP server demonstrates the power of the Model Context Protocol for audio processing workflows.*
# Audio Processor Pro

## Overview

Audio Processor Pro is a Flask-based web application designed for professional audio processing tasks. The application provides a comprehensive suite of audio manipulation tools including vocal separation, pitch adjustment, format conversion, noise reduction, and audio enhancement. It features a modern dark-themed web interface with drag-and-drop file upload functionality and supports multiple audio formats (MP3, WAV, FLAC, OGG, M4A).

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Web Framework**: Bootstrap 5 with dark theme for responsive UI design
- **JavaScript Architecture**: Class-based modular approach with separate modules for audio player and main application logic
- **Template Engine**: Jinja2 templates with Flask's built-in templating system
- **User Interface**: Single-page application with drag-and-drop file upload and real-time audio processing controls

### Backend Architecture
- **Web Framework**: Flask with ProxyFix middleware for deployment behind reverse proxies
- **Audio Processing Engine**: Custom AudioProcessor class using multiple audio libraries (librosa, pydub, soundfile)
- **File Management**: Secure file handling with UUID-based naming and validation
- **Session Management**: Flask sessions with configurable secret key
- **Error Handling**: Comprehensive logging and error handling throughout the application

### Audio Processing Pipeline
- **Format Support**: Multi-format audio file validation and conversion
- **Processing Features**: Vocal separation using Spleeter, noise reduction, normalization, and pitch adjustment
- **File Processing**: Temporary file management with automatic cleanup
- **Audio Analysis**: Metadata extraction and audio file validation

### Security & Validation
- **File Security**: Secure filename handling with werkzeug utilities
- **File Size Limits**: 500MB maximum upload size to prevent resource exhaustion
- **Format Validation**: Strict audio format validation before processing
- **Input Sanitization**: All user inputs are validated and sanitized

### Configuration Management
- **Environment Variables**: Session secrets and configuration via environment variables
- **Directory Management**: Automatic creation of upload and processed file directories
- **Development Mode**: Debug mode enabled for development with detailed logging

## External Dependencies

### Core Python Libraries
- **Flask**: Web framework for HTTP request handling and routing
- **librosa**: Advanced audio analysis and feature extraction
- **pydub**: Audio file format conversion and basic manipulation
- **soundfile**: High-quality audio file I/O operations
- **noisereduce**: Noise reduction algorithms for audio enhancement

### Audio Processing Libraries
- **Spleeter**: AI-based vocal separation (referenced in code)
- **mutagen**: Audio metadata reading and writing
- **scipy**: Signal processing algorithms for audio manipulation
- **numpy**: Numerical operations for audio data processing

### Frontend Dependencies
- **Bootstrap 5**: CSS framework with dark theme from cdn.replit.com
- **Font Awesome 6**: Icon library for UI elements
- **Custom CSS/JS**: Application-specific styling and functionality

### System Dependencies
- **ffmpeg**: Required by pydub for audio format conversion (system-level dependency)
- **Temporary File System**: OS-level temporary directory management for processing workflows

### Development Tools
- **Werkzeug**: WSGI utilities and development server
- **Python Logging**: Built-in logging for debugging and monitoring
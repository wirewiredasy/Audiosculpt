# Audio Processor Pro

## Overview

Audio Processor Pro is a FastAPI-based microservices application designed for professional audio processing tasks. The application provides a comprehensive suite of 13 audio manipulation tools across 8 independent microservices including vocal separation, pitch adjustment, format conversion, noise reduction, and audio enhancement. It features a modern dark-themed web interface with drag-and-drop file upload functionality and supports multiple audio formats (MP3, WAV, FLAC, OGG, M4A).

## Recent Changes (August 2025)

- ✅ **Complete Flask to FastAPI Migration**: Successfully migrated from Flask to FastAPI with full microservices architecture
- ✅ **Microservices Implementation**: Created 8 independent services for each audio processing tool
- ✅ **ASGI Server**: Now using uvicorn instead of gunicorn for high-performance async processing
- ✅ **13 Processing Endpoints**: All audio tools available through separate microservice endpoints
- ✅ **Async Error Handling**: Implemented comprehensive async error handling with proper HTTP status codes
- ✅ **Server Configuration Fixed**: Resolved gunicorn/uvicorn compatibility issues and optimized startup process
- ✅ **Audio Dependencies**: Installed core audio processing libraries (librosa, soundfile, pydub, mutagen)
- ✅ **Fallback Systems**: Implemented smart fallback for noisereduce dependency using librosa spectral gating
- ✅ **Application Debugging Complete (August 3, 2025)**: Fixed server compatibility and type conversion issues, application now running successfully

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Web Framework**: Bootstrap 5 with dark theme for responsive UI design
- **JavaScript Architecture**: Class-based modular approach with separate modules for audio player and main application logic
- **Template Engine**: Jinja2 templates with Flask's built-in templating system
- **User Interface**: Single-page application with drag-and-drop file upload and real-time audio processing controls

### Backend Architecture
- **Web Framework**: FastAPI with uvicorn ASGI server for high-performance async processing
- **Microservices Architecture**: Independent services for each audio processing tool
- **Audio Processing Services**: Separate microservices for vocal separation, pitch/tempo, format conversion, cutting, noise reduction, volume normalization, effects, and metadata
- **File Management**: Secure file handling with UUID-based naming and validation
- **API Gateway**: Central FastAPI application managing all microservice interactions
- **Error Handling**: Comprehensive async error handling with proper HTTP status codes
- **Server Startup**: Proper uvicorn configuration with reload functionality for development

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
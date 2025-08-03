"""
Format Conversion Microservice
Handles audio format conversion between different formats
"""
import os
import uuid
from pydub import AudioSegment
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class FormatConversionService:
    """Microservice for audio format conversion"""
    
    async def convert_format(self, input_path: str, output_dir: str, output_format: str) -> Dict[str, Any]:
        """Convert audio to different format"""
        try:
            valid_formats = ['mp3', 'wav', 'flac', 'ogg', 'm4a']
            if output_format.lower() not in valid_formats:
                return {'success': False, 'error': f"Unsupported format. Allowed: {', '.join(valid_formats)}"}
            
            audio = AudioSegment.from_file(input_path)
            output_filename = f"converted_{uuid.uuid4()}.{output_format.lower()}"
            output_path = os.path.join(output_dir, output_filename)
            
            # Export with appropriate settings for each format
            if output_format.lower() == 'mp3':
                audio.export(output_path, format='mp3', bitrate='192k')
            elif output_format.lower() == 'wav':
                audio.export(output_path, format='wav')
            elif output_format.lower() == 'flac':
                audio.export(output_path, format='flac')
            elif output_format.lower() == 'ogg':
                audio.export(output_path, format='ogg')
            elif output_format.lower() == 'm4a':
                audio.export(output_path, format='mp4', codec='aac')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Successfully converted to {output_format.upper()}"
            }
            
        except Exception as e:
            logger.error(f"Error converting format: {e}")
            return {'success': False, 'error': f"Format conversion failed: {str(e)}"}
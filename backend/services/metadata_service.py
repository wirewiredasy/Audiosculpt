"""
Metadata Service Microservice
Handles audio metadata reading and editing
"""
import os
import uuid
import shutil
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.id3._frames import TIT2, TPE1, TALB, TPE2
from pydub import AudioSegment
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class MetadataService:
    """Microservice for metadata operations"""
    
    async def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive audio file information"""
        try:
            audio = AudioSegment.from_file(file_path)
            
            info = {
                'duration': len(audio) / 1000.0,  # seconds
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'format': os.path.splitext(file_path)[1][1:].upper(),
                'file_size': os.path.getsize(file_path)
            }
            
            # Try to get metadata for MP3 files
            if file_path.lower().endswith('.mp3'):
                try:
                    mp3_file = MP3(file_path)
                    if mp3_file.tags:
                        info['title'] = str(mp3_file.tags.get('TIT2', ['Unknown'])[0])
                        info['artist'] = str(mp3_file.tags.get('TPE1', ['Unknown'])[0])
                        info['album'] = str(mp3_file.tags.get('TALB', ['Unknown'])[0])
                        info['bitrate'] = mp3_file.info.bitrate if mp3_file.info else 'Unknown'
                except Exception as e:
                    logger.warning(f"Could not read MP3 metadata: {e}")
            
            return {
                'success': True,
                'info': info,
                'message': "Audio information retrieved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            return {'success': False, 'error': f"Failed to get audio info: {str(e)}"}

    async def edit_metadata(self, input_path: str, output_dir: str, metadata: Dict[str, str]) -> Dict[str, Any]:
        """Edit MP3 metadata"""
        try:
            if not input_path.lower().endswith('.mp3'):
                return {'success': False, 'error': 'Metadata editing only supported for MP3 files'}
            
            output_filename = f"metadata_{uuid.uuid4()}.mp3"
            output_path = os.path.join(output_dir, output_filename)
            
            # Copy file first
            shutil.copy2(input_path, output_path)
            
            audio_file = MP3(output_path, ID3=ID3)
            
            if audio_file.tags is None:
                audio_file.add_tags()
            
            tags = audio_file.tags
            if tags is not None:
                if 'title' in metadata:
                    tags.add(TIT2(encoding=3, text=metadata['title']))
                if 'artist' in metadata:
                    tags.add(TPE1(encoding=3, text=metadata['artist']))
                if 'album' in metadata:
                    tags.add(TALB(encoding=3, text=metadata['album']))
                if 'albumartist' in metadata:
                    tags.add(TPE2(encoding=3, text=metadata['albumartist']))
            
            audio_file.save()
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': "Metadata updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error editing metadata: {e}")
            return {'success': False, 'error': f"Metadata editing failed: {str(e)}"}
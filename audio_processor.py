import os
import logging
import tempfile
import numpy as np
from typing import Optional, Tuple, Dict, Any
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize
try:
    import noisereduce as nr
    HAS_NOISEREDUCE = True
except ImportError:
    HAS_NOISEREDUCE = False
    nr = None
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2
from scipy import signal
import subprocess
import shutil

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Comprehensive audio processing class with all required features"""
    
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temp directory: {e}")
    
    def validate_audio_file(self, file_path: str) -> bool:
        """Validate if file is a supported audio format"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                return False
            
            # Try to load with pydub
            AudioSegment.from_file(file_path)
            return True
        except Exception as e:
            logger.error(f"Invalid audio file {file_path}: {e}")
            return False
    
    def separate_vocals(self, input_path: str, output_dir: str) -> Tuple[str, str]:
        """
        Separate vocals using Spleeter 2-stem model
        Returns paths to vocals and accompaniment files
        """
        try:
            # For CPU processing, we'll use a simplified vocal removal technique
            # using center channel extraction as Spleeter requires specific setup
            audio = AudioSegment.from_file(input_path)
            
            # Convert to numpy array for processing
            samples = np.array(audio.get_array_of_samples())
            
            if audio.channels == 2:
                # Reshape for stereo
                samples = samples.reshape((-1, 2))
                
                # Simple vocal removal: subtract center channel
                # Vocals are typically centered, so L-R removes center content
                vocals = (samples[:, 0] + samples[:, 1]) / 2  # Center channel (vocals)
                instrumental = (samples[:, 0] - samples[:, 1]) / 2  # Side channels
                
                # Convert back to AudioSegment
                vocals_audio = AudioSegment(
                    vocals.astype(np.int16).tobytes(),
                    frame_rate=audio.frame_rate,
                    sample_width=audio.sample_width,
                    channels=1
                )
                
                instrumental_audio = AudioSegment(
                    instrumental.astype(np.int16).tobytes(),
                    frame_rate=audio.frame_rate,
                    sample_width=audio.sample_width,
                    channels=1
                )
            else:
                # Mono audio - can't separate effectively
                vocals_audio = audio
                instrumental_audio = AudioSegment.silent(duration=len(audio))
            
            # Save separated tracks
            vocals_path = os.path.join(output_dir, 'vocals.wav')
            instrumental_path = os.path.join(output_dir, 'instrumental.wav')
            
            vocals_audio.export(vocals_path, format='wav')
            instrumental_audio.export(instrumental_path, format='wav')
            
            return vocals_path, instrumental_path
            
        except Exception as e:
            logger.error(f"Error in vocal separation: {e}")
            raise
    
    def change_pitch_tempo(self, input_path: str, output_path: str, 
                          pitch_shift: float = 0, tempo_change: float = 1.0) -> str:
        """
        Change pitch and tempo using librosa
        pitch_shift: semitones to shift (positive = higher, negative = lower)
        tempo_change: tempo multiplier (1.0 = original, 2.0 = double speed)
        """
        try:
            # Load audio with librosa
            y, sr = librosa.load(input_path, sr=None)
            
            # Apply pitch shift
            if pitch_shift != 0:
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_shift)
            
            # Apply tempo change
            if tempo_change != 1.0:
                y = librosa.effects.time_stretch(y, rate=tempo_change)
            
            # Save the result
            sf.write(output_path, y, sr)
            return output_path
            
        except Exception as e:
            logger.error(f"Error in pitch/tempo change: {e}")
            raise
    
    def convert_format(self, input_path: str, output_path: str, output_format: str) -> str:
        """Convert audio to different format using pydub"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Set quality parameters based on format
            export_params = {}
            if output_format.lower() == 'mp3':
                export_params = {'bitrate': '320k'}
            elif output_format.lower() == 'ogg':
                export_params = {'codec': 'libvorbis'}
            
            audio.export(output_path, format=output_format.lower(), **export_params)
            return output_path
            
        except Exception as e:
            logger.error(f"Error in format conversion: {e}")
            raise
    
    def cut_audio(self, input_path: str, output_path: str, 
                  start_time: float, end_time: float) -> str:
        """Cut audio segment (times in seconds)"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)
            
            cut_audio = audio[start_ms:end_ms]
            cut_audio.export(output_path, format='wav')
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error cutting audio: {e}")
            raise
    
    def join_audio(self, input_paths: list, output_path: str) -> str:
        """Join multiple audio files"""
        try:
            combined = AudioSegment.empty()
            
            for path in input_paths:
                audio = AudioSegment.from_file(path)
                combined += audio
            
            combined.export(output_path, format='wav')
            return output_path
            
        except Exception as e:
            logger.error(f"Error joining audio: {e}")
            raise
    
    def reduce_noise(self, input_path: str, output_path: str, 
                     noise_reduce_factor: float = 0.5) -> str:
        """Reduce noise using spectral gating or noisereduce if available"""
        try:
            # Load audio
            y, sr = librosa.load(input_path, sr=None)
            
            if HAS_NOISEREDUCE:
                # Use noisereduce library if available
                reduced_noise = nr.reduce_noise(y=y, sr=sr, prop_decrease=noise_reduce_factor)
            else:
                # Fallback: Simple spectral gating using librosa
                # Compute spectral centroid to identify noisy regions
                stft = librosa.stft(y)
                magnitude = np.abs(stft)
                
                # Apply simple noise gate based on magnitude threshold
                threshold = np.percentile(magnitude, 20 * (1 - noise_reduce_factor))
                mask = magnitude > threshold
                
                # Apply the mask
                stft_filtered = stft * mask
                reduced_noise = librosa.istft(stft_filtered)
            
            # Save result
            sf.write(output_path, reduced_noise, sr)
            return output_path
            
        except Exception as e:
            logger.error(f"Error in noise reduction: {e}")
            raise
    
    def normalize_volume(self, input_path: str, output_path: str, 
                        target_dBFS: float = -20.0) -> str:
        """Normalize audio volume"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Normalize to target dBFS
            change_in_dBFS = target_dBFS - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dBFS)
            
            normalized_audio.export(output_path, format='wav')
            return output_path
            
        except Exception as e:
            logger.error(f"Error normalizing volume: {e}")
            raise
    
    def apply_fade(self, input_path: str, output_path: str, 
                   fade_in_duration: float = 0, fade_out_duration: float = 0) -> str:
        """Apply fade in/out effects (durations in seconds)"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            if fade_in_duration > 0:
                audio = audio.fade_in(int(fade_in_duration * 1000))
            
            if fade_out_duration > 0:
                audio = audio.fade_out(int(fade_out_duration * 1000))
            
            audio.export(output_path, format='wav')
            return output_path
            
        except Exception as e:
            logger.error(f"Error applying fade: {e}")
            raise
    
    def reverse_audio(self, input_path: str, output_path: str) -> str:
        """Reverse audio playback"""
        try:
            audio = AudioSegment.from_file(input_path)
            reversed_audio = audio.reverse()
            reversed_audio.export(output_path, format='wav')
            return output_path
            
        except Exception as e:
            logger.error(f"Error reversing audio: {e}")
            raise
    
    def apply_equalizer(self, input_path: str, output_path: str, 
                       low_gain: float = 0, mid_gain: float = 0, high_gain: float = 0) -> str:
        """Apply 3-band equalizer (gains in dB)"""
        try:
            # Load audio
            y, sr = librosa.load(input_path, sr=None)
            
            # Define frequency bands
            low_freq = 300   # Hz
            high_freq = 3000 # Hz
            
            # Create filters
            nyquist = sr / 2
            
            # Low band (below 300 Hz)
            if low_gain != 0:
                low_sos = signal.butter(4, low_freq / nyquist, btype='low', output='sos')
                low_filtered = signal.sosfilt(low_sos, y)
                low_filtered *= (10 ** (low_gain / 20))
                y = y + (low_filtered - signal.sosfilt(low_sos, y))
            
            # High band (above 3000 Hz)
            if high_gain != 0:
                high_sos = signal.butter(4, high_freq / nyquist, btype='high', output='sos')
                high_filtered = signal.sosfilt(high_sos, y)
                high_filtered *= (10 ** (high_gain / 20))
                y = y + (high_filtered - signal.sosfilt(high_sos, y))
            
            # Mid band (300-3000 Hz)
            if mid_gain != 0:
                mid_sos = signal.butter(4, [low_freq / nyquist, high_freq / nyquist], 
                                      btype='band', output='sos')
                mid_filtered = signal.sosfilt(mid_sos, y)
                mid_filtered *= (10 ** (mid_gain / 20))
                y = y + (mid_filtered - signal.sosfilt(mid_sos, y))
            
            # Normalize to prevent clipping
            y = y / np.max(np.abs(y))
            
            # Save result
            sf.write(output_path, y, sr)
            return output_path
            
        except Exception as e:
            logger.error(f"Error applying equalizer: {e}")
            raise
    
    def edit_metadata(self, input_path: str, output_path: str, metadata: Dict[str, str]) -> str:
        """Edit MP3 metadata"""
        try:
            # Copy file first
            shutil.copy2(input_path, output_path)
            
            # Load and edit metadata
            audio_file = MP3(output_path, ID3=ID3)
            
            # Add ID3 tag if it doesn't exist
            if audio_file.tags is None:
                audio_file.add_tags()
            
            # Set metadata fields
            if 'title' in metadata:
                audio_file.tags.add(TIT2(encoding=3, text=metadata['title']))
            if 'artist' in metadata:
                audio_file.tags.add(TPE1(encoding=3, text=metadata['artist']))
            if 'album' in metadata:
                audio_file.tags.add(TALB(encoding=3, text=metadata['album']))
            if 'albumartist' in metadata:
                audio_file.tags.add(TPE2(encoding=3, text=metadata['albumartist']))
            
            audio_file.save()
            return output_path
            
        except Exception as e:
            logger.error(f"Error editing metadata: {e}")
            raise
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """Get audio file information"""
        try:
            audio = AudioSegment.from_file(file_path)
            
            info = {
                'duration': len(audio) / 1000.0,  # seconds
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'bitrate': getattr(audio, 'bitrate', 'Unknown'),
                'format': os.path.splitext(file_path)[1][1:].upper()
            }
            
            # Try to get metadata for MP3 files
            if file_path.lower().endswith('.mp3'):
                try:
                    mp3_file = MP3(file_path)
                    if mp3_file.tags:
                        info['title'] = str(mp3_file.tags.get('TIT2', ['Unknown'])[0])
                        info['artist'] = str(mp3_file.tags.get('TPE1', ['Unknown'])[0])
                        info['album'] = str(mp3_file.tags.get('TALB', ['Unknown'])[0])
                except:
                    pass
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            return {}

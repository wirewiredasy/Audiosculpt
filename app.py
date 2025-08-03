"""
Flask Application - Compatible with existing workflow
Provides full ODOREMOVER functionality with improved UI
"""
import os
import uuid
import json
import asyncio
import logging
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

# Audio processing imports
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.id3._frames import TIT2, TPE1, TALB, TPE2
from scipy import signal

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Supported audio formats
SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']

# Thread pool for async processing
executor = ThreadPoolExecutor(max_workers=4)

class AudioProcessor:
    """Audio processing service with all 11 features"""
    
    @staticmethod
    def validate_audio_file(file_path: str) -> bool:
        """Validate if file is a supported audio format"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in SUPPORTED_FORMATS:
                return False
            AudioSegment.from_file(file_path)
            return True
        except Exception as e:
            logger.error(f"Invalid audio file {file_path}: {e}")
            return False
    
    @staticmethod
    def get_audio_info(file_path: str) -> Dict[str, Any]:
        """Get audio file information"""
        try:
            audio = AudioSegment.from_file(file_path)
            
            info = {
                'duration': len(audio) / 1000.0,  # seconds
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
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
            raise
    
    @staticmethod
    def separate_vocals(input_path: str) -> Dict[str, Any]:
        """Separate vocals using center channel extraction"""
        try:
            audio = AudioSegment.from_file(input_path)
            samples = np.array(audio.get_array_of_samples())
            
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
                vocals = (samples[:, 0] + samples[:, 1]) / 2
                instrumental = (samples[:, 0] - samples[:, 1]) / 2
                
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
                vocals_audio = audio
                instrumental_audio = AudioSegment.silent(duration=len(audio))
            
            vocals_filename = f"vocals_{uuid.uuid4()}.wav"
            instrumental_filename = f"instrumental_{uuid.uuid4()}.wav"
            
            vocals_path = os.path.join(app.config['PROCESSED_FOLDER'], vocals_filename)
            instrumental_path = os.path.join(app.config['PROCESSED_FOLDER'], instrumental_filename)
            
            vocals_audio.export(vocals_path, format='wav')
            instrumental_audio.export(instrumental_path, format='wav')
            
            return {
                'success': True,
                'vocals_file': vocals_filename,
                'instrumental_file': instrumental_filename,
                'message': "Vocal separation completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error in vocal separation: {e}")
            return {'success': False, 'error': f"Vocal separation failed: {str(e)}"}
    
    @staticmethod
    def change_pitch_tempo(input_path: str, pitch_shift: float = 0, tempo_change: float = 1.0) -> Dict[str, Any]:
        """Change pitch and tempo using librosa"""
        try:
            y, sr = librosa.load(input_path, sr=None)
            
            if pitch_shift != 0:
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=pitch_shift)
            
            if tempo_change != 1.0:
                y = librosa.effects.time_stretch(y, rate=tempo_change)
            
            output_filename = f"pitch_tempo_{uuid.uuid4()}.wav"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            sf.write(output_path, y, sr)
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': "Pitch and tempo adjustment completed"
            }
            
        except Exception as e:
            logger.error(f"Error in pitch/tempo change: {e}")
            return {'success': False, 'error': f"Pitch/tempo change failed: {str(e)}"}
    
    @staticmethod
    def convert_format(input_path: str, output_format: str) -> Dict[str, Any]:
        """Convert audio to different format"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            export_params = {}
            if output_format.lower() == 'mp3':
                export_params = {'bitrate': '320k'}
            elif output_format.lower() == 'ogg':
                export_params = {'codec': 'libvorbis'}
            
            output_filename = f"converted_{uuid.uuid4()}.{output_format}"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            
            audio.export(output_path, format=output_format.lower(), **export_params)
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Converted to {output_format.upper()} format"
            }
            
        except Exception as e:
            logger.error(f"Error in format conversion: {e}")
            return {'success': False, 'error': f"Format conversion failed: {str(e)}"}
    
    @staticmethod
    def cut_audio(input_path: str, start_time: float, end_time: float) -> Dict[str, Any]:
        """Cut audio segment"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)
            
            cut_audio = audio[start_ms:end_ms]
            
            output_filename = f"cut_{uuid.uuid4()}.wav"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            cut_audio.export(output_path, format='wav')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Audio cut from {start_time}s to {end_time}s"
            }
            
        except Exception as e:
            logger.error(f"Error cutting audio: {e}")
            return {'success': False, 'error': f"Audio cutting failed: {str(e)}"}
    
    @staticmethod
    def reduce_noise(input_path: str, noise_factor: float = 0.5) -> Dict[str, Any]:
        """Reduce noise using spectral gating"""
        try:
            y, sr = librosa.load(input_path, sr=None)
            
            stft = librosa.stft(y)
            magnitude = np.abs(stft)
            
            threshold = np.percentile(magnitude, 20 * (1 - noise_factor))
            mask = magnitude > threshold
            
            stft_filtered = stft * mask
            reduced_noise = librosa.istft(stft_filtered)
            
            output_filename = f"denoised_{uuid.uuid4()}.wav"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            sf.write(output_path, reduced_noise, sr)
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': "Noise reduction completed"
            }
            
        except Exception as e:
            logger.error(f"Error in noise reduction: {e}")
            return {'success': False, 'error': f"Noise reduction failed: {str(e)}"}
    
    @staticmethod
    def normalize_volume(input_path: str, target_dBFS: float = -20.0) -> Dict[str, Any]:
        """Normalize audio volume"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            change_in_dBFS = target_dBFS - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dBFS)
            
            output_filename = f"normalized_{uuid.uuid4()}.wav"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            normalized_audio.export(output_path, format='wav')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': f"Volume normalized to {target_dBFS}dB"
            }
            
        except Exception as e:
            logger.error(f"Error normalizing volume: {e}")
            return {'success': False, 'error': f"Volume normalization failed: {str(e)}"}
    
    @staticmethod
    def apply_fade(input_path: str, fade_in_duration: float = 0, fade_out_duration: float = 0) -> Dict[str, Any]:
        """Apply fade in/out effects"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            if fade_in_duration > 0:
                audio = audio.fade_in(int(fade_in_duration * 1000))
            
            if fade_out_duration > 0:
                audio = audio.fade_out(int(fade_out_duration * 1000))
            
            output_filename = f"faded_{uuid.uuid4()}.wav"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            audio.export(output_path, format='wav')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': "Fade effects applied successfully"
            }
            
        except Exception as e:
            logger.error(f"Error applying fade: {e}")
            return {'success': False, 'error': f"Fade application failed: {str(e)}"}
    
    @staticmethod
    def reverse_audio(input_path: str) -> Dict[str, Any]:
        """Reverse audio playback"""
        try:
            audio = AudioSegment.from_file(input_path)
            reversed_audio = audio.reverse()
            
            output_filename = f"reversed_{uuid.uuid4()}.wav"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            reversed_audio.export(output_path, format='wav')
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': "Audio reversed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error reversing audio: {e}")
            return {'success': False, 'error': f"Audio reversal failed: {str(e)}"}
    
    @staticmethod
    def apply_equalizer(input_path: str, low_gain: float = 0, mid_gain: float = 0, high_gain: float = 0) -> Dict[str, Any]:
        """Apply 3-band equalizer"""
        try:
            y, sr = librosa.load(input_path, sr=None)
            
            low_freq = 300
            high_freq = 3000
            nyquist = sr / 2
            
            if low_gain != 0:
                low_sos = signal.butter(4, low_freq / nyquist, btype='low', output='sos')
                low_filtered = signal.sosfilt(low_sos, y)
                low_filtered = low_filtered * (10 ** (low_gain / 20))
                y = y + (low_filtered - signal.sosfilt(low_sos, y))
            
            if high_gain != 0:
                high_sos = signal.butter(4, high_freq / nyquist, btype='high', output='sos')
                high_filtered = signal.sosfilt(high_sos, y)
                high_filtered = high_filtered * (10 ** (high_gain / 20))
                y = y + (high_filtered - signal.sosfilt(high_sos, y))
            
            if mid_gain != 0:
                mid_sos = signal.butter(4, [low_freq / nyquist, high_freq / nyquist], btype='band', output='sos')
                mid_filtered = signal.sosfilt(mid_sos, y)
                mid_filtered = mid_filtered * (10 ** (mid_gain / 20))
                y = y + (mid_filtered - signal.sosfilt(mid_sos, y))
            
            y = y / np.max(np.abs(y))
            
            output_filename = f"equalized_{uuid.uuid4()}.wav"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            sf.write(output_path, y, sr)
            
            return {
                'success': True,
                'processed_file': output_filename,
                'message': "Equalizer applied successfully"
            }
            
        except Exception as e:
            logger.error(f"Error applying equalizer: {e}")
            return {'success': False, 'error': f"Equalizer application failed: {str(e)}"}
    
    @staticmethod
    def edit_metadata(input_path: str, metadata: Dict[str, str]) -> Dict[str, Any]:
        """Edit MP3 metadata"""
        try:
            output_filename = f"metadata_{uuid.uuid4()}.mp3"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            
            # Copy file first
            import shutil
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

# Routes
@app.route('/')
def index():
    """Main application page with modern UI"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """Upload and validate audio file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    if not file.filename:
        return jsonify({'error': 'Invalid filename'}), 400
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in SUPPORTED_FORMATS:
        return jsonify({'error': f"Unsupported format. Allowed: {', '.join(SUPPORTED_FORMATS)}"}), 400
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Save file
    file.save(file_path)
    
    # Get audio info
    try:
        audio_info = AudioProcessor.get_audio_info(file_path)
        audio_info['file_id'] = unique_filename
        audio_info['original_name'] = file.filename
        return jsonify(audio_info)
    except Exception as e:
        return jsonify({'error': f"Failed to process file: {str(e)}"}), 500

@app.route('/api/process/vocal-separation', methods=['POST'])
def separate_vocals():
    """Separate vocals from instrumental"""
    data = request.get_json()
    file_id = data.get('file_id')
    
    if not file_id:
        return jsonify({'error': 'File ID required'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    result = AudioProcessor.separate_vocals(file_path)
    return jsonify(result)

@app.route('/api/process/pitch-tempo', methods=['POST'])
def adjust_pitch_tempo():
    """Adjust pitch and tempo"""
    file_id = request.form.get('file_id')
    try:
        pitch_shift = float(request.form.get('pitch_shift', 0))
        tempo_change = float(request.form.get('tempo_change', 1.0))
    except ValueError:
        return jsonify({'error': 'Invalid numeric values'}), 400
    
    if not file_id:
        return jsonify({'error': 'File ID required'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    result = AudioProcessor.change_pitch_tempo(file_path, pitch_shift, tempo_change)
    return jsonify(result)

@app.route('/api/process/convert', methods=['POST'])
def convert_format():
    """Convert audio format"""
    file_id = request.form.get('file_id')
    output_format = request.form.get('output_format')
    
    if not file_id or not output_format:
        return jsonify({'error': 'File ID and output format required'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    result = AudioProcessor.convert_format(file_path, output_format)
    return jsonify(result)

@app.route('/api/process/cut', methods=['POST'])
def cut_audio():
    """Cut audio segment"""
    file_id = request.form.get('file_id')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    
    if not start_time_str or not end_time_str:
        return jsonify({'error': 'Start time and end time required'}), 400
    
    try:
        start_time = float(start_time_str)
        end_time = float(end_time_str)
    except ValueError:
        return jsonify({'error': 'Invalid time values'}), 400
    
    if not file_id:
        return jsonify({'error': 'File ID required'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    result = AudioProcessor.cut_audio(file_path, start_time, end_time)
    return jsonify(result)

@app.route('/api/process/noise-reduction', methods=['POST'])
def reduce_noise():
    """Reduce background noise"""
    file_id = request.form.get('file_id')
    try:
        noise_factor = float(request.form.get('noise_factor', 0.5))
    except ValueError:
        return jsonify({'error': 'Invalid noise factor value'}), 400
    
    if not file_id:
        return jsonify({'error': 'File ID required'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    result = AudioProcessor.reduce_noise(file_path, noise_factor)
    return jsonify(result)

@app.route('/api/process/normalize', methods=['POST'])
def normalize_volume():
    """Normalize audio volume"""
    file_id = request.form.get('file_id')
    try:
        target_db = float(request.form.get('target_db', -20.0))
    except ValueError:
        return jsonify({'error': 'Invalid target dB value'}), 400
    
    if not file_id:
        return jsonify({'error': 'File ID required'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    result = AudioProcessor.normalize_volume(file_path, target_db)
    return jsonify(result)

@app.route('/api/process/fade', methods=['POST'])
def apply_fade():
    """Apply fade in/out effects"""
    file_id = request.form.get('file_id')
    fade_in = float(request.form.get('fade_in', 0))
    fade_out = float(request.form.get('fade_out', 0))
    
    if not file_id:
        return jsonify({'error': 'File ID required'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    result = AudioProcessor.apply_fade(file_path, fade_in, fade_out)
    return jsonify(result)

@app.route('/api/process/reverse', methods=['POST'])
def reverse_audio():
    """Reverse audio playback"""
    data = request.get_json()
    file_id = data.get('file_id')
    
    if not file_id:
        return jsonify({'error': 'File ID required'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    result = AudioProcessor.reverse_audio(file_path)
    return jsonify(result)

@app.route('/api/process/equalizer', methods=['POST'])
def apply_equalizer():
    """Apply 3-band equalizer"""
    file_id = request.form.get('file_id')
    low_gain = float(request.form.get('low_gain', 0))
    mid_gain = float(request.form.get('mid_gain', 0))
    high_gain = float(request.form.get('high_gain', 0))
    
    if not file_id:
        return jsonify({'error': 'File ID required'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    result = AudioProcessor.apply_equalizer(file_path, low_gain, mid_gain, high_gain)
    return jsonify(result)

@app.route('/api/process/metadata', methods=['POST'])
def edit_metadata():
    """Edit MP3 metadata"""
    file_id = request.form.get('file_id')
    
    if not file_id:
        return jsonify({'error': 'File ID required'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    if not file_path.lower().endswith('.mp3'):
        return jsonify({'error': 'Metadata editing only supported for MP3 files'}), 400
    
    metadata = {}
    if request.form.get('title'): metadata['title'] = request.form.get('title')
    if request.form.get('artist'): metadata['artist'] = request.form.get('artist')
    if request.form.get('album'): metadata['album'] = request.form.get('album')
    if request.form.get('album_artist'): metadata['albumartist'] = request.form.get('album_artist')
    
    result = AudioProcessor.edit_metadata(file_path, metadata)
    return jsonify(result)

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download processed file"""
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=filename)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "ODOREMOVER Audio Processing API"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
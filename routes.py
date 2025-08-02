import os
import uuid
import json
import logging
from flask import render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from app import app
from audio_processor import AudioProcessor

logger = logging.getLogger(__name__)

# Global processor instance
audio_processor = AudioProcessor()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['mp3', 'wav', 'flac', 'ogg', 'm4a']

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file format'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename or 'upload')
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Validate audio file
        if not audio_processor.validate_audio_file(file_path):
            os.remove(file_path)
            return jsonify({'error': 'Invalid audio file'}), 400
        
        # Get audio info
        audio_info = audio_processor.get_audio_info(file_path)
        
        return jsonify({
            'success': True,
            'file_id': unique_filename,
            'original_name': filename,
            'audio_info': audio_info
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/process', methods=['POST'])
def process_audio():
    """Process audio with specified operation"""
    try:
        data = request.get_json()
        operation = data.get('operation')
        file_id = data.get('file_id')
        params = data.get('params', {})
        
        if not file_id:
            return jsonify({'error': 'No file specified'}), 400
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(input_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Generate output filename
        output_filename = f"processed_{uuid.uuid4()}.wav"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # Process based on operation
        if operation == 'vocal_removal':
            vocals_path, instrumental_path = audio_processor.separate_vocals(
                input_path, app.config['PROCESSED_FOLDER']
            )
            return jsonify({
                'success': True,
                'vocals_file': os.path.basename(vocals_path),
                'instrumental_file': os.path.basename(instrumental_path)
            })
            
        elif operation == 'pitch_tempo':
            pitch_shift = float(params.get('pitch_shift', 0))
            tempo_change = float(params.get('tempo_change', 1.0))
            audio_processor.change_pitch_tempo(input_path, output_path, pitch_shift, tempo_change)
            
        elif operation == 'convert':
            output_format = params.get('format', 'wav')
            output_filename = f"converted_{uuid.uuid4()}.{output_format}"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            audio_processor.convert_format(input_path, output_path, output_format)
            
        elif operation == 'cut':
            start_time = float(params.get('start_time', 0))
            end_time = float(params.get('end_time', 10))
            audio_processor.cut_audio(input_path, output_path, start_time, end_time)
            
        elif operation == 'noise_reduction':
            noise_factor = float(params.get('noise_factor', 0.5))
            audio_processor.reduce_noise(input_path, output_path, noise_factor)
            
        elif operation == 'normalize':
            target_db = float(params.get('target_db', -20.0))
            audio_processor.normalize_volume(input_path, output_path, target_db)
            
        elif operation == 'fade':
            fade_in = float(params.get('fade_in', 0))
            fade_out = float(params.get('fade_out', 0))
            audio_processor.apply_fade(input_path, output_path, fade_in, fade_out)
            
        elif operation == 'reverse':
            audio_processor.reverse_audio(input_path, output_path)
            
        elif operation == 'equalizer':
            low_gain = float(params.get('low_gain', 0))
            mid_gain = float(params.get('mid_gain', 0))
            high_gain = float(params.get('high_gain', 0))
            audio_processor.apply_equalizer(input_path, output_path, low_gain, mid_gain, high_gain)
            
        elif operation == 'metadata':
            if not input_path.lower().endswith('.mp3'):
                return jsonify({'error': 'Metadata editing only supported for MP3 files'}), 400
            output_filename = f"metadata_{uuid.uuid4()}.mp3"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            metadata = params.get('metadata', {})
            audio_processor.edit_metadata(input_path, output_path, metadata)
            
        else:
            return jsonify({'error': 'Unknown operation'}), 400
        
        return jsonify({
            'success': True,
            'processed_file': os.path.basename(output_path)
        })
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download processed file"""
    try:
        file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': 'Download failed'}), 500

@app.route('/audio_info/<file_id>')
def get_audio_info(file_id):
    """Get audio file information"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        info = audio_processor.get_audio_info(file_path)
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"Info error: {e}")
        return jsonify({'error': 'Failed to get audio info'}), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 500MB.'}), 413

@app.errorhandler(500)
def server_error(e):
    """Handle server errors"""
    logger.error(f"Server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

/**
 * Modern ODOREMOVER Application
 * FastAPI + Microservices Architecture
 */

class ModernAudioApp {
    constructor() {
        this.currentFileId = null;
        this.uploadedFileName = null;
        this.init();
    }

    init() {
        this.setupFileUpload();
        this.setupToolCards();
        this.setupModalHandlers();
        this.animateOnScroll();
    }

    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        // Drag and drop handlers
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });

        // Click to upload
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
    }

    setupToolCards() {
        const toolCards = document.querySelectorAll('.tool-card');
        
        toolCards.forEach(card => {
            card.addEventListener('click', () => {
                if (!this.currentFileId) {
                    this.showAlert('Please upload an audio file first', 'warning');
                    return;
                }
                
                const tool = card.getAttribute('data-tool');
                this.openProcessingModal(tool);
            });
        });
    }

    setupModalHandlers() {
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('processing-form')) {
                e.preventDefault();
                this.processAudio(e.target);
            }
        });

        // Dynamic range slider updates
        document.addEventListener('input', (e) => {
            if (e.target.type === 'range') {
                this.updateRangeDisplay(e.target);
            }
        });
    }

    async handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        this.showLoading('Uploading file...');

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.currentFileId = result.file_id;
                this.uploadedFileName = result.original_name;
                this.displayFileInfo(result);
                this.showToolsSection();
                this.hideLoading();
                this.showAlert('File uploaded successfully!', 'success');
            } else {
                throw new Error(result.detail || 'Upload failed');
            }
        } catch (error) {
            this.hideLoading();
            this.showAlert(`Upload failed: ${error.message}`, 'error');
        }
    }

    displayFileInfo(fileInfo) {
        const fileInfoSection = document.getElementById('fileInfoSection');
        const fileInfoContent = document.getElementById('fileInfoContent');

        fileInfoContent.innerHTML = `
            <div class="row align-items-center">
                <div class="col-md-2">
                    <div class="file-icon">
                        <i class="fas fa-file-audio fa-3x"></i>
                    </div>
                </div>
                <div class="col-md-10">
                    <h4 class="mb-3">${fileInfo.original_name}</h4>
                    <div class="row">
                        <div class="col-md-4">
                            <p><strong>Duration:</strong> ${this.formatDuration(fileInfo.duration)}</p>
                            <p><strong>Format:</strong> ${fileInfo.format}</p>
                        </div>
                        <div class="col-md-4">
                            <p><strong>Channels:</strong> ${fileInfo.channels === 1 ? 'Mono' : 'Stereo'}</p>
                            <p><strong>Sample Rate:</strong> ${fileInfo.frame_rate} Hz</p>
                        </div>
                        <div class="col-md-4">
                            <p><strong>Bit Depth:</strong> ${fileInfo.sample_width * 8}-bit</p>
                            ${fileInfo.title ? `<p><strong>Title:</strong> ${fileInfo.title}</p>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;

        fileInfoSection.style.display = 'block';
        fileInfoSection.classList.add('fade-in');
    }

    showToolsSection() {
        const toolsSection = document.getElementById('toolsSection');
        toolsSection.style.display = 'block';
        toolsSection.classList.add('slide-up');
        
        // Scroll to tools section
        setTimeout(() => {
            toolsSection.scrollIntoView({ behavior: 'smooth' });
        }, 300);
    }

    openProcessingModal(tool) {
        const modal = new bootstrap.Modal(document.getElementById('processingModal'));
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');

        modalTitle.textContent = this.getToolTitle(tool);
        modalBody.innerHTML = this.getToolForm(tool);

        modal.show();
    }

    getToolTitle(tool) {
        const titles = {
            'vocal-separation': 'Vocal Separation',
            'pitch-tempo': 'Pitch & Tempo Adjustment',
            'convert': 'Format Conversion',
            'cut': 'Audio Cutting',
            'noise-reduction': 'Noise Reduction',
            'normalize': 'Volume Normalization',
            'fade': 'Fade Effects',
            'reverse': 'Reverse Audio',
            'equalizer': '3-Band Equalizer',
            'metadata': 'Metadata Editor'
        };
        return titles[tool] || 'Audio Processing';
    }

    getToolForm(tool) {
        switch (tool) {
            case 'vocal-separation':
                return `
                    <form class="processing-form" data-tool="vocal-separation">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            This will separate your audio into vocals and instrumental tracks using advanced AI processing.
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-microphone-slash"></i> Separate Vocals
                        </button>
                    </form>
                `;

            case 'pitch-tempo':
                return `
                    <form class="processing-form" data-tool="pitch-tempo">
                        <div class="mb-4">
                            <label class="form-label">Pitch Shift (semitones)</label>
                            <input type="range" class="form-range" name="pitch_shift" min="-12" max="12" value="0" step="1">
                            <div class="d-flex justify-content-between small text-muted">
                                <span>-12</span><span id="pitchValue" class="fw-bold">0</span><span>+12</span>
                            </div>
                        </div>
                        <div class="mb-4">
                            <label class="form-label">Tempo Change</label>
                            <input type="range" class="form-range" name="tempo_change" min="0.5" max="2.0" value="1.0" step="0.1">
                            <div class="d-flex justify-content-between small text-muted">
                                <span>0.5x</span><span id="tempoValue" class="fw-bold">1.0x</span><span>2.0x</span>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-tune"></i> Apply Changes
                        </button>
                    </form>
                `;

            case 'convert':
                return `
                    <form class="processing-form" data-tool="convert">
                        <div class="mb-4">
                            <label class="form-label">Output Format</label>
                            <select class="form-select" name="output_format" required>
                                <option value="">Choose format...</option>
                                <option value="mp3">MP3 (320kbps)</option>
                                <option value="wav">WAV (Uncompressed)</option>
                                <option value="flac">FLAC (Lossless)</option>
                                <option value="ogg">OGG Vorbis</option>
                                <option value="m4a">M4A (AAC)</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-exchange-alt"></i> Convert Audio
                        </button>
                    </form>
                `;

            case 'cut':
                return `
                    <form class="processing-form" data-tool="cut">
                        <div class="mb-3">
                            <label class="form-label">Start Time (seconds)</label>
                            <input type="number" class="form-control" name="start_time" min="0" step="0.1" value="0" required>
                        </div>
                        <div class="mb-4">
                            <label class="form-label">End Time (seconds)</label>
                            <input type="number" class="form-control" name="end_time" min="0" step="0.1" value="30" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-cut"></i> Cut Audio
                        </button>
                    </form>
                `;

            case 'noise-reduction':
                return `
                    <form class="processing-form" data-tool="noise-reduction">
                        <div class="mb-4">
                            <label class="form-label">Noise Reduction Level</label>
                            <input type="range" class="form-range" name="noise_factor" min="0.1" max="1.0" value="0.5" step="0.1">
                            <div class="d-flex justify-content-between small text-muted">
                                <span>Light</span><span id="noiseValue" class="fw-bold">Medium</span><span>Heavy</span>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-volume-xmark"></i> Reduce Noise
                        </button>
                    </form>
                `;

            case 'normalize':
                return `
                    <form class="processing-form" data-tool="normalize">
                        <div class="mb-4">
                            <label class="form-label">Target Volume (dBFS)</label>
                            <input type="range" class="form-range" name="target_db" min="-30" max="0" value="-20" step="1">
                            <div class="d-flex justify-content-between small text-muted">
                                <span>-30dB</span><span id="dbValue" class="fw-bold">-20dB</span><span>0dB</span>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-volume-up"></i> Normalize Volume
                        </button>
                    </form>
                `;

            case 'fade':
                return `
                    <form class="processing-form" data-tool="fade">
                        <div class="mb-3">
                            <label class="form-label">Fade In Duration (seconds)</label>
                            <input type="number" class="form-control" name="fade_in" min="0" step="0.1" value="0">
                        </div>
                        <div class="mb-4">
                            <label class="form-label">Fade Out Duration (seconds)</label>
                            <input type="number" class="form-control" name="fade_out" min="0" step="0.1" value="0">
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-chart-line"></i> Apply Fade Effects
                        </button>
                    </form>
                `;

            case 'reverse':
                return `
                    <form class="processing-form" data-tool="reverse">
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle"></i>
                            This will completely reverse the audio playback. This effect cannot be undone.
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-backward"></i> Reverse Audio
                        </button>
                    </form>
                `;

            case 'equalizer':
                return `
                    <form class="processing-form" data-tool="equalizer">
                        <div class="row mb-4">
                            <div class="col-4 text-center">
                                <label class="form-label">Low (±20dB)</label>
                                <input type="range" class="form-range vertical-range" name="low_gain" min="-20" max="20" value="0" step="1" orient="vertical">
                                <span id="lowValue" class="fw-bold">0dB</span>
                            </div>
                            <div class="col-4 text-center">
                                <label class="form-label">Mid (±20dB)</label>
                                <input type="range" class="form-range vertical-range" name="mid_gain" min="-20" max="20" value="0" step="1" orient="vertical">
                                <span id="midValue" class="fw-bold">0dB</span>
                            </div>
                            <div class="col-4 text-center">
                                <label class="form-label">High (±20dB)</label>
                                <input type="range" class="form-range vertical-range" name="high_gain" min="-20" max="20" value="0" step="1" orient="vertical">
                                <span id="highValue" class="fw-bold">0dB</span>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-sliders-h"></i> Apply Equalizer
                        </button>
                    </form>
                `;

            case 'metadata':
                return `
                    <form class="processing-form" data-tool="metadata">
                        <div class="mb-3">
                            <label class="form-label">Title</label>
                            <input type="text" class="form-control" name="title" placeholder="Song title">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Artist</label>
                            <input type="text" class="form-control" name="artist" placeholder="Artist name">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Album</label>
                            <input type="text" class="form-control" name="album" placeholder="Album name">
                        </div>
                        <div class="mb-4">
                            <label class="form-label">Album Artist</label>
                            <input type="text" class="form-control" name="album_artist" placeholder="Album artist">
                        </div>
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            Metadata editing is only supported for MP3 files.
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-tags"></i> Save Metadata
                        </button>
                    </form>
                `;

            default:
                return '<p>Processing form not available for this tool.</p>';
        }
    }

    async processAudio(form) {
        const tool = form.getAttribute('data-tool');
        const formData = new FormData(form);
        
        // Add file_id to form data
        formData.append('file_id', this.currentFileId);

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('processingModal'));
        modal.hide();

        this.showLoading(`Processing ${this.getToolTitle(tool).toLowerCase()}...`);

        try {
            let endpoint;
            switch (tool) {
                case 'vocal-separation':
                    endpoint = '/api/process/vocal-separation';
                    break;
                case 'pitch-tempo':
                    endpoint = '/api/process/pitch-tempo';
                    break;
                case 'convert':
                    endpoint = '/api/process/convert';
                    break;
                case 'cut':
                    endpoint = '/api/process/cut';
                    break;
                case 'noise-reduction':
                    endpoint = '/api/process/noise-reduction';
                    break;
                case 'normalize':
                    endpoint = '/api/process/normalize';
                    break;
                case 'fade':
                    endpoint = '/api/process/fade';
                    break;
                case 'reverse':
                    endpoint = '/api/process/reverse';
                    // For reverse, we need JSON
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ file_id: this.currentFileId })
                    });
                    const result = await response.json();
                    this.handleProcessingResult(result, tool);
                    return;
                case 'equalizer':
                    endpoint = '/api/process/equalizer';
                    break;
                case 'metadata':
                    endpoint = '/api/process/metadata';
                    break;
                default:
                    throw new Error('Unknown processing tool');
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            this.handleProcessingResult(result, tool);

        } catch (error) {
            this.hideLoading();
            this.showAlert(`Processing failed: ${error.message}`, 'error');
        }
    }

    handleProcessingResult(result, tool) {
        this.hideLoading();

        if (result.success) {
            if (tool === 'vocal-separation') {
                this.displayVocalSeparationResults(result);
            } else {
                this.displayProcessingResults(result, tool);
            }
            this.showAlert('Processing completed successfully!', 'success');
        } else {
            this.showAlert(`Processing failed: ${result.error}`, 'error');
        }
    }

    displayVocalSeparationResults(result) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsContent = document.getElementById('resultsContent');

        resultsContent.innerHTML = `
            <div class="row">
                <div class="col-12 mb-4">
                    <h3><i class="fas fa-microphone-slash"></i> Vocal Separation Results</h3>
                </div>
                <div class="col-md-6">
                    <div class="result-card">
                        <h5><i class="fas fa-microphone"></i> Vocals Track</h5>
                        <p>Extracted vocal elements from your audio</p>
                        <a href="/api/download/${result.vocals_file}" class="btn btn-primary">
                            <i class="fas fa-download"></i> Download Vocals
                        </a>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="result-card">
                        <h5><i class="fas fa-music"></i> Instrumental Track</h5>
                        <p>Background music without vocals</p>
                        <a href="/api/download/${result.instrumental_file}" class="btn btn-primary">
                            <i class="fas fa-download"></i> Download Instrumental
                        </a>
                    </div>
                </div>
            </div>
        `;

        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    displayProcessingResults(result, tool) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsContent = document.getElementById('resultsContent');

        resultsContent.innerHTML = `
            <div class="result-card">
                <h4><i class="fas fa-check-circle text-success"></i> ${this.getToolTitle(tool)} Complete</h4>
                <p>${result.message || 'Your audio has been processed successfully.'}</p>
                <a href="/api/download/${result.processed_file}" class="btn btn-primary">
                    <i class="fas fa-download"></i> Download Processed Audio
                </a>
            </div>
        `;

        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    updateRangeDisplay(slider) {
        const value = slider.value;
        const name = slider.name;

        switch (name) {
            case 'pitch_shift':
                document.getElementById('pitchValue').textContent = value;
                break;
            case 'tempo_change':
                document.getElementById('tempoValue').textContent = value + 'x';
                break;
            case 'noise_factor':
                const levels = ['Light', 'Light', 'Light-Med', 'Medium', 'Med-Heavy', 'Heavy', 'Heavy', 'Heavy', 'Heavy', 'Heavy'];
                document.getElementById('noiseValue').textContent = levels[Math.floor(value * 10)] || 'Medium';
                break;
            case 'target_db':
                document.getElementById('dbValue').textContent = value + 'dB';
                break;
            case 'low_gain':
                document.getElementById('lowValue').textContent = (value > 0 ? '+' : '') + value + 'dB';
                break;
            case 'mid_gain':
                document.getElementById('midValue').textContent = (value > 0 ? '+' : '') + value + 'dB';
                break;
            case 'high_gain':
                document.getElementById('highValue').textContent = (value > 0 ? '+' : '') + value + 'dB';
                break;
        }
    }

    showLoading(text = 'Processing...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        
        loadingText.textContent = text;
        overlay.classList.add('show');
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        overlay.classList.remove('show');
    }

    showAlert(message, type = 'info') {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        alert.style.top = '100px';
        alert.style.right = '20px';
        alert.style.zIndex = '9999';
        alert.style.minWidth = '300px';
        
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alert);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    formatDuration(seconds) {
        if (isNaN(seconds)) return '0:00';
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    animateOnScroll() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        });

        // Observe tool cards
        document.querySelectorAll('.tool-card').forEach(card => {
            observer.observe(card);
        });
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new ModernAudioApp();
});

// Add result card styles dynamically
const resultCardStyles = `
<style>
.result-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    padding: 2rem;
    backdrop-filter: blur(20px);
    margin-bottom: 2rem;
    text-align: center;
}

.result-card h4, .result-card h5 {
    margin-bottom: 1rem;
}

.result-card p {
    color: var(--text-muted);
    margin-bottom: 1.5rem;
}

.vertical-range {
    writing-mode: bt-lr;
    writing-mode: vertical-lr;
    width: 6px;
    height: 150px;
    margin: 1rem auto;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', resultCardStyles);
/**
 * Convertr — Vanilla JS Frontend Logic
 */

const API_BASE = '/api';

// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker Registered'))
            .catch(err => console.log('Service Worker Registration Failed', err));
    });
}

// DOM Elements
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const errorContainer = document.getElementById('error-container');
const fileInfo = document.getElementById('file-info');
const filenameDisplay = document.getElementById('filename-display');
const filesizeDisplay = document.getElementById('filesize-display');
const formatSelection = document.getElementById('format-selection');
const formatOptions = document.getElementById('format-options');
const convertBtn = document.getElementById('convert-btn');
const btnText = convertBtn.querySelector('.btn-text');
const spinner = convertBtn.querySelector('.spinner');
const successContainer = document.getElementById('success-container');
const downloadLink = document.getElementById('download-link');
const downloadText = document.getElementById('download-text');
const removeFileBtn = document.getElementById('remove-file-btn');

// Remove File Handler
removeFileBtn.onclick = (e) => {
    e.stopPropagation();
    resetUI();
    selectedFile = null;
    fileInput.value = ''; // Clear file input
};

// State
let selectedFile = null;
let uploadedFileRecord = null;
let targetFormat = null;
let availableFormats = {};

// Initialize
async function init() {
    try {
        const response = await fetch(`${API_BASE}/formats`);
        const data = await response.json();
        availableFormats = data.formats;
    } catch (err) {
        console.error('Failed to load formats:', err);
        showError('Warning: Could not connect to the server. Some features may not work.');
    }
}

init();

// Event Listeners
dropzone.addEventListener('click', () => fileInput.click());

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

async function handleFileSelect(file) {
    resetUI();
    selectedFile = file;

    // Show local file info
    filenameDisplay.textContent = file.name;
    filesizeDisplay.textContent = `(${(file.size / 1024).toFixed(1)} KB)`;
    fileInfo.style.display = 'block'; // Make sure the container is visible
    fileInfo.classList.remove('hidden');

    // Start upload immediately
    try {
        setLoading(true, 'Uploading...');
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/files`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Upload failed');
        }

        uploadedFileRecord = await response.json();
        showFormatOptions(uploadedFileRecord.format);
    } catch (err) {
        showError(err.message);
        fileInfo.classList.add('hidden');
    } finally {
        setLoading(false);
    }
}

function showFormatOptions(sourceFormat) {
    const targets = availableFormats[sourceFormat.toLowerCase()] || [];

    if (targets.length === 0) {
        showError(`Sorry, conversion for .${sourceFormat} is not supported yet.`);
        return;
    }

    formatOptions.innerHTML = '';
    targets.forEach(format => {
        const btn = document.createElement('button');
        btn.className = 'format-btn';
        btn.textContent = format;
        btn.onclick = () => selectFormat(format, btn);
        formatOptions.appendChild(btn);
    });

    formatSelection.classList.remove('hidden');

    // Auto-select if only one option
    if (targets.length === 1) {
        formatOptions.firstChild.click();
    }
}

function selectFormat(format, element) {
    targetFormat = format;

    // Update UI
    document.querySelectorAll('.format-btn').forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');

    convertBtn.classList.remove('hidden');
    convertBtn.disabled = false;
}

convertBtn.onclick = async () => {
    if (!uploadedFileRecord || !targetFormat) return;

    try {
        setLoading(true, 'Converting...');
        successContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');

        const response = await fetch(`${API_BASE}/convert`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                fileId: uploadedFileRecord.id,
                targetFormat: targetFormat
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Conversion failed');
        }

        const result = await response.json();
        showSuccess(result.fileId, result.filename);
    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(false);
    }
};

function showSuccess(fileId, filename) {
    const downloadUrl = `${API_BASE}/download/${fileId}`;
    downloadLink.href = downloadUrl;
    downloadText.textContent = `Download ${filename}`;
    successContainer.classList.remove('hidden');

    // Scroll to success
    successContainer.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function showError(msg) {
    errorContainer.textContent = msg;
    errorContainer.classList.remove('hidden');
}

function resetUI() {
    errorContainer.classList.add('hidden');
    fileInfo.classList.add('hidden');
    fileInfo.style.display = 'none';
    formatSelection.classList.add('hidden');
    convertBtn.classList.add('hidden');
    successContainer.classList.add('hidden');
    uploadedFileRecord = null;
    targetFormat = null;
}

function setLoading(isLoading, text = 'Processing...') {
    if (isLoading) {
        convertBtn.disabled = true;
        btnText.textContent = text;
        spinner.classList.remove('hidden');
        dropzone.style.pointerEvents = 'none';
        dropzone.style.opacity = '0.6';
    } else {
        convertBtn.disabled = false;
        btnText.textContent = 'Convert';
        spinner.classList.add('hidden');
        dropzone.style.pointerEvents = 'auto';
        dropzone.style.opacity = '1';
    }
}

// Feedback Modal Logic
const modal = document.getElementById('feedback-modal');
const feedbackTrigger = document.getElementById('feedback-trigger');
const closeModal = document.getElementById('close-modal');

feedbackTrigger.onclick = () => {
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent scroll
};

const closeFeedbackModal = () => {
    modal.classList.add('hidden');
    document.body.style.overflow = '';
};

closeModal.onclick = closeFeedbackModal;
window.onclick = (e) => {
    if (e.target === modal.querySelector('.modal-overlay')) {
        closeFeedbackModal();
    }
};

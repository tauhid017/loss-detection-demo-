// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewContainer = document.getElementById('previewContainer');
const previewImage = document.getElementById('previewImage');
const fileName = document.getElementById('fileName');
const generateBtn = document.getElementById('generateBtn');
const resultsSection = document.getElementById('resultsSection');
const loadingSection = document.getElementById('loadingSection');
const imageCaption = document.getElementById('imageCaption');
const lossDescription = document.getElementById('lossDescription');
const damageTypeDisplay = document.getElementById('damageTypeDisplay');
const downloadBtn = document.getElementById('downloadBtn');
const errorAlert = document.getElementById('errorAlert');
const errorMessage = document.getElementById('errorMessage');

// Event Listeners
if (uploadArea) {
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
}

if (fileInput) {
    fileInput.addEventListener('change', handleFileSelect);
}

if (generateBtn) {
    generateBtn.addEventListener('click', processImage);
}

if (downloadBtn) {
    downloadBtn.addEventListener('click', downloadDescription);
}

// Drag and Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFiles(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFiles(file);
    }
}

function handleFiles(file) {
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
        showError('Please select a valid image file (JPEG, PNG, or GIF)');
        return;
    }
    
    // Validate file size (max 16MB)
    if (file.size > 16 * 1024 * 1024) {
        showError('File size too large. Please select an image smaller than 16MB.');
        return;
    }
    
    // Display file name
    fileName.textContent = file.name;
    
    // Preview image
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImage.src = e.target.result;
        previewContainer.classList.remove('hidden');
        generateBtn.disabled = false;
    };
    reader.readAsDataURL(file);
    
    hideError();
}

async function processImage() {
    const file = fileInput.files[0];
    const damageType = document.getElementById('damageType').value;
    const customDamage = document.getElementById('customDamage').value;
    
    if (!file) {
        showError('Please select an image file first.');
        return;
    }
    
    // Show loading state
    showLoading();
    generateBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('damage_type', damageType);
    if (customDamage) {
        formData.append('custom_damage', customDamage);
    }
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
        } else {
            showError(data.error || 'An error occurred while processing the image.');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        hideLoading();
        generateBtn.disabled = false;
    }
}

function displayResults(data) {
    imageCaption.textContent = data.image_caption;
    lossDescription.textContent = data.loss_description;
    damageTypeDisplay.textContent = data.damage_type;
    
    // Store data for download
    downloadBtn.setAttribute('data-description', data.loss_description);
    downloadBtn.setAttribute('data-damage-type', data.damage_type);
    
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

async function downloadDescription() {
    const description = downloadBtn.getAttribute('data-description');
    const damageType = downloadBtn.getAttribute('data-damage-type');
    
    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description: description,
                damage_type: damageType
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `loss_description_${damageType.replace(' ', '_')}.txt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } else {
            showError('Failed to download file.');
        }
    } catch (error) {
        showError('Download error: ' + error.message);
    }
}

function showLoading() {
    loadingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
}

function hideLoading() {
    loadingSection.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorAlert.classList.remove('hidden');
    errorAlert.scrollIntoView({ behavior: 'smooth' });
}

function hideError() {
    errorAlert.classList.add('hidden');
}

// Custom damage type handling
document.getElementById('damageType').addEventListener('change', function() {
    const customDamageGroup = document.getElementById('customDamageGroup');
    if (this.value === 'Other') {
        customDamageGroup.classList.remove('hidden');
    } else {
        customDamageGroup.classList.add('hidden');
    }
});

// Initialize upload container
function initializeUploadContainer() {
    const uploadContainer = document.getElementById('uploadContainer');
    const imageSection = document.querySelector('.image-section');
    
    // Reset file input
    fileInput.value = '';
    
    // Hide preview and show upload area
    previewContainer.classList.add('hidden');
    imageSection.style.display = 'none';
    
    // Enable upload area
    uploadContainer.style.display = 'flex';
    uploadContainer.style.cursor = 'pointer';
    
    // Reset generate button
    generateBtn.disabled = true;
    
    // Clear any existing results
    resultsSection.classList.add('hidden');
}

// Sidebar functions
function openSidebar() {
    document.getElementById('sidebar').style.right = '0';
}

function closeSidebar() {
    document.getElementById('sidebar').style.right = '-400px';
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Loss Description Generator initialized');
});
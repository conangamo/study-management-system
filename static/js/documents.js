// Documents App JavaScript

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            if (alert.classList.contains('alert-dismissible')) {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);
});

// Confirm delete actions
function confirmDelete(message) {
    return confirm(message || 'Bạn có chắc chắn muốn xóa?');
}

// File upload progress (placeholder)
function showUploadProgress() {
    var progressBar = document.getElementById('upload-progress');
    if (progressBar) {
        progressBar.style.display = 'block';
    }
}

// Document delete function
function deleteDocument(documentId, documentTitle) {
    var message = 'Bạn có chắc chắn muốn xóa tài liệu "' + documentTitle + '"?';
    if (confirm(message)) {
        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/documents/' + documentId + '/delete/';

        var csrfToken = document.createElement('input');
        csrfToken.type = 'hidden';
        csrfToken.name = 'csrfmiddlewaretoken';
        csrfToken.value = document.querySelector('[name=csrfmiddlewaretoken]').value;

        form.appendChild(csrfToken);
        document.body.appendChild(form);
        form.submit();
    }
}

// Change view function
function changeView(view) {
    console.log('Switching to ' + view + ' view');
    // Implementation for view switching
}

// File upload drag and drop functionality
function initializeFileUpload() {
    const fileUploadAreas = document.querySelectorAll('.file-upload-area');
    
    fileUploadAreas.forEach(function(area) {
        const fileInput = area.querySelector('input[type="file"]');
        
        if (!fileInput) return;
        
        // Drag and drop events
        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                updateFileName(files[0], area);
            }
        });

        // Click to select file
        area.addEventListener('click', function() {
            fileInput.click();
        });

        // File input change
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                updateFileName(this.files[0], area);
            }
        });
    });
}

function updateFileName(file, area) {
    const fileName = file.name;
    const fileSize = (file.size / (1024 * 1024)).toFixed(2);
    
    area.innerHTML = `
        <i class="fas fa-file fa-2x text-success mb-2"></i>
        <p class="mb-1"><strong>${fileName}</strong></p>
        <p class="text-muted small">${fileSize} MB</p>
        <input type="file" name="file" style="display: none;">
    `;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
}); 
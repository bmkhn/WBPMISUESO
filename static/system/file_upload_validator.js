/**
 * Global File Upload Validator
 * Enforces maximum file size limit (10MB) for all file inputs across the system.
 * Synced with Django settings: DATA_UPLOAD_MAX_MEMORY_SIZE and FILE_UPLOAD_MAX_MEMORY_SIZE
 */

(function() {
    'use strict';
    
    // Maximum file size in bytes (10MB)
    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
    const MAX_FILE_SIZE_MB = 10;
    
    /**
     * Format bytes to human-readable format
     */
    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    /**
     * Show error message near file input
     */
    function showError(input, message) {
        // Remove all previous error messages related to this input
        // Remove from parent
        input.parentElement.querySelectorAll('.file-size-error').forEach(e => e.remove());
        // Remove from parent's parent (for upload-area)
        if (input.parentElement.parentElement) {
            input.parentElement.parentElement.querySelectorAll('.file-size-error').forEach(e => e.remove());
        }
        // Remove from upload-area ancestor
        const uploadArea = input.closest('.upload-area');
        if (uploadArea && uploadArea.parentElement) {
            uploadArea.parentElement.querySelectorAll('.file-size-error').forEach(e => e.remove());
        }

        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'file-size-error';
        errorDiv.style.cssText = 'color:#dc3545;font-size:0.875rem;margin-top:0.25rem;font-weight:500;';
        errorDiv.innerHTML = '<i class="fa-solid fa-exclamation-circle"></i> ' + message;

        // Insert after input or after its parent container
        if (input.parentElement.classList.contains('upload-area')) {
            input.parentElement.parentElement.insertBefore(errorDiv, input.parentElement.nextSibling);
        } else {
            input.parentElement.appendChild(errorDiv);
        }

        // Add error styling to input
        input.classList.add('is-invalid');
        if (uploadArea) {
            uploadArea.style.borderColor = '#dc3545';
        }
    }
    
    /**
     * Clear error message
     */
    function clearError(input) {
        // Remove all previous error messages related to this input
        input.parentElement.querySelectorAll('.file-size-error').forEach(e => e.remove());
        if (input.parentElement.parentElement) {
            input.parentElement.parentElement.querySelectorAll('.file-size-error').forEach(e => e.remove());
        }
        const uploadArea = input.closest('.upload-area');
        if (uploadArea && uploadArea.parentElement) {
            uploadArea.parentElement.querySelectorAll('.file-size-error').forEach(e => e.remove());
        }

        // Remove error styling
        input.classList.remove('is-invalid');
        if (uploadArea) {
            uploadArea.style.borderColor = '';
        }
    }
    
    /**
     * Validate file size
     */
    function validateFileSize(file) {
        return file.size <= MAX_FILE_SIZE;
    }
    
    /**
     * Handle file input change
     */
    function handleFileChange(event) {
        const input = event.target;
        const files = input.files;
        
        if (!files || files.length === 0) {
            clearError(input);
            return;
        }
        
        // Check each file
        let hasError = false;
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (!validateFileSize(file)) {
                showError(
                    input, 
                    `File "${file.name}" exceeds maximum size of ${MAX_FILE_SIZE_MB}MB (${formatBytes(file.size)} provided)`
                );
                input.value = ''; // Clear the input
                hasError = true;
                break;
            }
        }
        
        if (!hasError) {
            clearError(input);
        }
    }
    
    /**
     * Prevent form submission if any file input has oversized files
     */
    function preventOversizedSubmission(event) {
        const form = event.target;
        const fileInputs = form.querySelectorAll('input[type="file"]');
        let hasOversizedFile = false;
        
        fileInputs.forEach(input => {
            if (input.files && input.files.length > 0) {
                for (let i = 0; i < input.files.length; i++) {
                    const file = input.files[i];
                    if (!validateFileSize(file)) {
                        showError(
                            input, 
                            `File "${file.name}" exceeds maximum size of ${MAX_FILE_SIZE_MB}MB`
                        );
                        hasOversizedFile = true;
                        break;
                    }
                }
            }
        });
        
        if (hasOversizedFile) {
            event.preventDefault();
            event.stopPropagation();
            
            // Show alert
            alert(`Please remove files larger than ${MAX_FILE_SIZE_MB}MB before submitting.`);
            
            // Scroll to first error
            const firstError = form.querySelector('.file-size-error');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            
            return false;
        }
        
        return true;
    }
    
    /**
     * Add size limit hint to all file inputs
     */
    function addSizeHints() {
        document.querySelectorAll('input[type="file"]').forEach(input => {
            // Skip if hint already exists
            if (input.parentElement.querySelector('.file-size-hint')) {
                return;
            }
            
            // Create hint element
            const hint = document.createElement('small');
            hint.className = 'file-size-hint';
            hint.style.cssText = 'color:#6c757d;font-size:0.875rem;display:block;margin-top:0.25rem;';
            hint.innerHTML = '<i class="fa-solid fa-info-circle"></i> Maximum file size: ' + MAX_FILE_SIZE_MB + 'MB';
            
            // Insert hint
            if (input.parentElement.classList.contains('upload-area')) {
                input.parentElement.parentElement.insertBefore(hint, input.parentElement.nextSibling);
            } else {
                input.parentElement.appendChild(hint);
            }
        });
    }
    
    /**
     * Initialize validator
     */
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }
        
        // Add change listeners to all file inputs
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', handleFileChange);
        });
        
        // Add submit listeners to all forms with file inputs
        document.querySelectorAll('form').forEach(form => {
            if (form.querySelector('input[type="file"]')) {
                form.addEventListener('submit', preventOversizedSubmission);
            }
        });
        
        // Add size hints to all file inputs
        addSizeHints();
        
        // Watch for dynamically added file inputs
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // Check if the node itself is a file input
                        if (node.tagName === 'INPUT' && node.type === 'file') {
                            node.addEventListener('change', handleFileChange);
                            addSizeHints();
                        }
                        // Check for file inputs within the added node
                        const fileInputs = node.querySelectorAll?.('input[type="file"]');
                        if (fileInputs && fileInputs.length > 0) {
                            fileInputs.forEach(input => {
                                input.addEventListener('change', handleFileChange);
                            });
                            addSizeHints();
                        }
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    // Initialize
    init();
    
    // Expose utility function globally
    window.validateFileUpload = function(input) {
        if (input.files && input.files.length > 0) {
            return validateFileSize(input.files[0]);
        }
        return true;
    };
})();

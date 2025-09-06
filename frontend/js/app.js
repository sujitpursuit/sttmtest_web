/**
 * STTM Impact Analysis Tool - Alpine.js Application
 * Phase 1: File Upload and Validation
 */

/**
 * Main Alpine.js application for STTM Impact Analysis Tool
 * Handles file upload, validation, and workflow state management
 */
function sttmApp() {
    return {
        // State Management
        currentStep: 1,
        
        // File Management
        files: {
            sttm: null,
            qtest: null
        },
        
        // Drag and Drop State
        isDragOver: {
            sttm: false,
            qtest: false
        },
        
        // Validation Results
        validationResults: {
            sttm: null,
            qtest: null
        },
        
        // Loading States
        isLoading: {
            validation: false,
            upload: false,
            analysis: false,
            generation: false
        },
        
        // Current generation type
        generationType: null,
        
        // Analysis results
        analysisResult: null,
        
        // Generated files
        generatedFiles: [],
        
        // Workflow State
        workflow: {
            filesUploaded: false,
            filesValidated: false,
            impactAnalyzed: false,
            deltaGenerated: false,
            inPlaceGenerated: false
        },
        
        // UI Messages
        errorMessage: '',
        successMessage: '',
        
        // API Configuration
        apiBaseUrl: `${window.location.protocol}//${window.location.host}`,
        
        /**
         * Initialize the application
         * Called when Alpine.js component is mounted
         */
        init() {
            console.log('STTM App initialized - Phase 1');
            console.log('Alpine.js is working! Click handlers should work now.');
            this.loadFromStorage();
            this.updateWorkflowState();
        },
        
        /**
         * Handle file selection via file input
         * @param {Event} event - File input change event
         * @param {string} fileType - 'sttm' or 'qtest'
         */
        handleFileSelect(event, fileType) {
            const file = event.target.files[0];
            if (file) {
                this.processFile(file, fileType);
            }
        },
        
        /**
         * Handle file drop via drag and drop
         * @param {Event} event - Drop event
         * @param {string} fileType - 'sttm' or 'qtest'
         */
        handleFileDrop(event, fileType) {
            this.isDragOver[fileType] = false;
            const file = event.dataTransfer.files[0];
            if (file) {
                this.processFile(file, fileType);
            }
        },
        
        /**
         * Process uploaded file with client-side validation
         * @param {File} file - The uploaded file
         * @param {string} fileType - 'sttm' or 'qtest'
         */
        processFile(file, fileType) {
            // Client-side validation
            const validation = this.validateFile(file, fileType);
            
            if (!validation.valid) {
                this.showError(validation.message);
                return;
            }
            
            // Store the file
            this.files[fileType] = file;
            this.validationResults[fileType] = null; // Clear previous validation
            
            // Update workflow state
            this.updateWorkflowState();
            this.saveToStorage();
            
            console.log(`${fileType.toUpperCase()} file uploaded:`, file.name);
        },
        
        /**
         * Client-side file validation
         * @param {File} file - File to validate
         * @param {string} fileType - Expected file type
         * @returns {Object} Validation result
         */
        validateFile(file, fileType) {
            // File size validation (10MB limit)
            const maxSize = 10 * 1024 * 1024; // 10MB
            if (file.size > maxSize) {
                return {
                    valid: false,
                    message: 'File size exceeds 10MB limit'
                };
            }
            
            // File type validation
            if (fileType === 'sttm') {
                if (!file.type.includes('json') && !file.name.toLowerCase().endsWith('.json')) {
                    return {
                        valid: false,
                        message: 'STTM file must be a JSON file'
                    };
                }
            } else if (fileType === 'qtest') {
                const validTypes = ['xlsx', 'xls'];
                const isValidType = validTypes.some(type => 
                    file.type.includes(type) || file.name.toLowerCase().endsWith(`.${type}`)
                );
                if (!isValidType) {
                    return {
                        valid: false,
                        message: 'QTest file must be an Excel file (.xlsx or .xls)'
                    };
                }
            }
            
            return {
                valid: true,
                message: 'File format is valid'
            };
        },
        
        /**
         * Remove uploaded file
         * @param {string} fileType - 'sttm' or 'qtest'
         */
        removeFile(fileType) {
            this.files[fileType] = null;
            this.validationResults[fileType] = null;
            this.updateWorkflowState();
            this.saveToStorage();
            console.log(`${fileType.toUpperCase()} file removed`);
        },
        
        /**
         * Validate files through API
         * Calls the backend validation endpoints
         */
        async validateFiles() {
            if (!this.canValidateFiles()) {
                this.showError('Please upload both files before validation');
                return;
            }
            
            this.isLoading.validation = true;
            this.clearMessages();
            
            try {
                // Validate STTM file
                const sttmValidation = await this.validateSingleFile('sttm');
                
                // Validate QTest file
                const qtestValidation = await this.validateSingleFile('qtest');
                
                // Check if both validations passed
                if (sttmValidation.valid && qtestValidation.valid) {
                    this.workflow.filesValidated = true;
                    this.currentStep = 2;
                    this.showSuccess('✅ Both files validated successfully! Ready for analysis.');
                    this.saveToStorage();
                } else {
                    const errors = [];
                    if (!sttmValidation.valid) errors.push(`STTM: ${sttmValidation.message}`);
                    if (!qtestValidation.valid) errors.push(`QTest: ${qtestValidation.message}`);
                    this.showError(`Validation failed: ${errors.join(', ')}`);
                }
                
            } catch (error) {
                console.error('Validation error:', error);
                this.showError('Validation failed: ' + error.message);
            } finally {
                this.isLoading.validation = false;
            }
        },
        
        /**
         * Validate single file through API
         * @param {string} fileType - 'sttm' or 'qtest'
         * @returns {Promise<Object>} Validation result
         */
        async validateSingleFile(fileType) {
            const file = this.files[fileType];
            if (!file) {
                return { valid: false, message: 'File not found' };
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                // Use the new upload-validate endpoint
                const response = await fetch(`${this.apiBaseUrl}/api/upload-validate/${fileType}`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.detail || `${fileType.toUpperCase()} validation failed`);
                }
                
                // Store validation result
                this.validationResults[fileType] = {
                    valid: result.valid,
                    message: result.valid ? `${fileType.toUpperCase()} file is valid` : result.errors ? result.errors.join(', ') : 'Validation failed',
                    details: result
                };
                
                return { 
                    valid: result.valid, 
                    message: result.valid ? 'File is valid' : (result.errors ? result.errors.join(', ') : 'Validation failed')
                };
                
            } catch (error) {
                console.error(`${fileType} validation error:`, error);
                
                // Store error result
                this.validationResults[fileType] = {
                    valid: false,
                    message: error.message,
                    details: null
                };
                
                return { valid: false, message: error.message };
            }
        },
        
        /**
         * Update workflow state based on current conditions
         */
        updateWorkflowState() {
            // Update files uploaded state
            this.workflow.filesUploaded = !!(this.files.sttm && this.files.qtest);
            
            // Update current step
            if (this.workflow.filesUploaded && !this.workflow.filesValidated) {
                this.currentStep = 1;
            }
        },
        
        /**
         * Check if files can be validated
         * @returns {boolean} True if both files are uploaded
         */
        canValidateFiles() {
            return this.workflow.filesUploaded && !this.isLoading.validation;
        },
        
        /**
         * Format file size for display
         * @param {number} bytes - File size in bytes
         * @returns {string} Formatted file size
         */
        formatFileSize(bytes) {
            if (!bytes) return '';
            
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(1024));
            return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
        },
        
        /**
         * Calculate progress percentage
         * @returns {number} Progress percentage (0-100)
         */
        get progressPercentage() {
            return (this.currentStep / 4) * 100;
        },
        
        /**
         * Show error message
         * @param {string} message - Error message to display
         */
        showError(message) {
            this.errorMessage = message;
            this.successMessage = '';
            console.error('Error:', message);
            
            // Auto-clear error after 5 seconds
            setTimeout(() => {
                this.clearError();
            }, 5000);
        },
        
        /**
         * Show success message
         * @param {string} message - Success message to display
         */
        showSuccess(message) {
            this.successMessage = message;
            this.errorMessage = '';
            console.log('Success:', message);
            
            // Auto-clear success after 3 seconds
            setTimeout(() => {
                this.clearSuccess();
            }, 3000);
        },
        
        /**
         * Clear error message
         */
        clearError() {
            this.errorMessage = '';
        },
        
        /**
         * Clear success message
         */
        clearSuccess() {
            this.successMessage = '';
        },
        
        /**
         * Clear all messages
         */
        clearMessages() {
            this.errorMessage = '';
            this.successMessage = '';
        },
        
        /**
         * Save current state to session storage
         */
        saveToStorage() {
            const state = {
                workflow: this.workflow,
                currentStep: this.currentStep,
                validationResults: this.validationResults,
                // Note: Files are not saved to storage as they can't be serialized
                fileNames: {
                    sttm: this.files.sttm?.name || null,
                    qtest: this.files.qtest?.name || null
                }
            };
            
            try {
                sessionStorage.setItem('sttm_workflow_state', JSON.stringify(state));
                console.log('State saved to storage');
            } catch (error) {
                console.warn('Failed to save state to storage:', error);
            }
        },
        
        /**
         * Load state from session storage
         */
        loadFromStorage() {
            try {
                const savedState = sessionStorage.getItem('sttm_workflow_state');
                if (savedState) {
                    const state = JSON.parse(savedState);
                    this.workflow = { ...this.workflow, ...state.workflow };
                    this.currentStep = state.currentStep || 1;
                    this.validationResults = { ...this.validationResults, ...state.validationResults };
                    
                    console.log('State loaded from storage');
                }
            } catch (error) {
                console.warn('Failed to load state from storage:', error);
            }
        },
        
        /**
         * Analyze impact between STTM and QTest
         */
        async analyzeImpact() {
            if (!this.workflow.filesValidated || this.workflow.impactAnalyzed) {
                return;
            }
            
            this.isLoading.analysis = true;
            this.clearMessages();
            
            try {
                // Get the file names from validation results
                const sttmFile = this.validationResults.sttm?.details?.filename || this.files.sttm?.name;
                const qtestFile = this.validationResults.qtest?.details?.filename || this.files.qtest?.name;
                
                if (!sttmFile || !qtestFile) {
                    throw new Error('File names not found in validation results');
                }
                
                const response = await fetch(`${this.apiBaseUrl}/api/analyze-impact`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        sttm_file: sttmFile,
                        qtest_file: qtestFile
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Impact analysis failed');
                }
                
                const result = await response.json();
                this.analysisResult = result;
                
                // Update workflow state
                this.workflow.impactAnalyzed = true;
                this.currentStep = 3;
                
                // Show success message with summary - handle actual API response format
                let summaryText = '✅ Impact Analysis Complete!';
                if (result.summary && typeof result.summary === 'object') {
                    const summary = result.summary;
                    const totalChanges = summary.total_sttm_changes || 0;
                    const totalCases = summary.total_test_cases || 0;
                    const critical = summary.critical_impacts || 0;
                    const high = summary.high_impacts || 0;
                    
                    summaryText = `✅ Impact Analysis Complete! Found ${totalChanges} STTM changes affecting ${totalCases} test case(s). Critical: ${critical}, High: ${high}`;
                }
                this.showSuccess(summaryText);
                
                this.saveToStorage();
                
            } catch (error) {
                console.error('Analysis error:', error);
                this.showError('Analysis failed: ' + error.message);
            } finally {
                this.isLoading.analysis = false;
            }
        },
        
        /**
         * Generate test steps (delta or in-place)
         * @param {string} mode - 'delta' or 'in-place'
         */
        async generateTestSteps(mode) {
            if (!this.workflow.impactAnalyzed) {
                return;
            }
            
            // Check delta-first enforcement
            if (mode === 'in-place' && !this.workflow.deltaGenerated) {
                this.showError('Please generate Delta QTest first before In-Place generation');
                return;
            }
            
            this.isLoading.generation = true;
            this.generationType = mode;
            this.clearMessages();
            
            try {
                const sttmFile = this.validationResults.sttm?.details?.filename || this.files.sttm?.name;
                const qtestFile = this.validationResults.qtest?.details?.filename || this.files.qtest?.name;
                
                const response = await fetch(`${this.apiBaseUrl}/api/generate/test-steps`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        sttm_file: sttmFile,
                        qtest_file: qtestFile,
                        generation_mode: mode
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Test step generation failed');
                }
                
                const result = await response.json();
                console.log('Test step generation result:', result);
                
                // Extract filename from the API response structure
                let outputFile = result.saved_file_path;
                
                // If we have a full path, extract just the filename
                if (outputFile && outputFile.includes('/')) {
                    outputFile = outputFile.split('/').pop();
                } else if (outputFile && outputFile.includes('\\')) {
                    outputFile = outputFile.split('\\').pop();
                }
                
                // Store generated file info only if we have a filename
                if (outputFile) {
                    this.generatedFiles.push({
                        mode: mode,
                        file: outputFile,
                        timestamp: new Date().toISOString()
                    });
                }
                
                // Update workflow state
                if (mode === 'delta') {
                    this.workflow.deltaGenerated = true;
                } else {
                    this.workflow.inPlaceGenerated = true;
                }
                
                this.currentStep = 4;
                
                // Show success message with summary details
                const modeText = mode === 'delta' ? 'Delta' : 'In-Place';
                const fileText = outputFile ? `File: ${outputFile}` : 'Generation complete';
                
                let summaryText = '';
                if (result.summary && result.summary.total_steps_generated !== undefined) {
                    const totalSteps = result.summary.total_steps_generated || 0;
                    summaryText = ` (${totalSteps} steps generated)`;
                }
                
                this.showSuccess(`✅ ${modeText} QTest generated successfully! ${fileText}${summaryText}`);
                
                this.saveToStorage();
                
            } catch (error) {
                console.error('Generation error:', error);
                this.showError('Generation failed: ' + error.message);
            } finally {
                this.isLoading.generation = false;
                this.generationType = null;
            }
        },
        
        /**
         * Download JSON report
         */
        async downloadJSON() {
            if (!this.analysisResult || !this.analysisResult.report_links?.json_url) {
                this.showError('No JSON report available');
                return;
            }
            
            try {
                // Use the JSON report URL directly
                const jsonUrl = this.analysisResult.report_links.json_url;
                
                // Create download link
                const link = document.createElement('a');
                link.href = jsonUrl;
                link.download = jsonUrl.split('/').pop();
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                this.showSuccess('JSON report download started');
            } catch (error) {
                console.error('Download error:', error);
                this.showError('Failed to download JSON report');
            }
        },
        
        /**
         * Get formatted analysis summary for display
         * @returns {string} Formatted summary text
         */
        getAnalysisSummary() {
            if (!this.analysisResult) return '';
            
            // Handle the actual API response structure
            if (this.analysisResult.summary) {
                const summary = this.analysisResult.summary;
                if (summary.total_test_cases !== undefined && summary.total_sttm_changes !== undefined) {
                    const totalChanges = summary.total_sttm_changes || 0;
                    const totalCases = summary.total_test_cases || 0;
                    const critical = summary.critical_impacts || 0;
                    const high = summary.high_impacts || 0;
                    
                    return `Found ${totalChanges} STTM changes affecting ${totalCases} test case(s). Critical: ${critical}, High: ${high}`;
                }
            }
            
            return 'Analysis Complete';
        },

        /**
         * Reset workflow to initial state
         */
        resetWorkflow() {
            this.files = { sttm: null, qtest: null };
            this.validationResults = { sttm: null, qtest: null };
            this.workflow = {
                filesUploaded: false,
                filesValidated: false,
                impactAnalyzed: false,
                deltaGenerated: false,
                inPlaceGenerated: false
            };
            this.currentStep = 1;
            this.analysisResult = null;
            this.generatedFiles = [];
            this.clearMessages();
            
            // Clear storage
            sessionStorage.removeItem('sttm_workflow_state');
            
            console.log('Workflow reset');
        }
    }
}
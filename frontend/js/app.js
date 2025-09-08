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
            sttm: null,  // Keep for backward compatibility
            qtest: null
        },
        
        // Uploaded file info (for Chrome fix)
        uploadedQTestFile: null, // Will store {filename, file_size} after upload
        
        // NEW: QTest Azure blob info for selected comparison
        qtestBlobInfo: null, // Will store {blob_url, validation_details} after successful upload
        
        // Version Tracking State
        trackedFiles: [],
        selectedFile: null,
        comparisons: [],
        selectedComparison: null,
        
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
            generation: false,
            trackedFiles: false,
            comparisons: false
        },
        
        // Current generation type
        generationType: null,
        
        // Version information
        versionInfo: null,
        
        // Analysis results
        analysisResult: null,
        
        // Generated files
        generatedFiles: [],
        
        // Test step generation results with blob URLs
        testStepResults: {},
        
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
        apiBaseUrl: typeof CONFIG !== 'undefined' ? CONFIG.API_BASE_URL : `${window.location.protocol}//${window.location.host}`,
        
        /**
         * Initialize the application
         * Called when Alpine.js component is mounted
         */
        init() {
            console.log('STTM App initialized - Stage 2');
            console.log('Alpine.js is working! Click handlers should work now.');
            this.loadFromStorage();
            this.updateWorkflowState();
            this.loadTrackedFiles(); // Load tracked files on init
            this.loadVersionInfo(); // Load version information
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
        async processFile(file, fileType) {
            // Client-side validation
            const validation = this.validateFile(file, fileType);
            
            if (!validation.valid) {
                this.showError(validation.message);
                return;
            }
            
            // For QTest files, upload immediately to avoid Chrome ERR_UPLOAD_FILE_CHANGED
            if (fileType === 'qtest') {
                try {
                    this.isLoading.upload = true;
                    console.log('Uploading QTest file immediately to prevent Chrome issue...');
                    
                    const uploadFormData = new FormData();
                    uploadFormData.append('file', file);
                    
                    const uploadResponse = await fetch(`${this.apiBaseUrl}/api/upload/qtest`, {
                        method: 'POST',
                        body: uploadFormData
                    });
                    
                    if (!uploadResponse.ok) {
                        const error = await uploadResponse.json();
                        throw new Error(error.detail || 'QTest file upload failed');
                    }
                    
                    const uploadResult = await uploadResponse.json();
                    console.log('QTest upload successful:', uploadResult);
                    
                    // Store upload info instead of file object
                    this.uploadedQTestFile = {
                        filename: uploadResult.filename,
                        file_size: uploadResult.file_size,
                        original_name: file.name
                    };
                    
                    // Still store file reference for display purposes only
                    this.files[fileType] = file;
                    this.validationResults[fileType] = null;
                    
                    this.showSuccess(`QTest file "${file.name}" uploaded successfully`);
                    
                } catch (error) {
                    console.error('QTest upload error:', error);
                    this.showError(`Failed to upload QTest file: ${error.message}`);
                    return;
                } finally {
                    this.isLoading.upload = false;
                }
            } else {
                // For non-QTest files, store normally
                this.files[fileType] = file;
                this.validationResults[fileType] = null; // Clear previous validation
            }
            
            // Update workflow state
            this.updateWorkflowState();
            this.saveToStorage();
            
            console.log(`${fileType.toUpperCase()} file processed:`, file.name);
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
                this.showError('Please select a comparison and upload QTest file before validation');
                return;
            }
            
            this.isLoading.validation = true;
            this.clearMessages();
            
            try {
                // Validate comparison selection
                if (!this.selectedComparison) {
                    throw new Error('No comparison selected');
                }
                
                // Validate that comparison has JSON data available
                if (!this.selectedComparison.json_report_url) {
                    throw new Error('Selected comparison does not have JSON data available');
                }
                
                // Validate QTest file
                const qtestValidation = await this.validateSingleFile('qtest');
                
                // Check validation results
                if (qtestValidation.valid) {
                    this.workflow.filesValidated = true;
                    this.currentStep = 2;
                    this.showSuccess(`✅ Ready for analysis! Selected comparison: ${this.selectedComparison.comparison_title} with ${this.selectedComparison.total_changes} changes.`);
                    this.saveToStorage();
                } else {
                    this.showError(`Validation failed - QTest: ${qtestValidation.message}`);
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
         * Analyze impact between STTM and QTest - Two-step process
         */
        async analyzeImpact() {
            if (!this.workflow.filesValidated || this.workflow.impactAnalyzed) {
                return;
            }
            
            this.isLoading.analysis = true;
            this.clearMessages();
            
            try {
                // Validate required data
                if (!this.selectedComparison) {
                    throw new Error('No comparison selected');
                }
                
                if (!this.qtestBlobInfo) {
                    throw new Error('No QTest file uploaded to Azure');
                }
                
                // Using QTest file from Azure blob storage
                console.log('Using QTest file from Azure blob storage');
                
                // Run analysis with comparison_id (QTest will be fetched from Azure)
                console.log('Running impact analysis...');
                const analysisUrl = new URL(`${this.apiBaseUrl}/api/analyze-impact-from-comparison`);
                analysisUrl.searchParams.append('comparison_id', this.selectedComparison.comparison_id);
                
                const response = await fetch(analysisUrl, {
                    method: 'POST'
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
                // Validate required data for comparison-based generation
                if (!this.selectedComparison) {
                    throw new Error('No comparison selected');
                }
                
                if (!this.qtestBlobInfo) {
                    throw new Error('No QTest file uploaded to Azure');
                }
                
                // Using QTest file from Azure blob storage
                console.log('Using QTest file from Azure blob storage');
                
                // Generate test steps with comparison_id (QTest will be fetched from Azure)
                console.log('Generating test steps...');
                const generationUrl = new URL(`${this.apiBaseUrl}/api/generate/test-steps-from-comparison`);
                generationUrl.searchParams.append('comparison_id', this.selectedComparison.comparison_id);
                generationUrl.searchParams.append('generation_mode', mode);
                
                const response = await fetch(generationUrl, {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Test step generation failed');
                }
                
                const result = await response.json();
                console.log('Test step generation result:', result);
                
                // Store test step generation results with blob URLs
                let outputFile = null;
                
                if (result.blob_urls) {
                    // Store the blob URLs for this generation mode
                    if (!this.testStepResults) {
                        this.testStepResults = {};
                    }
                    
                    this.testStepResults[mode] = {
                        json_url: result.blob_urls.json_url,
                        excel_url: result.blob_urls.excel_url,
                        report_id: result.report_id,
                        timestamp: new Date().toISOString(),
                        summary: result.summary
                    };
                    
                    // Extract filename for display
                    if (result.blob_urls.excel_url) {
                        outputFile = result.blob_urls.excel_url.split('/').pop();
                    } else if (result.report_id) {
                        outputFile = `${result.report_id}.xlsx`;
                    }
                    
                    // Store generated file info for the files list
                    if (outputFile) {
                        this.generatedFiles.push({
                            mode: mode,
                            file: outputFile,
                            timestamp: new Date().toISOString(),
                            blob_urls: result.blob_urls
                        });
                    }
                } else {
                    // Fallback for cases without blob URLs
                    if (result.report_id) {
                        outputFile = `${result.report_id}.xlsx`;
                    }
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
         * Get API URL for test step Excel file
         */
        getTestStepExcelUrl(mode) {
            if (!this.selectedComparison) return '#';
            return `${this.apiBaseUrl}/api/test-steps/${this.selectedComparison.comparison_id}/${mode}/excel`;
        },
        
        /**
         * Get API URL for test step JSON file
         */
        getTestStepJsonUrl(mode) {
            if (!this.selectedComparison) return '#';
            return `${this.apiBaseUrl}/api/test-steps/${this.selectedComparison.comparison_id}/${mode}/json`;
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
         * Load tracked files from API
         */
        async loadTrackedFiles() {
            try {
                this.isLoading.trackedFiles = true;
                console.log('Loading tracked files...');
                
                const response = await fetch(`${this.apiBaseUrl}/api/tracked-files`);
                const data = await response.json();
                
                if (data.success && data.files) {
                    this.trackedFiles = data.files;
                    console.log(`Loaded ${data.files.length} tracked files`);
                } else {
                    throw new Error('Failed to load tracked files');
                }
                
            } catch (error) {
                console.error('Error loading tracked files:', error);
                this.showError('Failed to load tracked files: ' + error.message);
            } finally {
                this.isLoading.trackedFiles = false;
            }
        },
        
        /**
         * Load application version information
         */
        async loadVersionInfo() {
            try {
                console.log('Loading version information...');
                
                const response = await fetch(`${this.apiBaseUrl}/api/version`);
                const data = await response.json();
                
                if (data.success && data.version_info) {
                    const version = data.version_info;
                    this.versionInfo = `v${version.version} (${version.build_date}) [${version.build_hash}]`;
                    console.log('Version loaded:', this.versionInfo);
                } else {
                    console.warn('Failed to load version info');
                    this.versionInfo = 'v1.0.1 (unknown)';
                }
                
            } catch (error) {
                console.error('Error loading version info:', error);
                this.versionInfo = 'v1.0.1 (error)';
            }
        },
        
        /**
         * Handle tracked file selection
         * @param {number} fileId - Selected file ID
         */
        async selectTrackedFile(fileId) {
            try {
                // Find the selected file
                const file = this.trackedFiles.find(f => f.id === fileId);
                if (!file) {
                    this.showError('Selected file not found');
                    return;
                }
                
                this.selectedFile = file;
                this.selectedComparison = null; // Reset comparison selection
                this.comparisons = []; // Clear previous comparisons
                
                console.log(`Selected tracked file: ${file.friendly_name}`);
                
                // Load comparisons for this file
                await this.loadFileComparisons(fileId);
                
            } catch (error) {
                console.error('Error selecting tracked file:', error);
                this.showError('Failed to select tracked file: ' + error.message);
            }
        },
        
        /**
         * Load comparisons for a specific file
         * @param {number} fileId - File ID to load comparisons for
         */
        async loadFileComparisons(fileId) {
            try {
                this.isLoading.comparisons = true;
                console.log(`Loading comparisons for file ${fileId}...`);
                
                const response = await fetch(`${this.apiBaseUrl}/api/tracked-files/${fileId}/comparisons`);
                const data = await response.json();
                
                if (data.success && data.comparisons) {
                    this.comparisons = data.comparisons;
                    console.log(`Loaded ${data.comparisons.length} comparisons`);
                } else {
                    throw new Error('Failed to load comparisons');
                }
                
            } catch (error) {
                console.error('Error loading comparisons:', error);
                this.showError('Failed to load comparisons: ' + error.message);
            } finally {
                this.isLoading.comparisons = false;
            }
        },
        
        /**
         * Select a comparison
         * @param {number} comparisonId - Selected comparison ID
         */
        selectComparison(comparisonId) {
            const comparison = this.comparisons.find(c => c.comparison_id === comparisonId);
            if (!comparison) {
                this.showError('Selected comparison not found');
                return;
            }
            
            this.selectedComparison = comparison;
            console.log(`Selected comparison: ${comparison.comparison_title}`);
            
            // Update workflow state
            this.updateWorkflowState();
        },
        
        /**
         * Check if files are ready for validation (new logic)
         */
        canValidateFiles() {
            // New logic: need selected comparison + QTest file uploaded to Azure
            return this.selectedComparison && this.qtestBlobInfo;
        },
        
        /**
         * Format version display text
         * @param {Object} comparison - Comparison object
         * @returns {string} Formatted version text
         */
        formatVersionDisplay(comparison) {
            if (!comparison) return '';
            return `v${comparison.from_sharepoint_version} (${comparison.from_sequence}) → v${comparison.to_sharepoint_version} (${comparison.to_sequence})`;
        },
        
        /**
         * Format date for display
         * @param {string} dateString - ISO date string
         * @returns {string} Formatted date
         */
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        },

        /**
         * Reset workflow to initial state
         */
        /**
         * NEW: Upload QTest file with validation and Azure Blob storage
         * Completely new implementation - no reuse of existing code
         */
        async uploadQTestToAzure(event) {
            // Get the file from the input event
            const file = event.target.files ? event.target.files[0] : null;
            
            if (!file) {
                this.showError('No file selected');
                return;
            }
            
            // Check if comparison is selected
            if (!this.selectedComparison) {
                this.showError('Please select a comparison first');
                event.target.value = ''; // Reset file input
                return;
            }
            
            // Validate file type client-side
            if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
                this.showError('Please select an Excel file (.xlsx or .xls)');
                event.target.value = ''; // Reset file input
                return;
            }
            
            // Check file size (10MB limit)
            if (file.size > 10 * 1024 * 1024) {
                this.showError('File size exceeds 10MB limit');
                event.target.value = ''; // Reset file input
                return;
            }
            
            this.isLoading.upload = true;
            this.clearMessages();
            
            try {
                console.log(`NEW: Uploading QTest to Azure for comparison ${this.selectedComparison.comparison_id}`);
                
                // Create form data
                const formData = new FormData();
                formData.append('file', file);
                
                // Call the new API endpoint
                const response = await fetch(
                    `${this.apiBaseUrl}/api/qtest/upload-validate/${this.selectedComparison.comparison_id}`,
                    {
                        method: 'POST',
                        body: formData
                    }
                );
                
                const result = await response.json();
                
                // Debug: Log the full response
                console.log('NEW: Full API response:', result);
                
                if (!response.ok) {
                    console.error('NEW: HTTP error response:', result);
                    throw new Error(result.detail || result.error || 'Upload failed');
                }
                
                if (result.success) {
                    // Store the blob info
                    this.qtestBlobInfo = {
                        blob_url: result.blob_url,
                        validation: result.validation,
                        comparison_id: result.comparison_id,
                        upload_time: new Date().toISOString()
                    };
                    
                    // Show validation details
                    const validation = result.validation;
                    let message = `QTest uploaded successfully! `;
                    message += `${validation.worksheets} worksheets, ${validation.test_cases} test cases found.`;
                    
                    if (validation.warnings && validation.warnings.length > 0) {
                        message += ` Warnings: ${validation.warnings.join(', ')}`;
                    }
                    
                    this.showSuccess(message);
                    
                    // Mark workflow as ready for analysis
                    this.workflow.filesValidated = true;
                    this.currentStep = 2;
                    
                    console.log('NEW: QTest uploaded to Azure:', result.blob_url);
                } else {
                    // Show validation errors with detailed logging
                    console.error('NEW: Upload failed, result:', result);
                    console.error('NEW: Validation details:', result.validation);
                    
                    const errors = result.validation?.errors || [];
                    const errorMsg = result.error || 'Unknown upload error';
                    
                    if (errors.length > 0) {
                        throw new Error(`Validation failed: ${errors.join(', ')}`);
                    } else {
                        throw new Error(`Upload failed: ${errorMsg}`);
                    }
                }
                
            } catch (error) {
                console.error('NEW: QTest Azure upload error:', error);
                this.showError(`Failed to upload QTest: ${error.message}`);
            } finally {
                this.isLoading.upload = false;
                // Reset file input
                event.target.value = '';
            }
        },
        
        /**
         * NEW: Check if QTest is uploaded to Azure for current comparison
         */
        hasQTestInAzure() {
            return this.qtestBlobInfo && 
                   this.qtestBlobInfo.comparison_id === this.selectedComparison?.comparison_id;
        },
        
        resetWorkflow() {
            this.files = { sttm: null, qtest: null };
            this.validationResults = { sttm: null, qtest: null };
            this.selectedFile = null;
            this.selectedComparison = null;
            this.comparisons = [];
            this.qtestBlobInfo = null; // Clear Azure blob info
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
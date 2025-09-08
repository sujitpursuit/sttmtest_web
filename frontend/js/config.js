/**
 * Frontend Configuration
 * 
 * This file contains configuration settings for the frontend application.
 * Update API_BASE_URL to match your backend API server location.
 */

// API Configuration
const CONFIG = {
    // API Base URL - Update this to match your .env configuration
    // Default: Use the same host as the frontend is served from
    API_BASE_URL: window.location.origin,
    
    // Alternative configurations (uncomment and modify as needed):
    // API_BASE_URL: 'http://127.0.0.1:8004',  // Local development
    // API_BASE_URL: 'http://localhost:8004',   // Alternative local
    // API_BASE_URL: 'https://api.yourdomain.com',  // Production
    
    // File upload limits (in MB)
    MAX_FILE_SIZE: 50,
    
    // Timeouts (in milliseconds)
    UPLOAD_TIMEOUT: 60000,
    ANALYSIS_TIMEOUT: 300000,
    
    // UI Settings
    SHOW_DEBUG_INFO: false,
    AUTO_VALIDATE_ON_UPLOAD: true
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
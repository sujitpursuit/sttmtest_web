# STTM Frontend Development Plan - 4 Phases

## 📋 Project Overview
Build a lightweight Alpine.js frontend for the STTM Impact Analysis Tool with enforced sequential workflow: File Upload → Validation → Impact Analysis → Test Step Generation (Delta first, then In-Place).

**Base URL:** http://localhost:8004  
**Framework:** Alpine.js + Vanilla CSS  
**Enforcement:** Frontend-first with backend validation  

---

## 🎯 Development Phases

### **Phase 1: Basic File Upload & Validation (Foundation)** ✅ *COMPLETED*
**Duration:** 1-2 hours  
**Goal:** Core file upload functionality with validation

#### **Phase 1 Tasks:**
- [x] **F1.1** Create frontend directory structure (`frontend/`, `css/`, `js/`, `assets/`)
- [x] **F1.2** Set up `index.html` with Alpine.js CDN and base layout
- [x] **F1.3** Implement drag & drop file upload interface for STTM JSON and QTest Excel
- [x] **F1.4** Add client-side file validation (type, size checks)
- [x] **F1.5** Create visual feedback for upload status (progress, success, error states)
- [x] **F1.6** Integrate with existing validation APIs (`/api/validate/sttm`, `/api/validate/qtest`)
- [x] **F1.7** Implement basic workflow state management
- [x] **F1.8** Style upload interface with professional CSS
- [x] **F1.9** Test all Phase 1 functionality manually

#### **Phase 1 Deliverables:**
```
frontend/
├── index.html           # Main page with Alpine.js setup
├── css/
│   └── styles.css       # Clean, professional styling
├── js/
│   └── app.js          # Alpine.js application logic
└── assets/
    └── icons/          # Upload/status icons
```

#### **Phase 1 Testing Scenarios:**
- [ ] Upload valid STTM JSON file → Success indicator
- [ ] Upload valid QTest Excel file → Success indicator  
- [ ] Upload invalid file types → Error messages
- [ ] Upload both files → "Validate Files" button enables
- [ ] Click "Validate Files" → API calls succeed, validation results display

#### **Phase 1 Success Criteria:**
- ✅ File upload interface working with drag & drop
- ✅ Client-side validation prevents invalid uploads
- ✅ API integration with validation endpoints successful
- ✅ Visual feedback clear and professional
- ✅ "Validate Files" button properly enabled/disabled

---

### **Phase 2: Impact Analysis & Report Display** ⚫ *PENDING*
**Duration:** 2-3 hours  
**Goal:** Impact analysis execution with HTML/JSON report access

#### **Phase 2 Tasks:**
- [ ] **F2.1** Add "Analyze Impact" button (enabled after validation)
- [ ] **F2.2** Implement loading states and progress indicators during analysis
- [ ] **F2.3** Create results display section with analysis summary cards
- [ ] **F2.4** Add "View HTML Report" link functionality (opens in new tab)
- [ ] **F2.5** Implement "Download JSON" button with proper file download
- [ ] **F2.6** Add comprehensive error handling for analysis failures
- [ ] **F2.7** Style results section with stats cards and report actions
- [ ] **F2.8** Test analysis workflow with real data

#### **Phase 2 Features:**
- **Analysis Trigger**: "Analyze Impact" button (enabled after validation)
- **Loading States**: Progress indicators during analysis
- **Results Display**: Summary cards showing impact analysis results
- **Report Access**: "View HTML Report" link + "Download JSON" button
- **Error Handling**: Analysis failure scenarios

#### **Phase 2 Testing Scenarios:**
- [ ] Valid files → Validate → "Analyze Impact" button enables
- [ ] Click "Analyze Impact" → Loading state → Results display
- [ ] Click "View HTML Report" → Opens in new tab
- [ ] Click "Download JSON" → File downloads
- [ ] Analysis with errors → Error message display

#### **Phase 2 Success Criteria:**
- ✅ Impact analysis triggers correctly after validation
- ✅ Loading states provide clear user feedback
- ✅ Analysis results display in organized, readable format
- ✅ HTML report viewing works in new tab
- ✅ JSON download functionality working

---

### **Phase 3: Test Step Generation (Delta First)** ⚫ *PENDING*
**Duration:** 2-3 hours  
**Goal:** Delta test step generation with enforcement logic

#### **Phase 3 Tasks:**
- [ ] **F3.1** Add "Generate Delta Steps" button (enabled after analysis)
- [ ] **F3.2** Implement enforcement logic: "Generate In-Place Steps" disabled until delta completes
- [ ] **F3.3** Create delta step generation workflow with API integration
- [ ] **F3.4** Add delta results display with step summary and download option
- [ ] **F3.5** Implement collapsible step preview section
- [ ] **F3.6** Add "Generate In-Place Steps" functionality (unlocked after delta)
- [ ] **F3.7** Create download management for both delta and in-place results
- [ ] **F3.8** Add tooltips and help text for workflow enforcement
- [ ] **F3.9** Test complete test step generation workflow

#### **Phase 3 Features:**
- **Delta Generation**: "Generate Delta Steps" button (enabled after analysis)
- **Enforcement Logic**: "Generate In-Place Steps" remains disabled until delta completes
- **Results Display**: Delta step summary with download option
- **Step Preview**: Collapsible section showing generated steps
- **Download Management**: Save delta results to enable in-place generation

#### **Phase 3 Workflow Logic:**
```javascript
workflow: {
    filesUploaded: false,
    filesValidated: false,
    impactAnalyzed: false,
    deltaGenerated: false,      // NEW
    inPlaceGenerated: false     // NEW
}
```

#### **Phase 3 Testing Scenarios:**
- [ ] After analysis → "Generate Delta" enabled, "Generate In-Place" disabled
- [ ] Click "Generate Delta" → Loading → Results → Download available
- [ ] After delta success → "Generate In-Place" becomes enabled
- [ ] Try direct in-place call → Should fail (backend validation)
- [ ] Complete workflow → Both options available

#### **Phase 3 Success Criteria:**
- ✅ Delta generation works correctly after impact analysis
- ✅ In-place generation properly locked until delta completion
- ✅ Enforcement logic prevents workflow violations
- ✅ Step results display clearly with download options
- ✅ Backend validation catches direct API calls

---

### **Phase 4: Complete Workflow & Polish** ⚫ *PENDING*
**Duration:** 1-2 hours  
**Goal:** Full workflow integration with UX enhancements

#### **Phase 4 Tasks:**
- [ ] **F4.1** Add visual progress bar showing current workflow step
- [ ] **F4.2** Implement state persistence using SessionStorage
- [ ] **F4.3** Add "Start Over" reset functionality
- [ ] **F4.4** Optimize for responsive design (mobile/tablet)
- [ ] **F4.5** Add smooth loading animations and transitions
- [ ] **F4.6** Implement comprehensive error recovery with retry options
- [ ] **F4.7** Add keyboard navigation support
- [ ] **F4.8** Final testing across all browsers and devices
- [ ] **F4.9** Code cleanup and documentation

#### **Phase 4 Features:**
- **Progress Tracking**: Visual progress bar showing current step
- **State Persistence**: SessionStorage for page refresh handling
- **Reset Functionality**: "Start Over" button to clear all state
- **Responsive Design**: Mobile/tablet optimization
- **Loading Animations**: Smooth transitions and feedback
- **Error Recovery**: Graceful error handling with retry options

#### **Phase 4 Testing Scenarios:**
- [ ] Complete full workflow → All steps work sequentially
- [ ] Refresh page mid-workflow → State persists correctly
- [ ] Try to skip steps → Proper enforcement/error messages
- [ ] Mobile device testing → Responsive design works
- [ ] Error scenarios → Recovery options available
- [ ] Reset functionality → Clean state restoration

#### **Phase 4 Success Criteria:**
- ✅ Full workflow completion from start to finish
- ✅ State persistence across page refreshes
- ✅ Responsive design works on all device sizes
- ✅ Error handling provides clear recovery paths
- ✅ Professional, polished user experience

---

## 🔧 Technical Architecture

### **Frontend Structure:**
```
frontend/
├── index.html          # Single-page application
├── css/
│   ├── base.css       # Reset, variables, typography
│   ├── components.css # Buttons, cards, forms
│   └── layout.css     # Grid, responsive utilities
├── js/
│   ├── app.js         # Main Alpine.js application
│   ├── api.js         # API integration helpers
│   └── utils.js       # Utility functions
└── README.md          # Phase-by-phase setup instructions
```

### **API Endpoints Used:**
```
POST /api/validate/sttm         # STTM file validation
POST /api/validate/qtest        # QTest file validation  
POST /api/validate/both         # Combined validation
POST /api/analyze-impact        # Main impact analysis
POST /api/generate/test-steps   # Test step generation (delta/in-place)
GET  /api/reports/{report_id}   # Report file retrieval
```

### **State Management:**
- **Primary**: Alpine.js reactive data
- **Persistence**: SessionStorage for page refreshes
- **Validation**: Backend API checks for security

---

## 📊 Progress Tracking

### **Current Status:** 
- **Phase:** Phase 1 Complete - Ready for Phase 2
- **Progress:** 25% (Phase 1 Foundation Complete)

### **Milestones:**
- [x] **M1:** Phase 1 Complete - Basic file upload and validation
- [ ] **M2:** Phase 2 Complete - Impact analysis with report access
- [ ] **M3:** Phase 3 Complete - Test step generation with enforcement
- [ ] **M4:** Phase 4 Complete - Production-ready frontend

### **Testing Strategy:**
- **Manual Testing**: Browser-based testing after each phase
- **API Integration**: Test with existing FastAPI endpoints (port 8004)
- **Error Scenarios**: Test network failures, invalid responses
- **Cross-browser**: Chrome, Firefox, Edge compatibility
- **Responsive**: Mobile, tablet, desktop testing

---

## 📝 Development Guidelines

### **Code Standards:**
- **Comments**: Every function documented with purpose and parameters
- **Error Handling**: Try-catch blocks with user-friendly error messages
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support
- **Performance**: Minimal dependencies, optimized CSS/JS
- **Maintainability**: Clear naming conventions, modular structure

### **Documentation Requirements:**
```javascript
/**
 * Uploads and validates a file through the API
 * @param {string} fileType - 'sttm' or 'qtest'
 * @param {File} file - The file object to upload
 * @returns {Promise<Object>} Validation result from API
 * @throws {Error} Upload or validation failure
 */
async uploadFile(fileType, file) {
    // Clear implementation with error handling
}
```

### **Browser Support:**
- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

---

---

## 🗄️ Blob Storage Integration (Stage 2 Implementation)

### **Overview**
Implemented blob-first architecture for test step generation outputs. Files are stored in Azure Blob Storage and served through authenticated API endpoints.

### **Frontend Changes**

#### **Report Display Architecture**
- **Impact Analysis Reports**: Local files served via `/reports/` (HTML/JSON)
- **Test Step Generation Reports**: Blob storage served via API endpoints

#### **New JavaScript Functions**
```javascript
/**
 * Get API URL for test step Excel file
 * @param {string} mode - 'delta' or 'in-place'
 * @returns {string} API endpoint URL
 */
getTestStepExcelUrl(mode) {
    if (!this.selectedComparison) return '#';
    return `${this.apiBaseUrl}/api/test-steps/${this.selectedComparison.comparison_id}/${mode}/excel`;
}

/**
 * Get API URL for test step JSON file  
 * @param {string} mode - 'delta' or 'in-place'
 * @returns {string} API endpoint URL
 */
getTestStepJsonUrl(mode) {
    if (!this.selectedComparison) return '#';
    return `${this.apiBaseUrl}/api/test-steps/${this.selectedComparison.comparison_id}/${mode}/json`;
}
```

#### **Updated Data Structure**
```javascript
// Test step generation results with blob URLs
testStepResults: {
    'delta': {
        json_url: 'https://stexceldifffiles.blob.core.windows.net/output-files/comparison_10/delta/test_steps_delta_20250908_141014.json',
        excel_url: 'https://stexceldifffiles.blob.core.windows.net/output-files/comparison_10/delta/test_steps_delta_20250908_141014.xlsx',
        report_id: 'comparison_10_delta',
        timestamp: '2025-09-08T14:10:14.767Z',
        summary: {
            total_steps_generated: 1,
            action_breakdown: { ADD: 1, MODIFY: 0, DELETE: 0 }
        }
    },
    'in-place': {
        // Similar structure for in-place mode
    }
}
```

#### **HTML Template Updates**
```html
<!-- Test Step Generation Reports Section -->
<div class="result-card" x-show="testStepResults && Object.keys(testStepResults).length > 0">
    <div class="card-icon">📝</div>
    <div class="card-content">
        <h3>Test Step Generation Reports</h3>
        
        <!-- Delta Reports -->
        <div class="test-step-reports" x-show="testStepResults.delta">
            <h4 class="generation-mode">🔄 Delta Mode:</h4>
            <div class="report-links">
                <a :href="getTestStepExcelUrl('delta')" 
                   target="_blank" 
                   class="report-link"
                   x-show="testStepResults.delta && testStepResults.delta.excel_url">
                    📊 View Delta Excel Report
                </a>
                <a :href="getTestStepJsonUrl('delta')" 
                   target="_blank" 
                   class="report-link"
                   x-show="testStepResults.delta && testStepResults.delta.json_url">
                    📥 Download Delta JSON Report
                </a>
            </div>
            <div class="generation-summary" x-show="testStepResults.delta.summary">
                <small x-text="`Generated ${testStepResults.delta.summary?.total_steps_generated || 0} steps`"></small>
            </div>
        </div>
        
        <!-- In-Place Reports -->
        <div class="test-step-reports" x-show="testStepResults['in-place']">
            <h4 class="generation-mode">📝 In-Place Mode:</h4>
            <div class="report-links">
                <a :href="getTestStepExcelUrl('in-place')" 
                   target="_blank" 
                   class="report-link"
                   x-show="testStepResults['in-place'] && testStepResults['in-place'].excel_url">
                    📊 View In-Place Excel Report
                </a>
                <a :href="getTestStepJsonUrl('in-place')" 
                   target="_blank" 
                   class="report-link"
                   x-show="testStepResults['in-place'] && testStepResults['in-place'].json_url">
                    📥 Download In-Place JSON Report
                </a>
            </div>
            <div class="generation-summary" x-show="testStepResults['in-place'].summary">
                <small x-text="`Generated ${testStepResults['in-place'].summary?.total_steps_generated || 0} steps`"></small>
            </div>
        </div>
    </div>
</div>
```

#### **Removed Redundant Elements**
- ❌ **Generated Files List**: Removed duplicate download buttons section
- ✅ **Cleaner UI**: All downloads now organized by generation mode in dedicated reports section

### **User Experience Improvements**
1. **Clear Separation**: Impact Analysis vs Test Step Generation reports
2. **Organized by Mode**: Delta and In-Place sections with separate buttons
3. **Proper Authentication**: Files served through API with Azure credentials
4. **No Access Errors**: Eliminated "PublicAccessNotPermitted" blob errors
5. **Generation Summaries**: Shows step counts for each mode

### **CSS Additions**
```css
/* Test Step Generation Reports Styles */
.test-step-reports {
    margin-bottom: var(--spacing-4);
}

.test-step-reports:last-child {
    margin-bottom: 0;
}

.generation-mode {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: var(--spacing-2);
    color: var(--primary-color);
}

.generation-summary {
    margin-top: var(--spacing-2);
    color: var(--text-muted);
    font-style: italic;
}

.generation-summary small {
    font-size: 0.875rem;
}
```

---

**Last Updated:** September 8, 2025  
**Current Phase:** All Phases Complete + Blob Storage Integration ✅  
**API Base URL:** http://localhost:8000  
**Status:** Production Ready with Azure Blob Storage 🚀
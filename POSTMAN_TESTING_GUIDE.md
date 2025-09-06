# 🧪 Postman Testing Guide - STTM Impact Analysis API Stage 2

## 📋 **Quick Setup**

### **1. Import Collection**
1. Open Postman
2. Click **Import** button
3. Select `STTM_Impact_Analysis_API.postman_collection.json`
4. Collection will appear as "STTM Impact Analysis API - Stage 2"

### **2. Verify Server is Running**
- Ensure API server is running: `http://127.0.0.1:8004`
- If not running, start with: `python -m uvicorn api.main:app --host 127.0.0.1 --port 8004 --reload`

### **3. Check Variables**
The collection includes these variables (should auto-populate):
- `base_url`: http://127.0.0.1:8004
- `sttm_file`: STTM_DIFF.json  
- `qtest_file`: QTEST_STTM.xlsx

---

## 🎯 **Recommended Testing Order**

### **Phase 1: Basic Functionality** ⭐ *START HERE*

1. **🏥 Health Check**
   - Run: "API Health Check"
   - ✅ Expected: Status 200, API version info
   - 📊 Response time: < 100ms

2. **📁 File Discovery**
   - Run: "List STTM Files"
   - ✅ Expected: Shows STTM_DIFF.json in list
   - Run: "List QTEST Files"  
   - ✅ Expected: Shows QTEST_STTM.xlsx in list

3. **✅ File Validation**
   - Run: "Validate STTM File"
   - ✅ Expected: `"valid": true`, shows file structure
   - Run: "Validate QTEST File"
   - ✅ Expected: `"valid": true`, shows test case count
   - Run: "Validate Both Files"
   - ✅ Expected: `"both_valid": true`, compatibility confirmed

### **Phase 2: Core Analysis** ⭐ *MAIN FEATURE*

4. **🎯 Basic Impact Analysis**
   - Run: "Basic Impact Analysis (Default Config)"
   - ✅ Expected: `"success": true`
   - ✅ Expected: HTML report in response
   - ✅ Expected: JSON report with detailed analysis
   - ✅ Expected: Report files saved to reports/ directory
   - 📊 Processing time: ~0.2 seconds

5. **⚙️ Configuration Management**  
   - Run: "Get Configuration Presets"
   - ✅ Expected: 4 presets (balanced, conservative, aggressive, strict)
   - ✅ Expected: Each preset has config parameters

### **Phase 3: Advanced Features** ⭐ *CUSTOMIZATION*

6. **🔧 Custom Configurations**
   - Run: "Conservative Analysis (High Thresholds)"
   - ✅ Expected: Fewer impacts due to high thresholds
   - Run: "Aggressive Analysis (Low Thresholds)"  
   - ✅ Expected: More impacts due to low thresholds
   - Run: "Custom Scoring Points"
   - ✅ Expected: Different scoring affects results

7. **📊 Performance Testing**
   - Run: "Quick Analysis (Performance Check)"
   - ✅ Expected: Processing time < 1 second
   - 📊 Response time: < 500ms

### **Phase 4: Error Handling** ⭐ *ROBUSTNESS*

8. **❌ Error Testing**
   - Run: "Analysis with Missing STTM File"
   - ✅ Expected: Status 404 or error response
   - Run: "Analysis with Invalid Configuration"
   - ✅ Expected: Status 400, configuration error message
   - Run: "Validate Non-Existent File (Error Test)"
   - ✅ Expected: `"valid": false`, error message

---

## 🔍 **What to Look For in Results**

### **Impact Analysis Response Structure:**
```json
{
  "success": true,
  "summary": {
    "total_test_cases": 1,
    "total_sttm_changes": 8,
    "critical_impacts": 1,
    "high_impacts": 2,
    "priority_impacts": 3
  },
  "html_report": "<!DOCTYPE html>...",
  "json_report": { /* detailed analysis data */ },
  "processing_time_seconds": 0.213721
}
```

### **Key Validation Points:**

✅ **Functionality Checks:**
- All endpoints return 200 status (except error tests)
- Response times under 5 seconds
- JSON responses are well-formatted
- Analysis produces consistent results

✅ **Analysis Quality Checks:**
- Impact levels detected: Critical, High, Medium, Low
- Affected step numbers identified (e.g., steps 11, 34)
- HTML report contains professional styling
- JSON report has detailed scoring explanations

✅ **Configuration Checks:**
- Different configs produce different results
- Conservative: Fewer impacts (higher thresholds)
- Aggressive: More impacts (lower thresholds)
- Custom scoring affects point calculations

✅ **Error Handling:**
- Missing files return appropriate errors
- Invalid configs return validation errors
- Missing required fields are caught

---

## 📊 **Expected Analysis Results**

### **With Default Configuration:**
- **Total Test Cases:** 1 (TC-65273)
- **STTM Changes:** 8 across 3 tabs
- **Critical Impacts:** 1 (Vendor Inbound DACH VenProxy)  
- **High Impacts:** 2 (NetSuite + VendorInbound tabs)
- **Affected Steps:** 11, 34
- **Processing Time:** ~0.2 seconds

### **With Conservative Configuration:**
- **Critical Impacts:** Should be fewer (higher thresholds)
- **Processing Time:** Similar (~0.2 seconds)

### **With Aggressive Configuration:**
- **Critical Impacts:** Should be more (lower thresholds)
- **Processing Time:** Similar (~0.2 seconds)

---

## 🚀 **Quick Test Sequence** (5 minutes)

Run these requests in order for a complete test:

1. **API Health Check** - Verify server running
2. **List STTM Files** - Confirm files available
3. **Basic Impact Analysis (Default Config)** - Main functionality  
4. **Get Configuration Presets** - Configuration management
5. **Conservative Analysis** - Custom config test
6. **Analysis with Missing STTM File** - Error handling

**✅ If all pass:** Stage 2 is working perfectly!

---

## 🐛 **Troubleshooting**

### **Common Issues:**

❌ **Connection Refused:**
- Check server is running on port 8004
- Restart: `python -m uvicorn api.main:app --host 127.0.0.1 --port 8004 --reload`

❌ **File Not Found:**
- Check files exist in `input_files/sttm/` and `input_files/qtest/`
- Run "List STTM Files" to see available files

❌ **Analysis Fails:**  
- Check server logs for detailed error messages
- Verify file formats are correct (JSON for STTM, Excel for QTEST)

❌ **Slow Performance:**
- Normal processing time: 0.2-1.0 seconds
- If > 5 seconds, check system resources

### **Success Indicators:**
✅ Health check returns API version  
✅ File lists show available files
✅ Analysis completes in < 1 second
✅ HTML reports have professional formatting
✅ Different configs produce different results
✅ Error cases return proper error messages

---

## 📈 **Automated Testing**

The collection includes automated tests that run with each request:

- **Response Time:** < 5 seconds
- **Status Code:** 200 for success cases  
- **Content Type:** application/json
- **JSON Validation:** Valid JSON response
- **Analysis Success:** `success: true` for analysis endpoints
- **Required Fields:** Presence of summary, reports, processing time

**View test results in Postman's "Test Results" tab after running requests.**

---

## 🎯 **Next Steps**

After testing Stage 2:
- All endpoints working? ✅ **Ready for Stage 3**  
- Issues found? 🐛 **Report for fixes**
- Need more features? 📝 **Ready for test step generation**

**Stage 2 provides full CLI feature parity for impact analysis!**
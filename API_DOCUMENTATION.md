# STTM Impact Analysis Tool - Complete API Documentation

## Overview
This API provides comprehensive STTM (System Test Table Mapping) impact analysis and test step generation capabilities. The API uses Azure Blob Storage for file management and supports version-tracked comparisons.

**Base URL**: `http://localhost:8001` (or your configured port)  
**Version**: 1.0.6  
**Content-Type**: `application/json`

---

## Authentication
Currently no authentication required. All endpoints are publicly accessible.

---

## Core Workflow

### 1. Upload QTest File to Azure
### 2. Perform Impact Analysis
### 3. Generate Test Steps (Delta Mode)
### 4. Generate Test Steps (In-Place Mode)

---

## API Endpoints

## 1. Impact Analysis

### `POST /api/analyze-impact-from-comparison`

Performs impact analysis using a pre-uploaded version comparison and QTest file stored in Azure Blob Storage.

#### Request Parameters

**Query Parameters:**
- `comparison_id` (integer, required): ID of the version comparison to analyze

#### Request Example

```http
POST /api/analyze-impact-from-comparison?comparison_id=9
Content-Type: application/json
```

#### Response Schema

```json
{
  "success": true,
  "summary": {
    "total_test_cases": 156,
    "total_sttm_changes": 23,
    "critical_impacts": 8,
    "high_impacts": 12,
    "medium_impacts": 15,
    "low_impacts": 32,
    "priority_impacts": 20,
    "analysis_timestamp": "2025-09-08T19:16:12.345678"
  },
  "json_report": {
    "analysis_metadata": {
      "comparison_id": 9,
      "sttm_file": "STTM_v2.1_extracted.json",
      "qtest_file": "QTest_Cases_v1.3.xlsx",
      "sttm_tabs_analyzed": 8,
      "analysis_timestamp": "2025-09-08T19:16:12.345678",
      "analyzer_version": "2.0",
      "config_used": {
        "impact_analysis": {
          "similarity_threshold": 0.8,
          "case_sensitivity": false,
          "fuzzy_matching": true
        }
      }
    },
    "analysis_results": [
      {
        "test_case_id": "TC_001",
        "test_case_name": "User Login Validation",
        "impact_level": "critical",
        "affected_steps": [
          {
            "step_number": 2,
            "step_description": "Enter username in login field",
            "impact_type": "field_mapping_changed",
            "sttm_changes": [
              {
                "tab_name": "Login_Page",
                "field_name": "username_field",
                "change_type": "modified",
                "old_mapping": "input[name='user']",
                "new_mapping": "input[id='username-input']",
                "confidence_score": 0.95
              }
            ]
          }
        ],
        "recommendations": [
          "Update test step to use new element selector",
          "Verify login functionality after mapping change"
        ]
      }
    ],
    "summary_statistics": {
      "total_test_cases_analyzed": 156,
      "total_affected_test_cases": 67,
      "impact_distribution": {
        "critical": 8,
        "high": 12,
        "medium": 15,
        "low": 32
      },
      "change_type_breakdown": {
        "field_mapping_changed": 45,
        "new_field_added": 12,
        "field_removed": 8,
        "tab_restructured": 3
      }
    }
  },
  "report_links": {
    "html_url": "/api/impact-reports/9/html",
    "json_url": "/api/impact-reports/9/json",
    "html_file": null,
    "json_file": null,
    "blob_urls": {
      "html_url": "https://stexceldifffiles.blob.core.windows.net/output-files/comparison_9/impact/impact_analysis_20250908_191612.html",
      "json_url": "https://stexceldifffiles.blob.core.windows.net/output-files/comparison_9/impact/impact_analysis_20250908_191612.json"
    }
  },
  "analysis_metadata": {
    "sttm_file": "STTM_v2.1_extracted.json",
    "qtest_file": "QTest_Cases_v1.3.xlsx",
    "sttm_tabs_analyzed": 8,
    "analysis_timestamp": "2025-09-08T19:16:12.345678",
    "analyzer_version": "2.0",
    "config_used": {
      "impact_analysis": {
        "similarity_threshold": 0.8,
        "case_sensitivity": false,
        "fuzzy_matching": true
      }
    }
  },
  "processing_time_seconds": 4.2156
}
```

#### Error Response

```json
{
  "detail": "Comparison 999 not found",
  "timestamp": "2025-09-08T19:16:12.345678",
  "endpoint": "/api/analyze-impact-from-comparison",
  "comparison_id": 999
}
```

---

## 2. Test Step Generation

### `POST /api/generate/test-steps-from-comparison`

Generates test steps based on impact analysis results. Supports both delta and in-place generation modes.

#### Request Parameters

**Query Parameters:**
- `comparison_id` (integer, required): ID of the version comparison
- `generation_mode` (string, required): Either "delta" or "in-place"

#### Request Examples

**Delta Mode:**
```http
POST /api/generate/test-steps-from-comparison?comparison_id=9&generation_mode=delta
Content-Type: application/json
```

**In-Place Mode:**
```http
POST /api/generate/test-steps-from-comparison?comparison_id=9&generation_mode=in-place
Content-Type: application/json
```

#### Response Schema

```json
{
  "success": true,
  "generation_mode": "delta",
  "generated_steps": [
    {
      "step_number": 1,
      "action": "verify_element_presence",
      "action_description": "Verify that username input field is present using updated selector",
      "test_case_id": "TC_001",
      "sttm_tab_name": "Login_Page",
      "notes": "Element selector updated from 'input[name=\"user\"]' to 'input[id=\"username-input\"]'",
      "generated_timestamp": "2025-09-08T19:26:50.123456",
      "field_name": "username_field",
      "change_type": "modified"
    },
    {
      "step_number": 2,
      "action": "input_text",
      "action_description": "Enter valid username in the login field",
      "test_case_id": "TC_001",
      "sttm_tab_name": "Login_Page",
      "notes": "Updated to use new element mapping",
      "generated_timestamp": "2025-09-08T19:26:50.123456",
      "field_name": "username_field",
      "change_type": "modified"
    }
  ],
  "updated_test_cases": [
    {
      "test_case_id": "TC_001",
      "test_case_name": "User Login Validation",
      "original_steps_count": 5,
      "updated_steps_count": 7,
      "new_steps_added": 2,
      "steps_modified": 3,
      "impact_level": "critical",
      "generation_notes": "Added verification steps for updated element mappings"
    }
  ],
  "summary": {
    "total_steps_generated": 24,
    "action_breakdown": {
      "verify_element_presence": 8,
      "input_text": 6,
      "click_element": 4,
      "verify_text_content": 3,
      "wait_for_element": 3
    },
    "step_types": {
      "verification": 11,
      "action": 10,
      "wait": 3
    },
    "generation_timestamp": "2025-09-08T19:26:50.123456"
  },
  "metadata": {
    "comparison_id": 9,
    "generation_mode": "delta",
    "sttm_file": "STTM_v2.1_extracted.json",
    "qtest_file": "QTest_Cases_v1.3.xlsx",
    "test_cases_processed": 67,
    "affected_test_cases": 12,
    "generator_version": "2.0",
    "processing_time_seconds": 3.8456,
    "config_applied": {
      "generation_settings": {
        "include_verification_steps": true,
        "add_wait_steps": true,
        "step_naming_convention": "descriptive"
      }
    }
  },
  "report_id": "teststeps_delta_9_20250908_192650",
  "blob_urls": {
    "json_url": "https://stexceldifffiles.blob.core.windows.net/output-files/comparison_9/delta/test_steps_delta_20250908_192650.json",
    "excel_url": "https://stexceldifffiles.blob.core.windows.net/output-files/comparison_9/delta/test_steps_delta_20250908_192650.xlsx"
  }
}
```

#### In-Place Mode Response

When `generation_mode=in-place`, the response structure is identical, but includes:

```json
{
  "generation_mode": "in-place",
  "updated_test_cases": [
    {
      "test_case_id": "TC_001",
      "test_case_name": "User Login Validation",
      "original_steps": [
        {
          "step_number": 1,
          "description": "Navigate to login page",
          "action": "navigate"
        },
        {
          "step_number": 2,
          "description": "Enter username",
          "action": "input_text",
          "element": "input[name='user']"
        }
      ],
      "updated_steps": [
        {
          "step_number": 1,
          "description": "Navigate to login page",
          "action": "navigate"
        },
        {
          "step_number": 2,
          "description": "Enter username",
          "action": "input_text",
          "element": "input[id='username-input']",
          "change_notes": "Updated element selector due to STTM mapping change"
        },
        {
          "step_number": 3,
          "description": "Verify username field is accessible",
          "action": "verify_element_presence",
          "element": "input[id='username-input']",
          "change_notes": "Added verification step for updated mapping"
        }
      ],
      "modifications_summary": {
        "steps_modified": 1,
        "steps_added": 1,
        "steps_removed": 0
      }
    }
  ]
}
```

#### Error Response

```json
{
  "detail": "Invalid generation mode. Must be 'delta' or 'in-place'",
  "timestamp": "2025-09-08T19:26:50.123456",
  "endpoint": "/api/generate/test-steps-from-comparison",
  "comparison_id": 9,
  "generation_mode": "invalid_mode"
}
```

---

## 3. File Download Endpoints

### `GET /api/impact-reports/{comparison_id}/html`

Downloads the HTML impact analysis report from Azure Blob Storage.

#### Request Example
```http
GET /api/impact-reports/9/html
```

#### Response
- **Content-Type**: `text/html; charset=utf-8`
- **Body**: Complete HTML report content

### `GET /api/impact-reports/{comparison_id}/json`

Downloads the JSON impact analysis report from Azure Blob Storage.

#### Request Example
```http
GET /api/impact-reports/9/json
```

#### Response
- **Content-Type**: `application/json; charset=utf-8`
- **Headers**: `Content-Disposition: attachment; filename=impact_analysis_9_20250908_191612.json`
- **Body**: Complete JSON report data

### `GET /api/test-steps/{comparison_id}/{generation_mode}/excel`

Downloads the Excel test steps file from Azure Blob Storage.

#### Request Examples
```http
GET /api/test-steps/9/delta/excel
GET /api/test-steps/9/in-place/excel
```

#### Response
- **Content-Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Headers**: `Content-Disposition: attachment; filename=test_steps_delta_9_20250908_192650.xlsx`
- **Body**: Excel file content

### `GET /api/test-steps/{comparison_id}/{generation_mode}/json`

Downloads the JSON test steps file from Azure Blob Storage.

#### Request Examples
```http
GET /api/test-steps/9/delta/json
GET /api/test-steps/9/in-place/json
```

#### Response
- **Content-Type**: `application/json; charset=utf-8`
- **Headers**: `Content-Disposition: attachment; filename=test_steps_delta_9_20250908_192650.json`
- **Body**: Complete JSON test steps data

---

## 4. Version and Health Endpoints

### `GET /api/version`

Returns current API version information.

#### Response
```json
{
  "success": true,
  "version_info": {
    "version": "1.0.6",
    "build_date": "2025-09-08",
    "build_time": "19:30:15",
    "build_hash": "a1b2c3d4",
    "full_version": "1.0.6-2025-09-08-a1b2c3d4"
  }
}
```

### `GET /api/health`

Returns API health status.

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2025-09-08T19:30:15.123456",
  "version": "1.0.6",
  "environment": "production"
}
```

---

## Error Handling

All endpoints return standardized error responses:

### 404 Not Found
```json
{
  "detail": "Comparison 999 not found",
  "timestamp": "2025-09-08T19:30:15.123456",
  "endpoint": "/api/analyze-impact-from-comparison"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid generation mode. Must be 'delta' or 'in-place'",
  "timestamp": "2025-09-08T19:30:15.123456",
  "endpoint": "/api/generate/test-steps-from-comparison"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Analysis failed: Database connection error",
  "timestamp": "2025-09-08T19:30:15.123456",
  "endpoint": "/api/analyze-impact-from-comparison"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting for production usage.

---

## Data Formats

### Timestamps
All timestamps are in ISO 8601 format: `2025-09-08T19:30:15.123456`

### File URLs
Blob storage URLs follow the pattern:
```
https://stexceldifffiles.blob.core.windows.net/output-files/comparison_{id}/{type}/{filename}
```

Where:
- `{id}`: Comparison ID
- `{type}`: `impact`, `delta`, or `inplace`
- `{filename}`: Timestamped filename

### Generation Modes
- `delta`: Generates additional test steps for changes
- `in-place`: Modifies existing test cases directly

---

## Integration Example

### Complete Workflow
```python
import requests

# 1. Perform Impact Analysis
response = requests.post(
    "http://localhost:8001/api/analyze-impact-from-comparison?comparison_id=9"
)
impact_result = response.json()

# 2. Generate Delta Test Steps
response = requests.post(
    "http://localhost:8001/api/generate/test-steps-from-comparison?comparison_id=9&generation_mode=delta"
)
delta_steps = response.json()

# 3. Generate In-Place Test Steps
response = requests.post(
    "http://localhost:8001/api/generate/test-steps-from-comparison?comparison_id=9&generation_mode=in-place"
)
inplace_steps = response.json()

# 4. Download Excel Report
response = requests.get(
    "http://localhost:8001/api/test-steps/9/delta/excel"
)
with open("test_steps_delta.xlsx", "wb") as f:
    f.write(response.content)
```

---

## Notes for Third-Party Integration

1. **Comparison ID**: Must be a valid comparison ID from the version tracking system
2. **Sequential Processing**: Impact analysis should be completed before test step generation
3. **Blob Storage**: All file outputs are stored in Azure Blob Storage and served via API endpoints
4. **Caching**: Reports are cached in blob storage and database for subsequent access
5. **File Cleanup**: Local temporary files are automatically cleaned up after blob upload

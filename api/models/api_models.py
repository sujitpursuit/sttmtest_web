"""
API Models - Pydantic models for STTM Impact Analysis API
Request and response models for all endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """API health check response"""
    status: str = "healthy"
    timestamp: str
    version: str = "1.0.0"
    environment: str = "development"


class FileInfo(BaseModel):
    """Information about a file"""
    filename: str
    size_bytes: int
    modified: float
    valid: bool
    error: Optional[str] = None


class FileListResponse(BaseModel):
    """Response for file listing endpoints"""
    files: List[FileInfo]
    directory: str
    total_files: int
    valid_files: int


class FileStructure(BaseModel):
    """File structure information"""
    has_data: Optional[bool] = None
    keys_found: Optional[List[str]] = None
    estimated_tabs: Optional[int] = None
    estimated_changes: Optional[int] = None
    worksheets: Optional[List[Dict[str, Any]]] = None
    estimated_test_cases: Optional[int] = None
    estimated_test_steps: Optional[int] = None


class ValidationRequest(BaseModel):
    """Request for file validation endpoints"""
    sttm_file: Optional[str] = Field(None, description="STTM JSON filename")
    qtest_file: Optional[str] = Field(None, description="QTEST Excel filename")


class ValidationResponse(BaseModel):
    """Response for validation endpoints"""
    filename: str
    valid: bool
    file_size: Optional[int] = None
    structure: Optional[FileStructure] = None
    errors: List[str] = []
    warnings: List[str] = []


class CombinedValidationResponse(BaseModel):
    """Response for combined file validation"""
    sttm_validation: ValidationResponse
    qtest_validation: ValidationResponse
    both_valid: bool
    compatibility_check: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: str
    endpoint: str


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None


# Configuration Models (for future use)
class AnalysisConfig(BaseModel):
    """Analysis configuration settings"""
    critical_threshold: Optional[int] = 15
    high_threshold: Optional[int] = 10
    medium_threshold: Optional[int] = 5
    low_threshold: Optional[int] = 1
    tab_name_match_points: Optional[int] = 8
    deleted_field_points: Optional[int] = 10
    modified_field_points: Optional[int] = 6
    added_field_points: Optional[int] = 2
    exact_tab_match_points: Optional[int] = 12
    partial_tab_match_points: Optional[int] = 4
    field_name_match_points: Optional[int] = 5
    sample_data_match_points: Optional[int] = 3


class ConfigPreset(BaseModel):
    """Configuration preset information"""
    name: str
    description: str
    config: AnalysisConfig
    recommended_for: List[str] = []


# Analysis Models (for Stage 2)
class ImpactAnalysisRequest(BaseModel):
    """Request for impact analysis"""
    sttm_file: str = Field(..., description="STTM JSON filename from input_files/sttm/")
    qtest_file: str = Field(..., description="QTEST Excel filename from input_files/qtest/")
    config: Optional[AnalysisConfig] = Field(None, description="Custom analysis configuration")
    include_html_in_response: bool = Field(False, description="Include full HTML content in API response (for backward compatibility)")


class ImpactSummary(BaseModel):
    """Summary of impact analysis results"""
    total_test_cases: int
    total_sttm_changes: int
    critical_impacts: int
    high_impacts: int
    medium_impacts: int
    low_impacts: int
    priority_impacts: int
    analysis_timestamp: str


# ImpactAnalysisResponse moved to api.models.responses


# Test Step Generation Models (for Stage 3)
class TestStepGenerationRequest(BaseModel):
    """Request for test step generation"""
    sttm_file: str = Field(..., description="STTM JSON filename from input_files/sttm/")
    qtest_file: str = Field(..., description="QTEST Excel filename from input_files/qtest/")
    generation_mode: str = Field("delta", description="'delta' for new steps only, 'in_place' for full test case updates")
    config: Optional[AnalysisConfig] = None
    save_to_file: bool = Field(True, description="Save generated steps to output_files directory")
    custom_filename: Optional[str] = Field(None, description="Custom filename for saved report (without extension)")


class GeneratedTestStep(BaseModel):
    """Individual generated test step"""
    step_number: int
    action: str
    action_description: str
    test_case_id: str
    sttm_tab_name: str
    notes: str
    generated_timestamp: str
    field_name: Optional[str] = None
    change_type: Optional[str] = None


class TestStepSummary(BaseModel):
    """Summary of test step generation"""
    total_steps_generated: int
    action_breakdown: Dict[str, int]
    step_types: Dict[str, int]
    generation_timestamp: str


class TestStepGenerationResponse(BaseModel):
    """Response for test step generation"""
    success: bool = True
    generation_mode: str
    generated_steps: Optional[List[GeneratedTestStep]] = None
    updated_test_cases: Optional[List[Dict[str, Any]]] = None
    summary: TestStepSummary
    metadata: Dict[str, Any]
    saved_file_path: Optional[str] = None
    report_id: Optional[str] = None


# Report Management Models
class ReportInfo(BaseModel):
    """Report information summary"""
    report_id: str
    report_type: str
    created_timestamp: str
    file_size_bytes: int
    last_modified: str


class ReportListResponse(BaseModel):
    """Response for listing reports"""
    reports: List[ReportInfo]
    total_reports: int
    filtered_by_type: Optional[str] = None


class StorageStatsResponse(BaseModel):
    """Storage statistics response"""
    total_reports: int
    total_size_bytes: int
    total_size_mb: float
    reports_by_type: Dict[str, int]
    oldest_report: Optional[str]
    newest_report: Optional[str]
    output_directory: str


# Configuration Management Models
class ConfigSaveRequest(BaseModel):
    """Request to save custom configuration"""
    name: str = Field(..., description="Configuration name")
    description: str = Field(..., description="Configuration description")
    config: AnalysisConfig = Field(..., description="Configuration settings")
    recommended_for: List[str] = Field(default=[], description="Recommended use cases")


class SavedConfigInfo(BaseModel):
    """Saved configuration information"""
    name: str
    description: str
    created_timestamp: str
    recommended_for: List[str]


class SavedConfigListResponse(BaseModel):
    """Response for listing saved configurations"""
    configurations: List[SavedConfigInfo]
    total_configurations: int


# Enhanced Health Check Model
class DetailedHealthResponse(BaseModel):
    """Detailed health check response"""
    status: str
    timestamp: str
    version: str
    environment: str
    uptime_seconds: float
    system_info: Dict[str, Any]
    storage_info: Dict[str, Any]
    dependencies_status: Dict[str, str]
    recent_activity: Dict[str, int]
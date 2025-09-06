"""
Response Models - Detailed Pydantic models for Stage 2 API responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class ImpactSummary(BaseModel):
    """Summary statistics for impact analysis"""
    total_test_cases: int = Field(..., description="Total number of test cases analyzed")
    total_sttm_changes: int = Field(..., description="Total number of STTM changes processed")
    critical_impacts: int = Field(..., description="Number of critical impact test cases")
    high_impacts: int = Field(..., description="Number of high impact test cases") 
    medium_impacts: int = Field(..., description="Number of medium impact test cases")
    low_impacts: int = Field(..., description="Number of low impact test cases")
    priority_impacts: int = Field(..., description="Total critical + high impacts requiring attention")
    analysis_timestamp: str = Field(..., description="ISO timestamp when analysis started")


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis process"""
    sttm_file: str = Field(..., description="STTM filename used")
    qtest_file: str = Field(..., description="QTEST filename used")
    sttm_tabs_analyzed: int = Field(..., description="Number of STTM tabs analyzed")
    analysis_timestamp: str = Field(..., description="Analysis timestamp from report")
    analyzer_version: str = Field(default="2.0", description="Analyzer version used")
    config_used: Dict[str, Any] = Field(..., description="Configuration settings applied")


class ReportLinks(BaseModel):
    """Links to generated report files"""
    html_url: Optional[str] = Field(None, description="API URL to access HTML report")
    json_url: Optional[str] = Field(None, description="API URL to access JSON report")
    html_file: Optional[str] = Field(None, description="Full file path to HTML report")
    json_file: Optional[str] = Field(None, description="Full file path to JSON report")


class ImpactAnalysisResponse(BaseModel):
    """Complete response for impact analysis endpoint"""
    success: bool = Field(True, description="Whether analysis completed successfully")
    summary: ImpactSummary = Field(..., description="Analysis summary statistics")
    json_report: Dict[str, Any] = Field(..., description="Detailed JSON analysis data")
    report_links: ReportLinks = Field(..., description="Links to saved report files")
    analysis_metadata: AnalysisMetadata = Field(..., description="Analysis process metadata")
    processing_time_seconds: float = Field(..., description="Total processing time in seconds")
    html_report: Optional[str] = Field(None, description="Complete HTML report content (optional)")


class ConfigPresetInfo(BaseModel):
    """Information about a configuration preset"""
    name: str = Field(..., description="Display name of the preset")
    description: str = Field(..., description="Description of when to use this preset")
    config: Dict[str, Any] = Field(..., description="Configuration settings")
    recommended_for: List[str] = Field(..., description="Use cases this preset is recommended for")


class ConfigPresetsResponse(BaseModel):
    """Response for configuration presets endpoint"""
    presets: Dict[str, ConfigPresetInfo] = Field(..., description="Available configuration presets")
    default: str = Field(..., description="Default preset name")
    total_presets: int = Field(..., description="Total number of available presets")


class AnalysisCompatibilityCheck(BaseModel):
    """File compatibility check for analysis"""
    compatible: bool = Field(..., description="Whether files are compatible for analysis")
    errors: List[str] = Field(default_factory=list, description="Any validation errors found")
    sttm_valid: bool = Field(..., description="Whether STTM file is valid")
    qtest_valid: bool = Field(..., description="Whether QTEST file is valid")
    estimated_processing_time: Optional[str] = Field(None, description="Estimated time for analysis")
    sttm_structure: Optional[Dict[str, Any]] = Field(None, description="STTM file structure info")
    qtest_structure: Optional[Dict[str, Any]] = Field(None, description="QTEST file structure info")


class ExecutiveSummary(BaseModel):
    """Executive summary for business stakeholders"""
    headline: str = Field(..., description="One-line summary of analysis results")
    priority_message: str = Field(..., description="Key message for decision makers")
    recommendations: List[str] = Field(..., description="Recommended actions")
    impact_breakdown: Dict[str, int] = Field(..., description="Impact counts by level")
    files_analyzed: Dict[str, str] = Field(..., description="Files processed in analysis")
    processing_summary: str = Field(..., description="Processing time and efficiency info")


class AnalysisErrorResponse(BaseModel):
    """Error response for failed analysis"""
    success: bool = Field(False, description="Analysis success status")
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error encountered")
    timestamp: str = Field(..., description="When the error occurred")
    failed_at_step: Optional[str] = Field(None, description="Which analysis step failed")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Additional debug information")
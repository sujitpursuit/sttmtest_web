"""
Custom Exceptions - HTTP exceptions for STTM Impact Analysis API
"""

from fastapi import HTTPException
from typing import Optional, Dict, Any


class STTMAPIException(HTTPException):
    """Base exception for STTM API"""
    
    def __init__(self, status_code: int, detail: str, headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class FileNotFoundError(STTMAPIException):
    """File not found in input_files directory"""
    
    def __init__(self, filename: str, file_type: str = "file"):
        detail = f"{file_type.upper()} file not found: {filename}"
        super().__init__(status_code=404, detail=detail)


class FileValidationError(STTMAPIException):
    """File validation failed"""
    
    def __init__(self, filename: str, validation_errors: list):
        error_list = "; ".join(validation_errors)
        detail = f"File validation failed for {filename}: {error_list}"
        super().__init__(status_code=400, detail=detail)


class InvalidFileTypeError(STTMAPIException):
    """Invalid file type provided"""
    
    def __init__(self, filename: str, expected_type: str):
        detail = f"Invalid file type for {filename}. Expected {expected_type} file."
        super().__init__(status_code=400, detail=detail)


class AnalysisError(STTMAPIException):
    """Analysis processing error"""
    
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=f"Analysis error: {detail}")


class ConfigurationError(STTMAPIException):
    """Configuration error"""
    
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=f"Configuration error: {detail}")


class ProcessingTimeoutError(STTMAPIException):
    """Processing timeout error"""
    
    def __init__(self, operation: str, timeout_seconds: int):
        detail = f"{operation} operation timed out after {timeout_seconds} seconds"
        super().__init__(status_code=408, detail=detail)


class TestStepGenerationError(STTMAPIException):
    """Test step generation error"""
    
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=f"Test step generation error: {detail}")


class ReportNotFoundError(STTMAPIException):
    """Report not found error"""
    
    def __init__(self, report_id: str):
        detail = f"Report not found: {report_id}"
        super().__init__(status_code=404, detail=detail)


class ReportStorageError(STTMAPIException):
    """Report storage error"""
    
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=f"Report storage error: {detail}")


def create_error_response(error: Exception, endpoint: str) -> Dict[str, Any]:
    """Create standardized error response"""
    from datetime import datetime
    
    return {
        "error": str(error),
        "detail": getattr(error, 'detail', None),
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint
    }
"""
FastAPI Main Application - STTM Impact Analysis API
Stage 1: Foundation & File Management
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import shutil
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import existing modules
sys.path.append(str(Path(__file__).parent.parent))

# Import API components
from api.services.file_service import FileService
from api.services.analysis_service import AnalysisService
from api.services.test_step_service import TestStepService
from api.services.report_service import ReportService
from api.services.config_service import ConfigService
from api.services.app_version_service import app_version_service
from api.services.version_tracking_service import VersionTrackingService
from api.services.azure_blob_service import AzureBlobService
from api.services.qtest_azure_service import QTestAzureService
from api.services.qtest_blob_reader_service import QTestBlobReaderService
from api.middleware.logging import EnhancedRequestLoggingMiddleware
from api.models.api_models import (
    HealthResponse, FileListResponse, ValidationRequest, ValidationResponse,
    CombinedValidationResponse, ErrorResponse, FileInfo,
    TestStepGenerationResponse, ReportListResponse,
    StorageStatsResponse, ConfigSaveRequest, SavedConfigListResponse,
    DetailedHealthResponse
)
from api.models.responses import (
    ImpactAnalysisResponse, ConfigPresetsResponse, AnalysisCompatibilityCheck,
    ExecutiveSummary
)
from api.utils.exceptions import (
    FileNotFoundError, FileValidationError, InvalidFileTypeError,
    AnalysisError, ConfigurationError, create_error_response
)
from api.utils.response_optimization import ResponseOptimizer

# Import existing CLI components (for validation)
from parsers.sttm_parser import parse_sttm_file
from parsers.qtest_parser import parse_qtest_file
from utils.logger import get_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)


# Create FastAPI app
app = FastAPI(
    title="STTM Impact Analysis API",
    description="REST API for STTM Impact Analysis Tool - Convert CLI functionality to web service",
    version="1.0.0-stage1",
    contact={
        "name": "STTM Analysis Team",
        "email": "admin@sttmanalysis.com"
    },
    license_info={
        "name": "Internal Use",
        "url": "https://internal.company.com/license"
    }
)

# Global service instances
file_service = FileService()
analysis_service = AnalysisService()
test_step_service = TestStepService()
report_service = ReportService()
config_service = ConfigService()
version_tracking_service = VersionTrackingService()
azure_blob_service = AzureBlobService()
response_optimizer = ResponseOptimizer(logger)

# Add request logging middleware
logging_middleware = EnhancedRequestLoggingMiddleware(app=None, logger=logger)
app.add_middleware(EnhancedRequestLoggingMiddleware)

# Mount static files for frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    logger.info(f"Static files mounted at /static from: {frontend_path}")
else:
    logger.warning(f"Frontend directory not found: {frontend_path}")

# Serve frontend index.html at root
@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html file at root"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

# Serve frontend index.html at /frontend route
@app.get("/frontend")
async def serve_frontend_route():
    """Serve the frontend index.html file at /frontend"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

# Handle trailing slash for frontend
@app.get("/frontend/")
async def serve_frontend_trailing_slash():
    """Serve the frontend index.html file at /frontend/"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

# Mount reports directory for serving generated reports
reports_path = Path(__file__).parent.parent / "reports"
if reports_path.exists():
    app.mount("/reports", StaticFiles(directory=str(reports_path)), name="reports")
    logger.info(f"Reports directory mounted at /reports from: {reports_path}")
else:
    logger.warning(f"Reports directory not found: {reports_path}")
    
# Mount output_files directory for serving generated test files
output_path = Path(__file__).parent.parent / "output_files"
if output_path.exists():
    app.mount("/output_files", StaticFiles(directory=str(output_path)), name="output_files")
    logger.info(f"Output files directory mounted at /output_files from: {output_path}")
else:
    logger.warning(f"Output files directory not found: {output_path}")

# API Version endpoint
@app.get("/api/version")
async def get_version():
    """Get application version information"""
    try:
        version_info = app_version_service.get_version_info()
        return {
            "success": True,
            "version_info": version_info
        }
    except Exception as e:
        logger.error(f"Error getting version info: {e}")
        return {
            "success": False,
            "error": str(e),
            "version_info": {
                "version": "1.0.1",
                "build_date": "2025-09-08",
                "build_hash": "unknown"
            }
        }


def get_file_service() -> FileService:
    """Dependency for file service"""
    return file_service


def get_analysis_service() -> AnalysisService:
    """Dependency for analysis service"""
    return analysis_service


def get_test_step_service() -> TestStepService:
    """Dependency for test step service"""
    return test_step_service


def get_report_service() -> ReportService:
    """Dependency for report service"""
    return report_service


def get_config_service() -> ConfigService:
    """Dependency for config service"""
    return config_service


def get_version_tracking_service() -> VersionTrackingService:
    """Dependency for version tracking service"""
    return version_tracking_service


def get_azure_blob_service() -> AzureBlobService:
    """Dependency for Azure blob service"""
    return azure_blob_service


@app.get("/", response_model=HealthResponse)
async def health_check():
    """API health check and information endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0-stage3",
        environment=os.getenv('ENVIRONMENT', 'development')
    )


@app.get("/app")
async def serve_frontend():
    """Serve the frontend application"""
    frontend_file = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_file.exists():
        return FileResponse(
            path=str(frontend_file),
            media_type="text/html"
        )
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/api/health")
async def detailed_health_check():
    """Comprehensive health check with system information"""
    import platform
    from pathlib import Path
    
    try:
        # Basic health info
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0-stage3",
            "environment": os.getenv('ENVIRONMENT', 'development'),
            "uptime_seconds": 0,
            "system_info": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0],
                "hostname": platform.node(),
                "note": "Basic system info - install psutil for detailed metrics"
            },
            "storage_info": {
                "note": "Storage stats available via /api/storage/stats"
            },
            "dependencies_status": {
                "directories": {
                    "input_files": "available" if Path("input_files").exists() else "missing",
                    "output_files": "available" if Path("output_files").exists() else "missing",
                    "input_files_sttm": "available" if Path("input_files/sttm").exists() else "missing",
                    "input_files_qtest": "available" if Path("input_files/qtest").exists() else "missing"
                },
                "services": "operational"
            },
            "recent_activity": {
                "note": "Request logging active"
            }
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0-stage3",
            "environment": os.getenv('ENVIRONMENT', 'development'),
            "error": str(e)
        }


@app.get("/api/files/sttm", response_model=FileListResponse)
async def list_sttm_files(fs: FileService = Depends(get_file_service)):
    """List all available STTM JSON files in input_files/sttm/"""
    try:
        logger.info("Listing STTM files")
        files_data = fs.list_sttm_files()
        
        # Convert to FileInfo models
        file_infos = []
        for file_data in files_data:
            file_infos.append(FileInfo(**file_data))
        
        valid_count = sum(1 for f in file_infos if f.valid)
        
        return FileListResponse(
            files=file_infos,
            directory="input_files/sttm",
            total_files=len(file_infos),
            valid_files=valid_count
        )
        
    except Exception as e:
        logger.error(f"Error listing STTM files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list STTM files: {str(e)}"
        )


@app.get("/api/files/qtest", response_model=FileListResponse)
async def list_qtest_files(fs: FileService = Depends(get_file_service)):
    """List all available QTEST Excel files in input_files/qtest/"""
    try:
        logger.info("Listing QTEST files")
        files_data = fs.list_qtest_files()
        
        # Convert to FileInfo models
        file_infos = []
        for file_data in files_data:
            file_infos.append(FileInfo(**file_data))
        
        valid_count = sum(1 for f in file_infos if f.valid)
        
        return FileListResponse(
            files=file_infos,
            directory="input_files/qtest",
            total_files=len(file_infos),
            valid_files=valid_count
        )
        
    except Exception as e:
        logger.error(f"Error listing QTEST files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list QTEST files: {str(e)}"
        )


@app.post("/api/upload-validate/sttm", response_model=ValidationResponse)
async def upload_and_validate_sttm(
    file: UploadFile = File(...),
    fs: FileService = Depends(get_file_service)
):
    """Upload and validate a STTM JSON file"""
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="File must be a JSON file")
        
        # Save uploaded file
        sttm_dir = Path(__file__).parent.parent / "input_files" / "sttm"
        sttm_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = sttm_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate the file
        logger.info(f"Validating uploaded STTM file: {file.filename}")
        
        # Use file service for basic validation
        validation_result = fs.validate_sttm_file(file.filename)
        
        # Enhanced validation using existing CLI parser
        if validation_result["valid"]:
            try:
                # Use existing CLI parser for thorough validation
                sttm_doc = parse_sttm_file(str(file_path), logger)
                
                # Add parser-specific validation info
                validation_result["structure"]["estimated_tabs"] = sttm_doc.total_tabs
                validation_result["structure"]["estimated_changes"] = sttm_doc.total_changes
                validation_result["structure"]["has_changed_tabs"] = len(sttm_doc.changed_tabs) > 0
                
                logger.info(f"STTM validation successful: {file.filename}")
                
            except Exception as parser_error:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Parser validation failed: {str(parser_error)}")
                logger.warning(f"STTM parser validation failed: {parser_error}")
        
        return ValidationResponse(**validation_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STTM upload/validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload/validation failed: {str(e)}"
        )


@app.post("/api/upload-validate/qtest", response_model=ValidationResponse)
async def upload_and_validate_qtest(
    file: UploadFile = File(...),
    fs: FileService = Depends(get_file_service)
):
    """Upload and validate a QTest Excel file"""
    try:
        # Validate file type
        if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")
        
        # Save uploaded file
        qtest_dir = Path(__file__).parent.parent / "input_files" / "qtest"
        qtest_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = qtest_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate the file
        logger.info(f"Validating uploaded QTest file: {file.filename}")
        
        # Use file service for basic validation
        validation_result = fs.validate_qtest_file(file.filename)
        
        # Enhanced validation using existing CLI parser
        if validation_result["valid"]:
            try:
                # Use existing CLI parser for thorough validation
                qtest_doc = parse_qtest_file(str(file_path), logger)
                
                # Add parser-specific validation info
                validation_result["structure"]["estimated_test_cases"] = qtest_doc.total_test_cases
                validation_result["structure"]["total_test_steps"] = sum(
                    tc.get_step_count() for tc in qtest_doc.test_cases
                )
                validation_result["structure"]["id_pattern"] = qtest_doc.detected_id_pattern
                validation_result["structure"]["id_format_description"] = qtest_doc.id_format_description
                
                logger.info(f"QTest validation successful: {file.filename}")
                
            except Exception as parser_error:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Parser validation failed: {str(parser_error)}")
                logger.warning(f"QTest parser validation failed: {parser_error}")
        
        return ValidationResponse(**validation_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QTest upload/validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload/validation failed: {str(e)}"
        )


@app.post("/api/upload/qtest")
async def upload_qtest_file(
    file: UploadFile = File(...)
):
    """Upload QTest file for comparison-based workflow - simple upload without validation"""
    try:
        logger.info(f"Uploading QTest file: {file.filename}")
        
        # Validate file extension
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Only Excel files (.xlsx, .xls) are allowed"
            )
        
        # Create qtest directory if it doesn't exist
        from pathlib import Path
        qtest_dir = Path(__file__).parent.parent / "input_files" / "qtest"
        qtest_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file to qtest directory
        qtest_path = qtest_dir / file.filename
        with open(qtest_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"QTest file uploaded successfully: {file.filename}")
        
        return {
            "success": True,
            "filename": file.filename,
            "message": f"QTest file '{file.filename}' uploaded successfully",
            "file_path": str(qtest_path),
            "file_size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QTest upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@app.post("/api/validate/sttm", response_model=ValidationResponse)
async def validate_sttm_file(
    request: ValidationRequest,
    fs: FileService = Depends(get_file_service)
):
    """Validate a single STTM JSON file using existing CLI parser"""
    if not request.sttm_file:
        raise HTTPException(status_code=400, detail="sttm_file is required")
    
    try:
        logger.info(f"Validating STTM file: {request.sttm_file}")
        
        # Use file service for basic validation
        validation_result = fs.validate_sttm_file(request.sttm_file)
        
        # Enhanced validation using existing CLI parser
        if validation_result["valid"]:
            try:
                file_path = fs.get_sttm_path(request.sttm_file)
                # Use existing CLI parser for thorough validation
                sttm_doc = parse_sttm_file(file_path, logger)
                
                # Add parser-specific validation info
                validation_result["structure"]["estimated_tabs"] = sttm_doc.total_tabs
                validation_result["structure"]["estimated_changes"] = sttm_doc.total_changes
                validation_result["structure"]["has_changed_tabs"] = len(sttm_doc.changed_tabs) > 0
                
                logger.info(f"STTM validation successful: {request.sttm_file}")
                
            except Exception as parser_error:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Parser validation failed: {str(parser_error)}")
                logger.warning(f"STTM parser validation failed: {parser_error}")
        
        return ValidationResponse(**validation_result)
        
    except FileNotFoundError:
        raise FileNotFoundError(request.sttm_file, "STTM")
    except Exception as e:
        logger.error(f"STTM validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@app.post("/api/validate/qtest", response_model=ValidationResponse)
async def validate_qtest_file(
    request: ValidationRequest,
    fs: FileService = Depends(get_file_service)
):
    """Validate a single QTEST Excel file using existing CLI parser"""
    if not request.qtest_file:
        raise HTTPException(status_code=400, detail="qtest_file is required")
    
    try:
        logger.info(f"Validating QTEST file: {request.qtest_file}")
        
        # Use file service for basic validation
        validation_result = fs.validate_qtest_file(request.qtest_file)
        
        # Enhanced validation using existing CLI parser
        if validation_result["valid"]:
            try:
                file_path = fs.get_qtest_path(request.qtest_file)
                # Use existing CLI parser for thorough validation
                qtest_doc = parse_qtest_file(file_path, logger)
                
                # Add parser-specific validation info
                validation_result["structure"]["estimated_test_cases"] = qtest_doc.total_test_cases
                validation_result["structure"]["total_test_steps"] = sum(
                    tc.get_step_count() for tc in qtest_doc.test_cases
                )
                validation_result["structure"]["id_pattern"] = qtest_doc.detected_id_pattern
                validation_result["structure"]["id_format_description"] = qtest_doc.id_format_description
                
                logger.info(f"QTEST validation successful: {request.qtest_file}")
                
            except Exception as parser_error:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Parser validation failed: {str(parser_error)}")
                logger.warning(f"QTEST parser validation failed: {parser_error}")
        
        return ValidationResponse(**validation_result)
        
    except FileNotFoundError:
        raise FileNotFoundError(request.qtest_file, "QTEST")
    except Exception as e:
        logger.error(f"QTEST validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@app.post("/api/validate/both", response_model=CombinedValidationResponse)
async def validate_both_files(
    request: ValidationRequest,
    fs: FileService = Depends(get_file_service)
):
    """Validate both STTM and QTEST files together"""
    if not request.sttm_file or not request.qtest_file:
        raise HTTPException(
            status_code=400,
            detail="Both sttm_file and qtest_file are required"
        )
    
    try:
        logger.info(f"Validating both files: {request.sttm_file} + {request.qtest_file}")
        
        # Validate STTM file
        sttm_request = ValidationRequest(sttm_file=request.sttm_file)
        sttm_validation = await validate_sttm_file(sttm_request, fs)
        
        # Validate QTEST file
        qtest_request = ValidationRequest(qtest_file=request.qtest_file)
        qtest_validation = await validate_qtest_file(qtest_request, fs)
        
        # Check overall compatibility
        both_valid = sttm_validation.valid and qtest_validation.valid
        
        compatibility_check = {
            "files_compatible": both_valid,
            "ready_for_analysis": both_valid,
            "estimated_processing_time": "2-5 minutes" if both_valid else "N/A"
        }
        
        if both_valid:
            logger.info(f"Both files validated successfully and are compatible")
        else:
            logger.warning(f"File validation issues found")
        
        return CombinedValidationResponse(
            sttm_validation=sttm_validation,
            qtest_validation=qtest_validation,
            both_valid=both_valid,
            compatibility_check=compatibility_check
        )
        
    except Exception as e:
        logger.error(f"Combined validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Combined validation failed: {str(e)}"
        )


# NOTE: /api/analyze-impact endpoint removed - not used by frontend
# Frontend uses /api/analyze-impact-from-comparison exclusively
# Legacy endpoint for file uploads is no longer needed

@app.get("/api/config/presets", response_model=ConfigPresetsResponse)
async def get_config_presets(
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """Get available analysis configuration presets"""
    try:
        logger.info("Retrieving configuration presets")
        presets_data = analysis_service.get_available_config_presets()
        
        # Convert to response model
        from api.models.responses import ConfigPresetInfo
        
        presets_converted = {}
        for key, preset in presets_data["presets"].items():
            presets_converted[key] = ConfigPresetInfo(**preset)
        
        return ConfigPresetsResponse(
            presets=presets_converted,
            default=presets_data["default"],
            total_presets=presets_data["total_presets"]
        )
        
    except Exception as e:
        logger.error(f"Error retrieving config presets: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve configuration presets: {str(e)}"
        )


# ============================
# PHASE 3 ENDPOINTS START HERE
# ============================


@app.get("/api/reports", response_model=ReportListResponse)
async def list_reports(
    report_type: str = None,
    report_service: ReportService = Depends(get_report_service)
):
    """List all saved reports"""
    try:
        logger.info(f"Listing reports" + (f" of type '{report_type}'" if report_type else ""))
        
        reports = report_service.list_reports(report_type)
        
        return ReportListResponse(
            reports=reports,
            total_reports=len(reports),
            filtered_by_type=report_type
        )
        
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list reports: {str(e)}"
        )


@app.get("/api/reports/{report_id}")
async def get_report(
    report_id: str,
    data_only: bool = False,
    report_service: ReportService = Depends(get_report_service)
):
    """Retrieve a specific report by ID"""
    try:
        logger.info(f"Retrieving report: {report_id}")
        
        if data_only:
            report_data = report_service.get_report_data_only(report_id)
        else:
            report_data = report_service.get_report(report_id)
        
        return JSONResponse(content=report_data)
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Failed to retrieve report {report_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve report: {str(e)}"
        )


@app.delete("/api/reports/{report_id}")
async def delete_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    """Delete a specific report"""
    try:
        logger.info(f"Deleting report: {report_id}")
        
        success = report_service.delete_report(report_id)
        
        return JSONResponse(content={
            "success": success,
            "message": f"Report {report_id} deleted successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Failed to delete report {report_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete report: {str(e)}"
        )


@app.get("/api/storage/stats", response_model=StorageStatsResponse)
async def get_storage_stats(
    report_service: ReportService = Depends(get_report_service)
):
    """Get storage statistics for reports"""
    try:
        logger.info("Retrieving storage statistics")
        
        stats = report_service.get_storage_stats()
        
        return StorageStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get storage statistics: {str(e)}"
        )


@app.get("/api/reports/{filename}")
async def get_report_file(filename: str):
    """Serve report files from the reports directory (legacy endpoint)"""
    try:
        reports_dir = Path("reports")
        file_path = reports_dir / filename
        
        # Security check - ensure file is in reports directory
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Report file not found: {filename}")
        
        if not str(file_path.resolve()).startswith(str(reports_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Determine media type based on file extension
        if filename.endswith('.html'):
            media_type = 'text/html'
        elif filename.endswith('.json'):
            media_type = 'application/json'
        else:
            media_type = 'application/octet-stream'
        
        logger.info(f"Serving report file: {filename}")
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error serving report file {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error serving report file: {str(e)}"
        )


@app.post("/api/config/save")
async def save_config(
    request: ConfigSaveRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Save a custom analysis configuration"""
    try:
        logger.info(f"Saving configuration: {request.name}")
        
        config_id = config_service.save_config(request)
        
        return JSONResponse(content={
            "success": True,
            "config_id": config_id,
            "message": f"Configuration '{request.name}' saved successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        if "already exists" in str(e).lower():
            raise HTTPException(status_code=409, detail=str(e))
        logger.error(f"Failed to save configuration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save configuration: {str(e)}"
        )


@app.get("/api/config/saved", response_model=SavedConfigListResponse)
async def list_saved_configs(
    config_service: ConfigService = Depends(get_config_service)
):
    """List all saved configurations"""
    try:
        logger.info("Listing saved configurations")
        
        configs = config_service.list_configs()
        
        return SavedConfigListResponse(
            configurations=configs,
            total_configurations=len(configs)
        )
        
    except Exception as e:
        logger.error(f"Failed to list configurations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list configurations: {str(e)}"
        )


@app.get("/api/config/saved/{config_id}")
async def get_saved_config(
    config_id: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Get a specific saved configuration"""
    try:
        logger.info(f"Retrieving configuration: {config_id}")
        
        config_data = config_service.get_config(config_id)
        
        return JSONResponse(content=config_data)
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Failed to retrieve configuration {config_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )


@app.delete("/api/config/saved/{config_id}")
async def delete_saved_config(
    config_id: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Delete a saved configuration"""
    try:
        logger.info(f"Deleting configuration: {config_id}")
        
        success = config_service.delete_config(config_id)
        
        return JSONResponse(content={
            "success": success,
            "message": f"Configuration {config_id} deleted successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        logger.error(f"Failed to delete configuration {config_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete configuration: {str(e)}"
        )


# ============================
# VERSION TRACKING ENDPOINTS
# ============================

@app.get("/api/tracked-files")
async def get_tracked_files(
    tracking_service: VersionTrackingService = Depends(get_version_tracking_service)
):
    """Get all active tracked files from the database"""
    try:
        logger.info("Fetching tracked files from database")
        
        # Check if service is properly configured
        if not tracking_service.connection_string:
            # Return mock data for testing if no database configured
            logger.warning("Database not configured, returning mock data")
            return {
                "success": True,
                "message": "Mock data - configure database connection",
                "files": [
                    {
                        "id": 1,
                        "file_name": "STTM_Sample.xlsx",
                        "friendly_name": "Sample STTM File",
                        "created_at": "2025-09-01T00:00:00"
                    }
                ]
            }
        
        files = tracking_service.get_tracked_files()
        
        return {
            "success": True,
            "count": len(files),
            "files": files
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch tracked files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tracked files: {str(e)}"
        )


@app.get("/api/tracked-files/{file_id}/comparisons")
async def get_file_comparisons(
    file_id: int,
    tracking_service: VersionTrackingService = Depends(get_version_tracking_service)
):
    """Get all comparisons for a specific tracked file with version details"""
    try:
        logger.info(f"Fetching comparisons for file {file_id}")
        
        # Check if service is properly configured
        if not tracking_service.connection_string:
            # Return mock data for testing
            logger.warning("Database not configured, returning mock data")
            return {
                "success": True,
                "message": "Mock data - configure database connection",
                "file_id": file_id,
                "comparisons": [
                    {
                        "comparison_id": 1,
                        "comparison_title": "Version 1 vs Version 2",
                        "from_sequence": 1,
                        "from_sharepoint_version": "1.0",
                        "from_modified": "2025-09-01T10:00:00",
                        "to_sequence": 2,
                        "to_sharepoint_version": "2.0",
                        "to_modified": "2025-09-01T11:00:00",
                        "total_changes": 5,
                        "added_mappings": 2,
                        "modified_mappings": 2,
                        "deleted_mappings": 1,
                        "comparison_taken_at": "2025-09-01T12:00:00"
                    }
                ]
            }
        
        comparisons = tracking_service.get_file_comparisons(file_id)
        
        return {
            "success": True,
            "file_id": file_id,
            "count": len(comparisons),
            "comparisons": comparisons
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch comparisons for file {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch comparisons: {str(e)}"
        )


@app.post("/api/analyze-impact-from-comparison")
async def analyze_impact_from_comparison(
    comparison_id: int = Query(...),
    tracking_service: VersionTrackingService = Depends(get_version_tracking_service),
    blob_service: AzureBlobService = Depends(get_azure_blob_service),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    optimize_response: bool = True
):
    """Run impact analysis using a comparison from database and QTest from Azure Blob"""
    try:
        logger.info(f"Starting impact analysis with comparison {comparison_id}")
        
        # Get comparison details from database
        comparison = tracking_service.get_comparison_details(comparison_id)
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail=f"Comparison {comparison_id} not found"
            )
        
        # Fetch JSON from Azure Blob
        json_url = comparison.get('json_report_url')
        local_path = comparison.get('local_json_path')
        
        if not json_url:
            raise HTTPException(
                status_code=400,
                detail="Comparison does not have a JSON report URL"
            )
        
        logger.info("Fetching comparison JSON from Azure Blob")
        json_content = blob_service.fetch_comparison_json(json_url, local_path)
        
        # Validate JSON structure
        if not blob_service.validate_json_structure(json_content):
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON structure in comparison"
            )
        
        # Import Path for file operations
        from pathlib import Path
        import json
        import tempfile
        
        # Create temporary STTM JSON file from fetched content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_sttm:
            json.dump(json_content, temp_sttm)
            temp_sttm_path = temp_sttm.name
        
        try:
            # Copy the JSON to input_files/sttm temporarily
            sttm_dir = Path(__file__).parent.parent / "input_files" / "sttm"
            sttm_dir.mkdir(parents=True, exist_ok=True)
            
            temp_sttm_name = f"comparison_{comparison_id}_temp.json"
            sttm_file_path = sttm_dir / temp_sttm_name
            
            with open(sttm_file_path, 'w') as f:
                json.dump(json_content, f)
            
            # Get QTest file from Azure Blob Storage
            qtest_reader = QTestBlobReaderService()
            qtest_success, qtest_temp_path, qtest_error = qtest_reader.get_qtest_from_comparison(comparison_id)
            
            if not qtest_success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Failed to get QTest file: {qtest_error}"
                )
            
            # Get just the filename from the temp path for the existing logic
            qtest_filename = Path(qtest_temp_path).name
            
            # Run analysis using filename (same as original endpoint)
            result = analysis_service.run_impact_analysis(
                sttm_file=temp_sttm_name,
                qtest_file=qtest_filename,
                config=None,
                include_html_in_response=False
            )
            
            # Add comparison info and temp file names to result for reuse in test generation
            result['comparison_info'] = {
                'comparison_id': comparison_id,
                'comparison_title': comparison.get('comparison_title'),
                'file_name': comparison.get('file_friendly_name')
            }
            
            # Add temp file names for reuse in test generation (don't clean them up)
            result['temp_files'] = {
                'sttm_file': temp_sttm_name,
                'qtest_file': qtest_filename
            }
            
            # PHASE 2: Upload impact analysis reports to blob storage
            try:
                # Get the local file paths from report_links
                if 'report_links' in result and result['report_links']:
                    html_file_path = result['report_links'].get('html_file')
                    json_file_path = result['report_links'].get('json_file')
                    
                    if html_file_path or json_file_path:
                        # Initialize blob service for impact reports
                        from api.services.output_blob_service import OutputBlobService
                        output_blob_service = OutputBlobService()
                        
                        # Upload to blob storage
                        blob_urls = output_blob_service.upload_impact_analysis_reports(
                            comparison_id=comparison_id,
                            html_file_path=html_file_path,
                            json_file_path=json_file_path
                        )
                        
                        # Update database with blob URLs
                        if blob_urls['html_url'] or blob_urls['json_url']:
                            tracking_service.update_impact_analysis_urls(
                                comparison_id=comparison_id,
                                html_blob_url=blob_urls.get('html_url'),
                                json_blob_url=blob_urls.get('json_url')
                            )
                            
                            # Update response with API endpoints instead of local file paths
                            result['report_links']['html_url'] = f"/api/impact-reports/{comparison_id}/html" if blob_urls['html_url'] else None
                            result['report_links']['json_url'] = f"/api/impact-reports/{comparison_id}/json" if blob_urls['json_url'] else None
                            result['report_links']['blob_urls'] = blob_urls
                            
                            logger.info(f"Updated impact analysis report URLs for comparison {comparison_id}")
                        
                        # Clean up local report files after upload
                        if html_file_path and os.path.exists(html_file_path):
                            os.unlink(html_file_path)
                            logger.info(f"Cleaned up local HTML file: {html_file_path}")
                        if json_file_path and os.path.exists(json_file_path):
                            os.unlink(json_file_path)
                            logger.info(f"Cleaned up local JSON file: {json_file_path}")
                    
            except Exception as e:
                logger.error(f"Failed to upload impact analysis reports to blob storage: {e}")
                # Continue with local file serving if blob upload fails
            
            # Optimize response for large reports (same as original endpoint)
            if optimize_response:
                return response_optimizer.optimize_response(result, compression=True)
            else:
                return ImpactAnalysisResponse(**result)
            
        finally:
            # Cleanup temporary files
            if os.path.exists(temp_sttm_path):
                os.unlink(temp_sttm_path)
            if sttm_file_path.exists():
                sttm_file_path.unlink()
            # Cleanup QTest temp file from Azure
            if 'qtest_temp_path' in locals() and qtest_temp_path:
                qtest_reader.cleanup_temp_file(qtest_temp_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Impact analysis from comparison failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/api/qtest/upload-validate/{comparison_id}")
async def upload_validate_qtest_new(
    comparison_id: int,
    file: UploadFile = File(...)
):
    """
    NEW endpoint for QTest upload with validation and Azure Blob storage
    Completely independent implementation - no reuse of existing code
    """
    try:
        logger.info(f"NEW QTest upload for comparison {comparison_id}: {file.filename}")
        
        # Check Azure configuration before initializing service
        azure_storage_conn = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not azure_storage_conn:
            logger.error("Azure Storage connection string not configured")
            return {
                "success": False,
                "comparison_id": comparison_id,
                "validation": {
                    "valid": False,
                    "errors": ["Azure Storage connection not configured. Please check AZURE_STORAGE_CONNECTION_STRING environment variable."],
                    "warnings": []
                },
                "blob_url": None,
                "comparison_updated": False,
                "error": "Azure Storage connection not configured"
            }
        
        # Initialize the new QTest Azure service
        qtest_service = QTestAzureService()
        
        # Read file content
        file_content = await file.read()
        
        # Process the upload (validate, upload to blob, update database)
        result = qtest_service.process_qtest_upload(
            file_content=file_content,
            filename=file.filename,
            comparison_id=comparison_id
        )
        
        # Return comprehensive response
        return {
            "success": result["success"],
            "comparison_id": comparison_id,
            "validation": result["validation"],
            "blob_url": result["blob_url"],
            "comparison_updated": result["database_updated"],
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"NEW QTest upload failed: {e}")
        
        # Return structured error response instead of HTTP exception
        return {
            "success": False,
            "comparison_id": comparison_id,
            "validation": {
                "valid": False,
                "errors": [f"Upload failed: {str(e)}"],
                "warnings": []
            },
            "blob_url": None,
            "comparison_updated": False,
            "error": str(e)
        }


@app.post("/api/generate/test-steps-from-comparison", response_model=TestStepGenerationResponse)
async def generate_test_steps_from_comparison(
    comparison_id: int = Query(...),
    generation_mode: str = Query(...),
    tracking_service: VersionTrackingService = Depends(get_version_tracking_service),
    blob_service: AzureBlobService = Depends(get_azure_blob_service),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    test_step_service: TestStepService = Depends(get_test_step_service),
    report_service: ReportService = Depends(get_report_service)
):
    """Generate test steps using a comparison from database and QTest from Azure Blob"""
    try:
        logger.info(f"Starting test step generation with comparison {comparison_id}, mode: {generation_mode}")
        
        # Get comparison details from database
        comparison = tracking_service.get_comparison_details(comparison_id)
        if not comparison:
            raise HTTPException(
                status_code=404,
                detail=f"Comparison {comparison_id} not found"
            )
        
        # Fetch JSON from Azure Blob
        json_url = comparison.get('json_report_url')
        local_path = comparison.get('local_json_path')
        
        if not json_url:
            raise HTTPException(
                status_code=400,
                detail="Comparison does not have a JSON report URL"
            )
        
        logger.info("Fetching comparison JSON from Azure Blob for test step generation")
        json_content = blob_service.fetch_comparison_json(json_url, local_path)
        
        # Validate JSON structure
        if not blob_service.validate_json_structure(json_content):
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON structure in comparison"
            )
        
        # Create temporary STTM JSON file from fetched content
        import json
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_sttm:
            json.dump(json_content, temp_sttm)
            temp_sttm_path = temp_sttm.name
        
        try:
            # Copy the JSON to input_files/sttm temporarily
            sttm_dir = Path(__file__).parent.parent / "input_files" / "sttm"
            sttm_dir.mkdir(parents=True, exist_ok=True)
            
            temp_sttm_name = f"comparison_{comparison_id}_temp.json"
            sttm_file_path = sttm_dir / temp_sttm_name
            
            with open(sttm_file_path, 'w') as f:
                json.dump(json_content, f)
            
            # Get QTest file from Azure Blob Storage
            qtest_reader = QTestBlobReaderService()
            qtest_success, qtest_temp_path, qtest_error = qtest_reader.get_qtest_from_comparison(comparison_id)
            
            if not qtest_success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Failed to get QTest file: {qtest_error}"
                )
            
            # Get just the filename from the temp path for the existing logic
            qtest_filename = Path(qtest_temp_path).name
            
            # First run impact analysis to get the data needed for test step generation
            analysis_result = analysis_service.run_impact_analysis(
                sttm_file=temp_sttm_name,
                qtest_file=qtest_filename,
                config=None,
                include_html_in_response=False  # We only need the data structures
            )
            
            # Create analyzers using the same pattern as the working /api/generate/test-steps endpoint
            from models.impact_models import ImpactAnalysisConfig
            from analyzers.impact_analyzer import ImpactAnalyzer
            from parsers.qtest_parser import QTestParser
            
            # Use default configuration
            analysis_config = ImpactAnalysisConfig()
            
            # Get file paths using file service
            from api.services.file_service import FileService
            file_service = FileService()
            sttm_path = str(sttm_file_path)
            qtest_path_str = qtest_temp_path  # Use the temp path directly from Azure
            
            # Parse documents and run analysis to get objects (same as working endpoint)
            analyzer = ImpactAnalyzer(analysis_config, logger)
            impact_report = analyzer.analyze_impact(sttm_path, qtest_path_str)
            
            # Parse qtest document separately to get test cases  
            qtest_parser = QTestParser(logger)
            qtest_document = qtest_parser.parse_file(qtest_path_str)
            test_cases = qtest_document.test_cases
            
            # Generate test steps using the exact same call as working endpoint
            logger.info(f"Generating {generation_mode} test steps")
            
            result = test_step_service.generate_test_steps(
                impact_report=impact_report,
                test_cases=test_cases,
                generation_mode=generation_mode
            )
            
            # STAGE 2: Generate files directly to blob storage
            import os
            import tempfile
            from api.services.output_blob_service import OutputBlobService
            output_blob_service = OutputBlobService()
            
            # Create temporary files for processing
            temp_json_path = None
            temp_excel_path = None
            
            try:
                # Save JSON report temporarily if service is available
                report_id = None
                try:
                    report_id = report_service.save_report(
                        result,
                        "test_steps",
                        f"comparison_{comparison_id}_{generation_mode}"
                    )
                    logger.info(f"Test step report saved with ID: {report_id}")
                    
                    # Create temporary JSON file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_json:
                        import json
                        json.dump(result, temp_json, indent=2)
                        temp_json_path = temp_json.name
                        
                except Exception as e:
                    logger.warning(f"Failed to save test step report to database: {e}")
                
                # Generate Excel file temporarily
                saved_excel_path = test_step_service.save_generated_steps(
                    result, 
                    qtest_file=qtest_path_str,
                    filename=f"temp_comparison_{comparison_id}_{generation_mode}"
                )
                
                # Create temporary Excel file with the generated content
                if saved_excel_path and os.path.exists(saved_excel_path):
                    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_excel:
                        temp_excel_path = temp_excel.name
                    
                    # Copy the generated Excel to our temp file location
                    import shutil
                    shutil.copy2(saved_excel_path, temp_excel_path)
                    # Clean up the generated file from output_files
                    os.unlink(saved_excel_path)
                    logger.info("Temporary Excel file created for blob upload")
                else:
                    logger.warning("Excel file generation failed")
                    temp_excel_path = None
                
                # Upload to blob storage
                blob_urls = output_blob_service.upload_test_step_outputs(
                    comparison_id=comparison_id,
                    generation_mode=generation_mode,
                    json_file_path=temp_json_path if temp_json_path else None,
                    excel_file_path=temp_excel_path if temp_excel_path else None
                )
                
                # Update database with blob URLs
                if generation_mode == 'delta':
                    tracking_service.update_delta_outputs(
                        comparison_id=comparison_id,
                        json_url=blob_urls.get('json_url'),
                        excel_url=blob_urls.get('excel_url')
                    )
                    logger.info(f"Updated delta blob URLs for comparison {comparison_id}")
                else:  # inplace/in_place/in-place
                    tracking_service.update_inplace_outputs(
                        comparison_id=comparison_id,
                        json_url=blob_urls.get('json_url'),
                        excel_url=blob_urls.get('excel_url')
                    )
                    logger.info(f"Updated inplace blob URLs for comparison {comparison_id}")
                
                # Add blob URLs to result instead of local paths
                result['blob_urls'] = blob_urls
                
            finally:
                # Clean up temporary files
                if temp_json_path and os.path.exists(temp_json_path):
                    os.unlink(temp_json_path)
                if temp_excel_path and os.path.exists(temp_excel_path):
                    os.unlink(temp_excel_path)
            
            # Add comparison info and file info to result
            result['comparison_info'] = {
                'comparison_id': comparison_id,
                'comparison_title': comparison.get('comparison_title'),
                'file_name': comparison.get('file_friendly_name')
            }
            
            # STAGE 2: Add report ID but no local file paths
            if report_id:
                result['report_id'] = report_id
            
            return TestStepGenerationResponse(**result)
            
        finally:
            # Cleanup temporary files
            if os.path.exists(temp_sttm_path):
                os.unlink(temp_sttm_path)
            if sttm_file_path.exists():
                sttm_file_path.unlink()
            # Cleanup QTest temp file from Azure
            if 'qtest_temp_path' in locals() and qtest_temp_path:
                qtest_reader.cleanup_temp_file(qtest_temp_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test step generation from comparison failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Test step generation failed: {str(e)}"
        )


# ============================
# BLOB FILE SERVING ENDPOINTS
# ============================

@app.get("/api/test-steps/{comparison_id}/{generation_mode}/excel")
async def serve_test_step_excel(
    comparison_id: int,
    generation_mode: str,
    tracking_service: VersionTrackingService = Depends(get_version_tracking_service)
):
    """Serve test step Excel file from blob storage with authentication"""
    try:
        logger.info(f"Serving test step Excel for comparison {comparison_id}, mode: {generation_mode}")
        
        # Convert URL parameter to database format
        db_mode = generation_mode.replace('-', '')  # "in-place" -> "inplace"
        
        # Get blob URLs from database
        urls = tracking_service.get_output_urls(comparison_id, db_mode)
        if not urls or not urls.get('excel_url'):
            raise HTTPException(
                status_code=404,
                detail=f"Excel file not found for comparison {comparison_id} ({generation_mode} mode)"
            )
        
        # Use OutputBlobService to fetch the file
        from api.services.output_blob_service import OutputBlobService
        blob_service = OutputBlobService()
        
        # Extract blob name from URL
        excel_url = urls['excel_url']
        blob_name = '/'.join(excel_url.split('/')[-3:])  # comparison_id/mode/filename
        
        # Download file content
        file_content = blob_service.download_file(blob_name)
        if not file_content:
            raise HTTPException(
                status_code=404,
                detail="File not found in blob storage"
            )
        
        # Generate filename
        filename = f"test_steps_{generation_mode}_{comparison_id}.xlsx"
        
        return Response(
            content=file_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving Excel file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve Excel file: {str(e)}"
        )


@app.get("/api/test-steps/{comparison_id}/{generation_mode}/json")
async def serve_test_step_json(
    comparison_id: int,
    generation_mode: str,
    tracking_service: VersionTrackingService = Depends(get_version_tracking_service)
):
    """Serve test step JSON file from blob storage with authentication"""
    try:
        logger.info(f"Serving test step JSON for comparison {comparison_id}, mode: {generation_mode}")
        
        # Convert URL parameter to database format
        db_mode = generation_mode.replace('-', '')  # "in-place" -> "inplace"
        
        # Get blob URLs from database
        urls = tracking_service.get_output_urls(comparison_id, db_mode)
        if not urls or not urls.get('json_url'):
            raise HTTPException(
                status_code=404,
                detail=f"JSON file not found for comparison {comparison_id} ({generation_mode} mode)"
            )
        
        # Use OutputBlobService to fetch the file
        from api.services.output_blob_service import OutputBlobService
        blob_service = OutputBlobService()
        
        # Extract blob name from URL
        json_url = urls['json_url']
        blob_name = '/'.join(json_url.split('/')[-3:])  # comparison_id/mode/filename
        
        # Download file content
        file_content = blob_service.download_file(blob_name)
        if not file_content:
            raise HTTPException(
                status_code=404,
                detail="File not found in blob storage"
            )
        
        # Generate filename
        filename = f"test_steps_{generation_mode}_{comparison_id}.json"
        
        return Response(
            content=file_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving JSON file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve JSON file: {str(e)}"
        )


# ============================
# IMPACT ANALYSIS REPORT ENDPOINTS
# ============================

@app.get("/api/impact-reports/{comparison_id}/html")
async def serve_impact_html_report(
    comparison_id: int,
    tracking_service: VersionTrackingService = Depends(get_version_tracking_service)
):
    """
    Serve impact analysis HTML report from Azure Blob Storage
    """
    try:
        logger.info(f"Serving impact analysis HTML report for comparison {comparison_id}")
        
        # Get blob URLs from database
        blob_urls = tracking_service.get_impact_analysis_urls(comparison_id)
        html_blob_url = blob_urls.get('html_url')
        
        if not html_blob_url:
            raise HTTPException(
                status_code=404,
                detail=f"No impact analysis HTML report found for comparison {comparison_id}"
            )
        
        # Download from blob storage
        from api.services.output_blob_service import OutputBlobService
        output_blob_service = OutputBlobService()
        
        file_content = output_blob_service.download_impact_analysis_report(html_blob_url, 'html')
        
        if not file_content:
            raise HTTPException(
                status_code=404,
                detail="HTML report not found in blob storage"
            )
        
        return Response(
            content=file_content,
            media_type="text/html; charset=utf-8"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving impact analysis HTML report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve HTML report: {str(e)}"
        )


@app.get("/api/impact-reports/{comparison_id}/json")
async def serve_impact_json_report(
    comparison_id: int,
    tracking_service: VersionTrackingService = Depends(get_version_tracking_service)
):
    """
    Serve impact analysis JSON report from Azure Blob Storage
    """
    try:
        logger.info(f"Serving impact analysis JSON report for comparison {comparison_id}")
        
        # Get blob URLs from database
        blob_urls = tracking_service.get_impact_analysis_urls(comparison_id)
        json_blob_url = blob_urls.get('json_url')
        
        if not json_blob_url:
            raise HTTPException(
                status_code=404,
                detail=f"No impact analysis JSON report found for comparison {comparison_id}"
            )
        
        # Download from blob storage
        from api.services.output_blob_service import OutputBlobService
        output_blob_service = OutputBlobService()
        
        file_content = output_blob_service.download_impact_analysis_report(json_blob_url, 'json')
        
        if not file_content:
            raise HTTPException(
                status_code=404,
                detail="JSON report not found in blob storage"
            )
        
        # Generate filename with timestamp
        timestamp = blob_urls.get('timestamp', 'unknown')
        if timestamp and timestamp != 'unknown':
            timestamp_str = timestamp.replace(':', '').replace('-', '').replace('T', '_')[:15]  # Format: YYYYMMDD_HHMMSS
        else:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        filename = f"impact_analysis_{comparison_id}_{timestamp_str}.json"
        
        return Response(
            content=file_content,
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving impact analysis JSON report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to serve JSON report: {str(e)}"
        )


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Global HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc, request.url.path)
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Global general exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=create_error_response(exc, request.url.path)
    )


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv('API_HOST', '127.0.0.1')
    port = int(os.getenv('API_PORT', '8004'))
    reload = os.getenv('API_RELOAD', 'True').lower() == 'true'
    log_level = os.getenv('API_LOG_LEVEL', 'info')
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )
"""
FastAPI Main Application - STTM Impact Analysis API
Stage 1: Foundation & File Management
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from datetime import datetime
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to import existing modules
sys.path.append(str(Path(__file__).parent.parent))

# Import API components
from api.services.file_service import FileService
from api.services.analysis_service import AnalysisService
from api.services.test_step_service import TestStepService
from api.services.report_service import ReportService
from api.services.config_service import ConfigService
from api.middleware.logging import EnhancedRequestLoggingMiddleware
from api.models.api_models import (
    HealthResponse, FileListResponse, ValidationRequest, ValidationResponse,
    CombinedValidationResponse, ErrorResponse, FileInfo, ImpactAnalysisRequest,
    TestStepGenerationRequest, TestStepGenerationResponse, ReportListResponse,
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
response_optimizer = ResponseOptimizer(logger)

# Add request logging middleware
logging_middleware = EnhancedRequestLoggingMiddleware(app=None, logger=logger)
app.add_middleware(EnhancedRequestLoggingMiddleware)


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


@app.get("/", response_model=HealthResponse)
async def health_check():
    """API health check and information endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0-stage3",
        environment="development"
    )


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
            "environment": "development",
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
            "environment": "development",
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


@app.post("/api/analyze-impact")
async def analyze_impact(
    request: ImpactAnalysisRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    optimize_response: bool = True
):
    """Run complete impact analysis between STTM and QTEST files"""
    try:
        logger.info(f"Starting impact analysis: {request.sttm_file} + {request.qtest_file}")
        
        # Run analysis using existing CLI logic
        result = analysis_service.run_impact_analysis(
            sttm_file=request.sttm_file,
            qtest_file=request.qtest_file,
            config=request.config.dict() if request.config else None,
            include_html_in_response=request.include_html_in_response
        )
        
        # Optimize response for large reports
        if optimize_response:
            return response_optimizer.optimize_response(result, compression=True)
        else:
            return ImpactAnalysisResponse(**result)
        
    except FileNotFoundError:
        raise  # Re-raise with proper HTTP status
    except ConfigurationError:
        raise  # Re-raise with proper HTTP status  
    except AnalysisError:
        raise  # Re-raise with proper HTTP status
    except Exception as e:
        logger.error(f"Unexpected analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed unexpectedly: {str(e)}"
        )


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

@app.post("/api/generate/test-steps", response_model=TestStepGenerationResponse)
async def generate_test_steps(
    request: TestStepGenerationRequest,
    test_step_service: TestStepService = Depends(get_test_step_service),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    report_service: ReportService = Depends(get_report_service)
):
    """Generate test steps based on STTM impact analysis (Phase 3B functionality)"""
    try:
        logger.info(f"Starting test step generation: {request.sttm_file} + {request.qtest_file}")
        # Force reload
        
        # First run impact analysis to get the data needed for test step generation
        analysis_result = analysis_service.run_impact_analysis(
            sttm_file=request.sttm_file,
            qtest_file=request.qtest_file,
            config=request.config.dict() if request.config else None,
            include_html_in_response=False  # We only need the data structures
        )
        
        # Create a new analyzer to get the required objects directly
        from models.impact_models import ImpactAnalysisConfig
        from analyzers.impact_analyzer import ImpactAnalyzer
        from parsers.qtest_parser import QTestParser
        
        # Get configuration
        if request.config:
            try:
                analysis_config = ImpactAnalysisConfig(**request.config.dict())
            except Exception as e:
                raise TestStepGenerationError(f"Invalid configuration: {str(e)}")
        else:
            analysis_config = ImpactAnalysisConfig()
            
        # Get file paths
        sttm_path = analysis_service.file_service.get_sttm_path(request.sttm_file)
        qtest_path = analysis_service.file_service.get_qtest_path(request.qtest_file)
        
        # Parse documents and run analysis to get objects
        analyzer = ImpactAnalyzer(analysis_config, logger)
        impact_report = analyzer.analyze_impact(sttm_path, qtest_path)
        
        # Parse qtest document separately to get test cases  
        qtest_parser = QTestParser(logger)
        qtest_document = qtest_parser.parse_file(qtest_path)
        test_cases = qtest_document.test_cases
        
        # Generate test steps
        generation_result = test_step_service.generate_test_steps(
            impact_report=impact_report,
            test_cases=test_cases,
            generation_mode=request.generation_mode
        )
        
        saved_file_path = None
        report_id = None
        
        # Save to file if requested
        if request.save_to_file:
            saved_file_path = test_step_service.save_generated_steps(
                generation_result, 
                request.custom_filename
            )
            
            # Also save to report service for retrieval via report endpoints
            report_id = report_service.save_report(
                generation_result,
                "test_steps",
                request.custom_filename or f"test_steps_{request.generation_mode}"
            )
        
        # Convert to response model
        response_data = {
            "success": True,
            "generation_mode": generation_result["generation_mode"],
            "summary": generation_result["summary"],
            "metadata": generation_result["metadata"],
            "saved_file_path": saved_file_path,
            "report_id": report_id
        }
        
        if request.generation_mode == "delta":
            response_data["generated_steps"] = generation_result["generated_steps"]
        else:
            response_data["updated_test_cases"] = generation_result["updated_test_cases"]
            response_data["generated_steps"] = generation_result["generated_steps"]
        
        return TestStepGenerationResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Test step generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Test step generation failed: {str(e)}"
        )


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
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8004,
        reload=True,
        log_level="info"
    )
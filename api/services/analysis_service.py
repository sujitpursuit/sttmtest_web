"""
Analysis Service - Wrapper for STTM Impact Analysis functionality
Integrates existing CLI analysis logic into FastAPI service layer
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import json

# Add parent directory to path to import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import existing CLI components
from analyzers.impact_analyzer import ImpactAnalyzer
from models.impact_models import ImpactAnalysisConfig
from utils.report_formatters import generate_html_report, generate_detailed_json_report
from utils.logger import get_logger

# Import API components
from api.services.file_service import FileService
from api.utils.exceptions import AnalysisError, FileNotFoundError, ConfigurationError


class AnalysisService:
    """Service for running STTM impact analysis through API"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.file_service = FileService()
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_impact_analysis(
        self,
        sttm_file: str,
        qtest_file: str,
        config: Optional[Dict[str, Any]] = None,
        include_html_in_response: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete impact analysis using existing CLI logic
        Returns comprehensive analysis results for API response
        """
        start_time = datetime.now()
        self.logger.info(f"Starting impact analysis: {sttm_file} + {qtest_file}")
        
        try:
            # Get full file paths
            sttm_path = self.file_service.get_sttm_path(sttm_file)
            qtest_path = self.file_service.get_qtest_path(qtest_file)
            
            # Create analysis configuration
            if config:
                try:
                    analysis_config = ImpactAnalysisConfig(**config)
                    self.logger.info("Using custom analysis configuration")
                except Exception as e:
                    raise ConfigurationError(f"Invalid configuration: {str(e)}")
            else:
                analysis_config = ImpactAnalysisConfig()
                self.logger.info("Using default analysis configuration")
            
            # Parse documents first to get the original objects
            from parsers.sttm_parser import STTMParser
            from parsers.qtest_parser import QTestParser
            
            sttm_parser = STTMParser(self.logger)
            qtest_parser = QTestParser(self.logger)
            
            sttm_document = sttm_parser.parse_file(sttm_path)
            qtest_document = qtest_parser.parse_file(qtest_path)
            
            # Run impact analysis using existing CLI logic
            analyzer = ImpactAnalyzer(analysis_config, self.logger)
            report = analyzer.analyze_impact(sttm_path, qtest_path)
            
            # Generate HTML and JSON reports
            html_content = generate_html_report(report)
            json_data = report.to_dict()
            
            # Always save reports to files and generate file links
            files_generated = self._save_report_files(report, sttm_file, html_content, json_data)
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Create comprehensive response
            analysis_result = {
                "success": True,
                "summary": {
                    "total_test_cases": report.total_test_cases_analyzed,
                    "total_sttm_changes": report.total_sttm_changes,
                    "critical_impacts": report.total_critical_impact,
                    "high_impacts": report.total_high_impact,
                    "medium_impacts": report.total_medium_impact,
                    "low_impacts": report.total_low_impact,
                    "priority_impacts": report.total_critical_impact + report.total_high_impact,
                    "analysis_timestamp": start_time.isoformat()
                },
                "json_report": json_data,
                "report_links": {
                    "html_url": f"/reports/{Path(files_generated.get('html_report', '')).name}" if files_generated.get('html_report') else None,
                    "json_url": f"/reports/{Path(files_generated.get('json_report', '')).name}" if files_generated.get('json_report') else None,
                    "html_file": files_generated.get('html_report'),
                    "json_file": files_generated.get('json_report')
                },
                "analysis_metadata": {
                    "sttm_file": sttm_file,
                    "qtest_file": qtest_file,
                    "sttm_tabs_analyzed": report.total_sttm_tabs_analyzed,
                    "analysis_timestamp": report.analysis_timestamp,
                    "analyzer_version": "2.0",
                    "config_used": self._config_to_dict(analysis_config)
                },
                "processing_time_seconds": processing_time
            }
            
            # Optionally include HTML in response (for backward compatibility)
            if include_html_in_response:
                analysis_result["html_report"] = html_content
            
            self.logger.info(
                f"Analysis completed in {processing_time:.2f} seconds. "
                f"Results: Critical={report.total_critical_impact}, "
                f"High={report.total_high_impact}, Medium={report.total_medium_impact}, "
                f"Low={report.total_low_impact}"
            )
            
            return analysis_result
            
        except FileNotFoundError as e:
            self.logger.error(f"File not found: {e}")
            raise
        except ConfigurationError as e:
            self.logger.error(f"Configuration error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            raise AnalysisError(f"Impact analysis failed: {str(e)}")
    
    def _save_report_files(
        self,
        report,
        sttm_file: str,
        html_content: str,
        json_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Save HTML and JSON reports to files"""
        try:
            # Create timestamped filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sttm_name = Path(sttm_file).stem
            
            html_file = self.reports_dir / f"impact_analysis_{sttm_name}_{timestamp}.html"
            json_file = self.reports_dir / f"impact_analysis_{sttm_name}_{timestamp}.json"
            
            # Save HTML report
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Save JSON report
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Reports saved: {html_file} and {json_file}")
            
            return {
                "html_report": str(html_file),
                "json_report": str(json_file)
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to save report files: {e}")
            return {}
    
    def validate_files_for_analysis(self, sttm_file: str, qtest_file: str) -> Dict[str, Any]:
        """Validate both files are ready for analysis"""
        try:
            # Validate STTM file
            sttm_validation = self.file_service.validate_sttm_file(sttm_file)
            if not sttm_validation["valid"]:
                return {
                    "compatible": False,
                    "errors": sttm_validation["errors"],
                    "sttm_valid": False,
                    "qtest_valid": False
                }
            
            # Validate QTEST file
            qtest_validation = self.file_service.validate_qtest_file(qtest_file)
            if not qtest_validation["valid"]:
                return {
                    "compatible": False,
                    "errors": qtest_validation["errors"],
                    "sttm_valid": True,
                    "qtest_valid": False
                }
            
            # Both files are valid
            return {
                "compatible": True,
                "errors": [],
                "sttm_valid": True,
                "qtest_valid": True,
                "estimated_processing_time": "2-5 minutes",
                "sttm_structure": sttm_validation.get("structure", {}),
                "qtest_structure": qtest_validation.get("structure", {})
            }
            
        except Exception as e:
            return {
                "compatible": False,
                "errors": [str(e)],
                "sttm_valid": False,
                "qtest_valid": False
            }
    
    def get_available_config_presets(self) -> Dict[str, Any]:
        """Get available analysis configuration presets"""
        presets = {
            "balanced": {
                "name": "Balanced",
                "description": "Good balance of sensitivity and accuracy for most scenarios",
                "config": {
                    "critical_threshold": 15,
                    "high_threshold": 10,
                    "medium_threshold": 5,
                    "low_threshold": 1,
                    "tab_name_match_points": 8,
                    "deleted_field_points": 10,
                    "modified_field_points": 6,
                    "added_field_points": 2
                },
                "recommended_for": ["General analysis", "Mixed change types", "Standard workflows"]
            },
            "conservative": {
                "name": "Conservative",
                "description": "Higher thresholds, focuses on clear and obvious impacts only",
                "config": {
                    "critical_threshold": 20,
                    "high_threshold": 15,
                    "medium_threshold": 8,
                    "low_threshold": 3,
                    "tab_name_match_points": 10,
                    "deleted_field_points": 12,
                    "modified_field_points": 8,
                    "added_field_points": 3
                },
                "recommended_for": ["High-stakes changes", "Production environments", "Risk-averse teams"]
            },
            "aggressive": {
                "name": "Aggressive",
                "description": "Lower thresholds, catches potential impacts early",
                "config": {
                    "critical_threshold": 10,
                    "high_threshold": 6,
                    "medium_threshold": 3,
                    "low_threshold": 1,
                    "tab_name_match_points": 6,
                    "deleted_field_points": 8,
                    "modified_field_points": 5,
                    "added_field_points": 2
                },
                "recommended_for": ["Development phases", "Thorough analysis", "Change detection"]
            },
            "strict": {
                "name": "Strict",
                "description": "Very high standards, only flags definitive impacts",
                "config": {
                    "critical_threshold": 25,
                    "high_threshold": 18,
                    "medium_threshold": 12,
                    "low_threshold": 6,
                    "tab_name_match_points": 12,
                    "deleted_field_points": 15,
                    "modified_field_points": 10,
                    "added_field_points": 4
                },
                "recommended_for": ["Final validation", "Critical systems", "Regulatory compliance"]
            }
        }
        
        return {
            "presets": presets,
            "default": "balanced",
            "total_presets": len(presets)
        }
    
    def _config_to_dict(self, config: ImpactAnalysisConfig) -> Dict[str, Any]:
        """Convert configuration to dictionary for response"""
        return {
            "critical_threshold": config.critical_threshold,
            "high_threshold": config.high_threshold,
            "medium_threshold": config.medium_threshold,
            "low_threshold": config.low_threshold,
            "tab_name_match_points": config.tab_name_match_points,
            "deleted_field_points": config.deleted_field_points,
            "modified_field_points": config.modified_field_points,
            "added_field_points": config.added_field_points,
            "exact_tab_match_points": config.exact_tab_match_points,
            "partial_tab_match_points": config.partial_tab_match_points,
            "field_name_match_points": config.field_name_match_points,
            "sample_data_match_points": config.sample_data_match_points
        }
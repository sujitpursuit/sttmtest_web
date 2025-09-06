"""
Report Persistence Service for FastAPI

Handles saving, retrieving, and managing analysis reports and generated test steps.
All reports are stored in the output_files directory with unique identifiers.
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import shutil
import logging

from api.utils.exceptions import ReportNotFoundError, ReportStorageError


class ReportService:
    """Service for managing report persistence and retrieval"""
    
    def __init__(self, output_dir: str = "output_files", logger: Optional[logging.Logger] = None):
        self.output_dir = output_dir
        self.logger = logger or logging.getLogger(__name__)
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """Ensure output directory exists"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.logger.debug(f"Output directory ensured: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create output directory: {str(e)}")
            raise ReportStorageError(f"Failed to create output directory: {str(e)}")
    
    def save_report(self, report_data: Dict[str, Any], report_type: str, 
                   custom_filename: Optional[str] = None) -> str:
        """
        Save a report to the output directory
        
        Args:
            report_data: Report data to save
            report_type: Type of report (e.g., 'analysis', 'test_steps', 'config')
            custom_filename: Optional custom filename (without extension)
            
        Returns:
            Report ID (filename without extension)
        """
        try:
            # Generate unique report ID
            if custom_filename:
                report_id = custom_filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_id = str(uuid.uuid4())[:8]
                report_id = f"{report_type}_{timestamp}_{unique_id}"
            
            # Add metadata to report
            enhanced_report_data = {
                "report_metadata": {
                    "report_id": report_id,
                    "report_type": report_type,
                    "created_timestamp": datetime.now().isoformat(),
                    "file_size_bytes": 0,  # Will be calculated after saving
                },
                "report_data": report_data
            }
            
            # Save to file
            file_path = os.path.join(self.output_dir, f"{report_id}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_report_data, f, indent=2, ensure_ascii=False)
            
            # Update file size in metadata
            file_size = os.path.getsize(file_path)
            enhanced_report_data["report_metadata"]["file_size_bytes"] = file_size
            
            # Re-save with updated metadata
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {report_type} report: {report_id} ({file_size} bytes)")
            return report_id
            
        except Exception as e:
            self.logger.error(f"Failed to save report: {str(e)}", exc_info=True)
            raise ReportStorageError(f"Failed to save report: {str(e)}")
    
    def get_report(self, report_id: str) -> Dict[str, Any]:
        """
        Retrieve a report by ID
        
        Args:
            report_id: Report identifier
            
        Returns:
            Report data dictionary
        """
        try:
            file_path = os.path.join(self.output_dir, f"{report_id}.json")
            
            if not os.path.exists(file_path):
                raise ReportNotFoundError(f"Report not found: {report_id}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            self.logger.debug(f"Retrieved report: {report_id}")
            return report_data
            
        except ReportNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to retrieve report {report_id}: {str(e)}")
            raise ReportStorageError(f"Failed to retrieve report: {str(e)}")
    
    def get_report_data_only(self, report_id: str) -> Dict[str, Any]:
        """Get only the report data without metadata"""
        full_report = self.get_report(report_id)
        return full_report.get("report_data", {})
    
    def get_report_metadata(self, report_id: str) -> Dict[str, Any]:
        """Get only the report metadata"""
        full_report = self.get_report(report_id)
        return full_report.get("report_metadata", {})
    
    def list_reports(self, report_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available reports
        
        Args:
            report_type: Optional filter by report type
            
        Returns:
            List of report summaries
        """
        try:
            reports = []
            
            if not os.path.exists(self.output_dir):
                return reports
            
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.json'):
                    report_id = filename[:-5]  # Remove .json extension
                    
                    try:
                        # Get basic info without loading full report
                        file_path = os.path.join(self.output_dir, filename)
                        file_size = os.path.getsize(file_path)
                        modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        # Try to get metadata from file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            metadata = data.get("report_metadata", {})
                        
                        report_info = {
                            "report_id": report_id,
                            "report_type": metadata.get("report_type", "unknown"),
                            "created_timestamp": metadata.get("created_timestamp", modified_time.isoformat()),
                            "file_size_bytes": file_size,
                            "last_modified": modified_time.isoformat()
                        }
                        
                        # Filter by type if specified
                        if report_type and report_info["report_type"] != report_type:
                            continue
                        
                        reports.append(report_info)
                        
                    except Exception as e:
                        self.logger.warning(f"Could not read report metadata for {filename}: {str(e)}")
                        continue
            
            # Sort by creation time (newest first)
            reports.sort(key=lambda x: x.get("created_timestamp", ""), reverse=True)
            
            self.logger.debug(f"Found {len(reports)} reports" + (f" of type '{report_type}'" if report_type else ""))
            return reports
            
        except Exception as e:
            self.logger.error(f"Failed to list reports: {str(e)}")
            raise ReportStorageError(f"Failed to list reports: {str(e)}")
    
    def delete_report(self, report_id: str) -> bool:
        """
        Delete a report
        
        Args:
            report_id: Report identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            file_path = os.path.join(self.output_dir, f"{report_id}.json")
            
            if not os.path.exists(file_path):
                raise ReportNotFoundError(f"Report not found: {report_id}")
            
            os.remove(file_path)
            self.logger.info(f"Deleted report: {report_id}")
            return True
            
        except ReportNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete report {report_id}: {str(e)}")
            raise ReportStorageError(f"Failed to delete report: {str(e)}")
    
    def cleanup_old_reports(self, days_old: int = 30, report_type: Optional[str] = None) -> int:
        """
        Clean up old reports
        
        Args:
            days_old: Delete reports older than this many days
            report_type: Optional filter by report type
            
        Returns:
            Number of reports deleted
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_count = 0
            
            reports = self.list_reports(report_type)
            
            for report_info in reports:
                report_id = report_info["report_id"]
                file_path = os.path.join(self.output_dir, f"{report_id}.json")
                
                if os.path.exists(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_time:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                            self.logger.info(f"Cleaned up old report: {report_id}")
                        except Exception as e:
                            self.logger.warning(f"Could not delete old report {report_id}: {str(e)}")
            
            self.logger.info(f"Cleaned up {deleted_count} old reports (older than {days_old} days)")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old reports: {str(e)}")
            raise ReportStorageError(f"Failed to cleanup old reports: {str(e)}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for reports"""
        try:
            if not os.path.exists(self.output_dir):
                return {
                    "total_reports": 0,
                    "total_size_bytes": 0,
                    "reports_by_type": {},
                    "oldest_report": None,
                    "newest_report": None
                }
            
            reports = self.list_reports()
            
            total_size = 0
            reports_by_type = {}
            oldest_date = None
            newest_date = None
            
            for report_info in reports:
                # Size
                total_size += report_info.get("file_size_bytes", 0)
                
                # Type count
                report_type = report_info.get("report_type", "unknown")
                reports_by_type[report_type] = reports_by_type.get(report_type, 0) + 1
                
                # Date tracking
                created_timestamp = report_info.get("created_timestamp")
                if created_timestamp:
                    if oldest_date is None or created_timestamp < oldest_date:
                        oldest_date = created_timestamp
                    if newest_date is None or created_timestamp > newest_date:
                        newest_date = created_timestamp
            
            return {
                "total_reports": len(reports),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "reports_by_type": reports_by_type,
                "oldest_report": oldest_date,
                "newest_report": newest_date,
                "output_directory": self.output_dir
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {str(e)}")
            return {"error": str(e)}
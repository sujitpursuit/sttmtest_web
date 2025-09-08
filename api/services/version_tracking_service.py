"""
Version Tracking Service - Database operations for tracked files and comparisons
Handles interaction with Azure SQL Database for version tracking functionality
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class VersionTrackingService:
    """Service for managing tracked files and version comparisons from database"""
    
    def __init__(self):
        """Initialize database connection"""
        self.connection_string = os.getenv('AZURE_SQL_CONNECTION_STRING')
        if not self.connection_string:
            logger.warning("Azure SQL connection string not found in environment variables")
            self.connection_string = None
    
    def _get_connection(self):
        """Create and return a database connection"""
        if not self.connection_string:
            raise ValueError("Database connection string not configured")
        
        try:
            conn = pyodbc.connect(self.connection_string)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def get_tracked_files(self) -> List[Dict[str, Any]]:
        """
        Get all active tracked files from the database
        
        Returns:
            List of tracked files with their details
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT 
                    id,
                    sharepoint_url,
                    file_name,
                    friendly_name,
                    drive_id,
                    item_id,
                    created_at,
                    last_checked_at
                FROM tracked_files
                WHERE is_active = 1
                ORDER BY friendly_name
                """
                
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                
                files = []
                for row in cursor.fetchall():
                    file_dict = dict(zip(columns, row))
                    # Convert datetime objects to ISO format strings
                    for key in ['created_at', 'last_checked_at']:
                        if file_dict.get(key) and isinstance(file_dict[key], datetime):
                            file_dict[key] = file_dict[key].isoformat()
                    files.append(file_dict)
                
                logger.info(f"Retrieved {len(files)} tracked files")
                return files
                
        except Exception as e:
            logger.error(f"Error fetching tracked files: {e}")
            raise
    
    def get_file_comparisons(self, file_id: int) -> List[Dict[str, Any]]:
        """
        Get all completed comparisons for a specific tracked file
        Includes version details from file_versions table
        
        Args:
            file_id: ID of the tracked file
            
        Returns:
            List of comparisons with version details
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT 
                    vc.id as comparison_id,
                    vc.comparison_title,
                    vc.comparison_status,
                    vc.html_report_url,
                    vc.json_report_url,
                    vc.local_html_path,
                    vc.local_json_path,
                    vc.total_changes,
                    vc.added_mappings,
                    vc.modified_mappings,
                    vc.deleted_mappings,
                    vc.tabs_compared,
                    vc.comparison_duration_seconds,
                    vc.comparison_taken_at,
                    vc.created_at,
                    vc.user_notes,
                    -- From version details
                    fv1.id as from_version_id,
                    fv1.sequence_number as from_sequence,
                    fv1.sharepoint_version_id as from_sharepoint_version,
                    fv1.modified_datetime as from_modified,
                    fv1.file_size_bytes as from_size,
                    -- To version details
                    fv2.id as to_version_id,
                    fv2.sequence_number as to_sequence,
                    fv2.sharepoint_version_id as to_sharepoint_version,
                    fv2.modified_datetime as to_modified,
                    fv2.file_size_bytes as to_size
                FROM version_comparisons vc
                INNER JOIN file_versions fv1 ON vc.file1_version_id = fv1.id
                INNER JOIN file_versions fv2 ON vc.file2_version_id = fv2.id
                WHERE fv1.file_id = ? 
                    AND vc.comparison_status = 'completed'
                    AND vc.is_archived = 0
                ORDER BY vc.created_at DESC
                """
                
                cursor.execute(query, file_id)
                columns = [column[0] for column in cursor.description]
                
                comparisons = []
                for row in cursor.fetchall():
                    comp_dict = dict(zip(columns, row))
                    
                    # Convert datetime objects to ISO format strings
                    datetime_fields = ['comparison_taken_at', 'created_at', 
                                      'from_modified', 'to_modified']
                    for key in datetime_fields:
                        if comp_dict.get(key) and isinstance(comp_dict[key], datetime):
                            comp_dict[key] = comp_dict[key].isoformat()
                    
                    # Convert numeric fields to proper types
                    numeric_fields = ['total_changes', 'added_mappings', 
                                     'modified_mappings', 'deleted_mappings', 
                                     'tabs_compared', 'from_size', 'to_size']
                    for key in numeric_fields:
                        if comp_dict.get(key) is not None:
                            comp_dict[key] = int(comp_dict[key])
                    
                    # Format comparison duration
                    if comp_dict.get('comparison_duration_seconds'):
                        comp_dict['comparison_duration_seconds'] = float(
                            comp_dict['comparison_duration_seconds']
                        )
                    
                    comparisons.append(comp_dict)
                
                logger.info(f"Retrieved {len(comparisons)} comparisons for file_id {file_id}")
                return comparisons
                
        except Exception as e:
            logger.error(f"Error fetching comparisons for file {file_id}: {e}")
            raise
    
    def get_comparison_details(self, comparison_id: int) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific comparison including blob URLs
        
        Args:
            comparison_id: ID of the comparison
            
        Returns:
            Comparison details or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT 
                    vc.*,
                    tf.friendly_name as file_friendly_name,
                    tf.file_name
                FROM version_comparisons vc
                INNER JOIN file_versions fv ON vc.file1_version_id = fv.id
                INNER JOIN tracked_files tf ON fv.file_id = tf.id
                WHERE vc.id = ?
                """
                
                cursor.execute(query, comparison_id)
                columns = [column[0] for column in cursor.description]
                
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"Comparison {comparison_id} not found")
                    return None
                
                comp_dict = dict(zip(columns, row))
                
                # Convert datetime objects
                datetime_fields = ['comparison_taken_at', 'created_at']
                for key in datetime_fields:
                    if comp_dict.get(key) and isinstance(comp_dict[key], datetime):
                        comp_dict[key] = comp_dict[key].isoformat()
                
                logger.info(f"Retrieved details for comparison {comparison_id}")
                return comp_dict
                
        except Exception as e:
            logger.error(f"Error fetching comparison {comparison_id}: {e}")
            raise
    
    def update_delta_outputs(self, comparison_id: int, json_url: str = None, excel_url: str = None) -> bool:
        """
        Update delta mode output URLs in database
        
        Args:
            comparison_id: ID of the comparison
            json_url: URL of JSON file in blob storage
            excel_url: URL of Excel file in blob storage
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query based on provided URLs
                updates = []
                params = []
                
                if json_url:
                    updates.append("delta_json_url = ?")
                    params.append(json_url)
                
                if excel_url:
                    updates.append("delta_excel_url = ?")
                    params.append(excel_url)
                
                if updates:
                    updates.append("delta_generated_at = GETDATE()")
                    params.append(comparison_id)
                    
                    query = f"""
                    UPDATE version_comparisons 
                    SET {', '.join(updates)}
                    WHERE id = ?
                    """
                    
                    cursor.execute(query, *params)
                    conn.commit()
                    
                    logger.info(f"Updated delta outputs for comparison {comparison_id}")
                    return cursor.rowcount > 0
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating delta outputs: {e}")
            return False
    
    def update_inplace_outputs(self, comparison_id: int, json_url: str = None, excel_url: str = None) -> bool:
        """
        Update in-place mode output URLs in database
        
        Args:
            comparison_id: ID of the comparison
            json_url: URL of JSON file in blob storage
            excel_url: URL of Excel file in blob storage
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query based on provided URLs
                updates = []
                params = []
                
                if json_url:
                    updates.append("inplace_json_url = ?")
                    params.append(json_url)
                
                if excel_url:
                    updates.append("inplace_excel_url = ?")
                    params.append(excel_url)
                
                if updates:
                    updates.append("inplace_generated_at = GETDATE()")
                    params.append(comparison_id)
                    
                    query = f"""
                    UPDATE version_comparisons 
                    SET {', '.join(updates)}
                    WHERE id = ?
                    """
                    
                    cursor.execute(query, *params)
                    conn.commit()
                    
                    logger.info(f"Updated inplace outputs for comparison {comparison_id}")
                    return cursor.rowcount > 0
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating inplace outputs: {e}")
            return False
    
    def get_output_urls(self, comparison_id: int, generation_mode: str = None) -> Dict:
        """
        Get output URLs for a comparison
        
        Args:
            comparison_id: ID of the comparison
            generation_mode: Optional - 'delta' or 'inplace' to get specific mode
            
        Returns:
            Dictionary with output URLs and timestamps
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if generation_mode == 'delta':
                    query = """
                    SELECT delta_json_url, delta_excel_url, delta_generated_at
                    FROM version_comparisons 
                    WHERE id = ?
                    """
                elif generation_mode == 'inplace':
                    query = """
                    SELECT inplace_json_url, inplace_excel_url, inplace_generated_at
                    FROM version_comparisons 
                    WHERE id = ?
                    """
                else:
                    # Get all outputs
                    query = """
                    SELECT 
                        delta_json_url, delta_excel_url, delta_generated_at,
                        inplace_json_url, inplace_excel_url, inplace_generated_at
                    FROM version_comparisons 
                    WHERE id = ?
                    """
                
                cursor.execute(query, comparison_id)
                result = cursor.fetchone()
                
                if not result:
                    return {}
                
                if generation_mode == 'delta':
                    return {
                        'json_url': result[0],
                        'excel_url': result[1],
                        'generated_at': result[2].isoformat() if result[2] else None
                    }
                elif generation_mode == 'inplace':
                    return {
                        'json_url': result[0],
                        'excel_url': result[1],
                        'generated_at': result[2].isoformat() if result[2] else None
                    }
                else:
                    return {
                        'delta': {
                            'json_url': result[0],
                            'excel_url': result[1],
                            'generated_at': result[2].isoformat() if result[2] else None
                        },
                        'inplace': {
                            'json_url': result[3],
                            'excel_url': result[4],
                            'generated_at': result[5].isoformat() if result[5] else None
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Error getting output URLs: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
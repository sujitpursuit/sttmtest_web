"""
QTest Blob Reader Service - Reusable Azure QTest file operations
Downloads QTest files from Azure Blob Storage for analysis and test generation
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Tuple, Optional
import pyodbc
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class QTestBlobReaderService:
    """Reusable service for reading QTest files from Azure Blob Storage"""
    
    def __init__(self):
        """Initialize Azure Blob and Database connections"""
        self.blob_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.db_connection_string = os.getenv('AZURE_SQL_CONNECTION_STRING')
        self.container_name = "qtest-files"
        
        if not self.blob_connection_string:
            logger.error("Azure Storage connection string not configured")
            raise ValueError("Azure Storage connection string is required")
        
        if not self.db_connection_string:
            logger.error("Azure SQL connection string not configured")
            raise ValueError("Azure SQL connection string is required")
        
        # Initialize blob service client
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.blob_connection_string
        )
        
        logger.info("QTestBlobReaderService initialized successfully")
    
    def get_qtest_from_comparison(self, comparison_id: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Get QTest file for a comparison and create temporary local file
        
        Args:
            comparison_id: ID of the comparison
            
        Returns:
            Tuple of (success, temp_file_path, error_message)
        """
        try:
            logger.info(f"Getting QTest for comparison {comparison_id}")
            
            # Step 1: Get blob URL from database
            blob_url = self._get_qtest_blob_url_from_database(comparison_id)
            if not blob_url:
                return False, None, f"No QTest file found for comparison {comparison_id}"
            
            logger.info(f"Found QTest blob URL: {blob_url[:50]}...")
            
            # Step 2: Download QTest file from Azure Blob
            success, content, error = self._download_qtest_from_blob(blob_url)
            if not success:
                return False, None, f"Failed to download QTest from Azure: {error}"
            
            logger.info(f"Downloaded QTest content: {len(content)} bytes")
            
            # Step 3: Create temporary file in expected location
            temp_file_path = self._create_temp_qtest_file(content, comparison_id)
            if not temp_file_path:
                return False, None, "Failed to create temporary QTest file"
            
            logger.info(f"Created temporary QTest file: {temp_file_path}")
            return True, temp_file_path, None
            
        except Exception as e:
            logger.error(f"Error getting QTest from comparison {comparison_id}: {e}")
            return False, None, str(e)
    
    def _get_qtest_blob_url_from_database(self, comparison_id: int) -> Optional[str]:
        """Get QTest blob URL from version_comparisons table"""
        try:
            with pyodbc.connect(self.db_connection_string) as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT qtest_file 
                FROM version_comparisons 
                WHERE id = ? AND qtest_file IS NOT NULL
                """
                
                cursor.execute(query, comparison_id)
                result = cursor.fetchone()
                
                if result and result.qtest_file:
                    logger.info(f"Found QTest blob URL for comparison {comparison_id}")
                    return result.qtest_file
                else:
                    logger.warning(f"No QTest blob URL found for comparison {comparison_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Database error getting QTest URL: {e}")
            return None
    
    def _download_qtest_from_blob(self, blob_url: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """Download QTest file content from Azure Blob Storage"""
        try:
            logger.info("Downloading QTest from Azure Blob Storage")
            
            # Extract blob name from URL
            # URL format: https://account.blob.core.windows.net/container/blob_name
            blob_name = blob_url.split(f"/{self.container_name}/")[-1]
            
            # Get blob client and download
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Download blob content
            blob_data = blob_client.download_blob()
            content = blob_data.readall()
            
            logger.info(f"Successfully downloaded QTest: {len(content)} bytes")
            return True, content, None
            
        except Exception as e:
            logger.error(f"Failed to download QTest from blob: {e}")
            return False, None, str(e)
    
    def _create_temp_qtest_file(self, content: bytes, comparison_id: int) -> Optional[str]:
        """Create temporary QTest file in the expected input_files/qtest directory"""
        try:
            # Create qtest directory if it doesn't exist
            qtest_dir = Path(__file__).parent.parent.parent / "input_files" / "qtest"
            qtest_dir.mkdir(parents=True, exist_ok=True)
            
            # Create temp filename that won't conflict with uploaded files
            temp_filename = f"azure_comparison_{comparison_id}_temp.xlsx"
            temp_file_path = qtest_dir / temp_filename
            
            # Write content to temp file
            with open(temp_file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Created temp QTest file: {temp_file_path}")
            return str(temp_file_path)
            
        except Exception as e:
            logger.error(f"Failed to create temp QTest file: {e}")
            return None
    
    def cleanup_temp_file(self, temp_file_path: str) -> bool:
        """Clean up temporary QTest file"""
        try:
            if temp_file_path and Path(temp_file_path).exists():
                Path(temp_file_path).unlink()
                logger.info(f"Cleaned up temp QTest file: {temp_file_path}")
                return True
            return True  # File doesn't exist, consider it cleaned
            
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {temp_file_path}: {e}")
            return False
    
    def get_temp_qtest_filename(self, comparison_id: int) -> str:
        """Get the expected temp filename for a comparison (for existing service compatibility)"""
        return f"azure_comparison_{comparison_id}_temp.xlsx"
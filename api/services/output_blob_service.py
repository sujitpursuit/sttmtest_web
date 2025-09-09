"""
Output Blob Service - Handles test step outputs in Azure Blob Storage
Manages JSON and Excel files for both delta and in-place generation modes
"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class OutputBlobService:
    """Service for managing test step output files in Azure Blob Storage"""
    
    def __init__(self):
        """Initialize Azure Blob connection for output files"""
        self.blob_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = "output-files"
        
        if not self.blob_connection_string:
            logger.error("Azure Storage connection string not configured")
            raise ValueError("Azure Storage connection string is required")
        
        # Initialize blob service client
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.blob_connection_string
        )
        
        # Ensure container exists
        self._ensure_container_exists()
        
        logger.info(f"OutputBlobService initialized with container: {self.container_name}")
    
    def _ensure_container_exists(self):
        """Create the output-files container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Created container: {self.container_name}")
            else:
                logger.debug(f"Container exists: {self.container_name}")
        except Exception as e:
            logger.error(f"Error ensuring container exists: {e}")
    
    def upload_test_step_outputs(self, 
                                comparison_id: int,
                                generation_mode: str,
                                json_file_path: Optional[str] = None,
                                excel_file_path: Optional[str] = None) -> Dict[str, Optional[str]]:
        """
        Upload test step generation outputs to Azure Blob Storage
        
        Args:
            comparison_id: ID of the comparison
            generation_mode: 'delta' or 'inplace'
            json_file_path: Local path to JSON report file
            excel_file_path: Local path to Excel file
            
        Returns:
            Dictionary with 'json_url' and 'excel_url' keys
        """
        result = {
            'json_url': None,
            'excel_url': None
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Upload JSON file if provided
        if json_file_path and os.path.exists(json_file_path):
            json_blob_name = f"comparison_{comparison_id}/{generation_mode}/test_steps_{generation_mode}_{timestamp}.json"
            json_url = self._upload_file(json_file_path, json_blob_name, 'application/json')
            if json_url:
                result['json_url'] = json_url
                logger.info(f"Uploaded JSON to: {json_url}")
        
        # Upload Excel file if provided
        if excel_file_path and os.path.exists(excel_file_path):
            excel_blob_name = f"comparison_{comparison_id}/{generation_mode}/test_steps_{generation_mode}_{timestamp}.xlsx"
            excel_url = self._upload_file(
                excel_file_path, 
                excel_blob_name, 
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            if excel_url:
                result['excel_url'] = excel_url
                logger.info(f"Uploaded Excel to: {excel_url}")
        
        return result
    
    def _upload_file(self, file_path: str, blob_name: str, content_type: str) -> Optional[str]:
        """
        Upload a single file to Azure Blob Storage
        
        Args:
            file_path: Local file path
            blob_name: Name for the blob in storage
            content_type: MIME type of the file
            
        Returns:
            Blob URL if successful, None otherwise
        """
        try:
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Read file content
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            # Upload with proper content settings
            content_settings = ContentSettings(content_type=content_type)
            
            blob_client.upload_blob(
                file_content,
                overwrite=True,
                content_settings=content_settings
            )
            
            # Return blob URL
            return blob_client.url
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_path} to blob {blob_name}: {e}")
            return None
    
    def download_output_file(self, blob_url: str, local_path: Optional[str] = None) -> Optional[str]:
        """
        Download an output file from Azure Blob Storage
        
        Args:
            blob_url: URL of the blob to download
            local_path: Optional local path to save the file
            
        Returns:
            Local file path if successful, None otherwise
        """
        try:
            # Extract blob name from URL
            blob_name = blob_url.split(f"/{self.container_name}/")[-1]
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Download blob content
            blob_data = blob_client.download_blob()
            content = blob_data.readall()
            
            # Determine local path
            if not local_path:
                import tempfile
                suffix = '.json' if blob_name.endswith('.json') else '.xlsx'
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                    tmp_file.write(content)
                    local_path = tmp_file.name
            else:
                with open(local_path, 'wb') as f:
                    f.write(content)
            
            logger.info(f"Downloaded blob to: {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download blob from {blob_url}: {e}")
            return None
    
    def delete_output_files(self, comparison_id: int, generation_mode: str) -> bool:
        """
        Delete output files for a specific comparison and mode
        
        Args:
            comparison_id: ID of the comparison
            generation_mode: 'delta' or 'inplace'
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # List blobs with prefix
            prefix = f"comparison_{comparison_id}/{generation_mode}/"
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            deleted_count = 0
            for blob in container_client.list_blobs(name_starts_with=prefix):
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob.name
                )
                blob_client.delete_blob()
                deleted_count += 1
                logger.info(f"Deleted blob: {blob.name}")
            
            logger.info(f"Deleted {deleted_count} blobs for comparison {comparison_id} ({generation_mode})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete output files: {e}")
            return False
    
    def list_comparison_outputs(self, comparison_id: int) -> Dict[str, list]:
        """
        List all output files for a comparison
        
        Args:
            comparison_id: ID of the comparison
            
        Returns:
            Dictionary with 'delta' and 'inplace' lists of blob URLs
        """
        result = {
            'delta': [],
            'inplace': []
        }
        
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # List delta outputs
            delta_prefix = f"comparison_{comparison_id}/delta/"
            for blob in container_client.list_blobs(name_starts_with=delta_prefix):
                blob_url = f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.container_name}/{blob.name}"
                result['delta'].append(blob_url)
            
            # List inplace outputs
            inplace_prefix = f"comparison_{comparison_id}/inplace/"
            for blob in container_client.list_blobs(name_starts_with=inplace_prefix):
                blob_url = f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.container_name}/{blob.name}"
                result['inplace'].append(blob_url)
            
            logger.info(f"Found {len(result['delta'])} delta and {len(result['inplace'])} inplace outputs for comparison {comparison_id}")
            
        except Exception as e:
            logger.error(f"Failed to list comparison outputs: {e}")
        
        return result
    
    def download_file(self, blob_name: str) -> bytes:
        """
        Download file content from blob storage
        
        Args:
            blob_name: Name of the blob to download (e.g., 'comparison_10/delta/file.xlsx')
            
        Returns:
            File content as bytes, or None if not found
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Download blob content
            download_stream = blob_client.download_blob()
            file_content = download_stream.readall()
            
            logger.info(f"Downloaded blob: {blob_name} ({len(file_content)} bytes)")
            return file_content
            
        except Exception as e:
            logger.error(f"Failed to download blob {blob_name}: {e}")
            return None
    
    def upload_impact_analysis_reports(
        self, 
        comparison_id: int,
        html_file_path: str,
        json_file_path: str
    ) -> Dict[str, Optional[str]]:
        """
        Upload impact analysis reports to Azure Blob Storage
        Uses the same container as test step outputs but different folder structure
        
        Args:
            comparison_id: ID of the comparison
            html_file_path: Path to the HTML report file
            json_file_path: Path to the JSON report file
            
        Returns:
            Dictionary with blob URLs for html_url and json_url
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create blob names with proper folder structure
        # Structure: output-files/comparison_{id}/impact/impact_analysis_{timestamp}.html
        html_blob_name = f"comparison_{comparison_id}/impact/impact_analysis_{timestamp}.html"
        json_blob_name = f"comparison_{comparison_id}/impact/impact_analysis_{timestamp}.json"
        
        result = {
            'html_url': None,
            'json_url': None
        }
        
        try:
            # Upload HTML file
            if html_file_path and os.path.exists(html_file_path):
                result['html_url'] = self._upload_file(
                    html_file_path, 
                    html_blob_name, 
                    'text/html; charset=utf-8'
                )
                if result['html_url']:
                    logger.info(f"Uploaded impact analysis HTML: {html_blob_name}")
            
            # Upload JSON file
            if json_file_path and os.path.exists(json_file_path):
                result['json_url'] = self._upload_file(
                    json_file_path, 
                    json_blob_name, 
                    'application/json; charset=utf-8'
                )
                if result['json_url']:
                    logger.info(f"Uploaded impact analysis JSON: {json_blob_name}")
            
            # Log summary
            uploaded_files = []
            if result['html_url']: uploaded_files.append('HTML')
            if result['json_url']: uploaded_files.append('JSON')
            
            if uploaded_files:
                logger.info(f"Successfully uploaded impact analysis reports for comparison {comparison_id}: {', '.join(uploaded_files)}")
            else:
                logger.warning(f"No impact analysis reports uploaded for comparison {comparison_id}")
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to upload impact analysis reports for comparison {comparison_id}: {e}")
            return result
    
    def download_impact_analysis_report(self, blob_url: str, file_type: str) -> Optional[bytes]:
        """
        Download impact analysis report content from blob storage
        
        Args:
            blob_url: URL of the blob to download
            file_type: 'html' or 'json' (for logging purposes)
            
        Returns:
            File content as bytes, None if failed
        """
        try:
            # Extract blob name from URL
            if f"/{self.container_name}/" in blob_url:
                blob_name = blob_url.split(f"/{self.container_name}/")[-1].split('?')[0]  # Remove SAS token if present
            else:
                logger.error(f"Invalid blob URL format: {blob_url}")
                return None
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Download blob content
            blob_data = blob_client.download_blob()
            content = blob_data.readall()
            
            logger.info(f"Downloaded impact analysis {file_type} report: {len(content)} bytes from {blob_name}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to download impact analysis {file_type} report from {blob_url}: {e}")
            return None
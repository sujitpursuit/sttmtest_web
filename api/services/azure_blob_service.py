"""
Azure Blob Service - Fetches JSON content from Azure Blob Storage
Handles downloading comparison JSON files from Azure Blob URLs with SAS tokens
"""

import logging
import requests
from typing import Dict, Any, Optional
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)


class AzureBlobService:
    """Service for fetching content from Azure Blob Storage"""
    
    def __init__(self):
        """Initialize the Azure Blob Service"""
        # Set reasonable timeout for blob requests
        self.timeout = 30  # seconds
        self.session = requests.Session()
    
    def fetch_json_from_blob(self, blob_url: str) -> Dict[str, Any]:
        """
        Fetch JSON content from Azure Blob Storage URL
        
        Args:
            blob_url: Full Azure Blob URL with SAS token
            
        Returns:
            Parsed JSON content as dictionary
            
        Raises:
            ValueError: If URL is invalid or content is not valid JSON
            RequestException: If network request fails
        """
        if not blob_url:
            raise ValueError("Blob URL cannot be empty")
        
        logger.info(f"Fetching JSON from Azure Blob: {blob_url[:50]}...")
        
        try:
            # Make GET request to fetch the blob content
            response = self.session.get(
                blob_url,
                timeout=self.timeout,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'STTM-Impact-Analysis/1.0'
                }
            )
            
            # Check for successful response
            response.raise_for_status()
            
            # Parse JSON content
            try:
                json_content = response.json()
                logger.info(f"Successfully fetched JSON from blob (size: {len(response.content)} bytes)")
                return json_content
                
            except ValueError as e:
                logger.error(f"Failed to parse JSON from blob response: {e}")
                raise ValueError(f"Blob content is not valid JSON: {e}")
                
        except Timeout:
            logger.error(f"Timeout while fetching blob: {blob_url[:50]}...")
            raise RequestException(f"Request timed out after {self.timeout} seconds")
            
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            
            if status_code == 403:
                logger.error("Access denied - SAS token may be expired or invalid")
                raise RequestException("Access denied to blob - SAS token may be expired")
            elif status_code == 404:
                logger.error("Blob not found at the specified URL")
                raise RequestException("Blob not found")
            else:
                logger.error(f"HTTP error while fetching blob: {e}")
                raise RequestException(f"Failed to fetch blob: HTTP {status_code}")
                
        except RequestException as e:
            logger.error(f"Network error while fetching blob: {e}")
            raise RequestException(f"Network error: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error while fetching blob: {e}")
            raise
    
    def fetch_json_from_local_path(self, local_path: str) -> Optional[Dict[str, Any]]:
        """
        Fallback method to fetch JSON from local path if blob URL fails
        
        Args:
            local_path: Local file path to the JSON file
            
        Returns:
            Parsed JSON content or None if file doesn't exist
        """
        import json
        from pathlib import Path
        
        try:
            file_path = Path(local_path)
            
            if not file_path.exists():
                logger.warning(f"Local file not found: {local_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json_content = json.load(f)
                
            logger.info(f"Successfully loaded JSON from local path: {local_path}")
            return json_content
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse local JSON file: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Error reading local file {local_path}: {e}")
            return None
    
    def fetch_comparison_json(self, blob_url: str, local_path: str = None) -> Dict[str, Any]:
        """
        Fetch comparison JSON with fallback to local path if blob fails
        
        Args:
            blob_url: Primary Azure Blob URL
            local_path: Optional fallback local path
            
        Returns:
            JSON content as dictionary
            
        Raises:
            Exception: If both blob and local fetch fail
        """
        # Try blob URL first
        try:
            return self.fetch_json_from_blob(blob_url)
        except Exception as blob_error:
            logger.warning(f"Failed to fetch from blob, trying local path: {blob_error}")
            
            # Try local path as fallback
            if local_path:
                local_content = self.fetch_json_from_local_path(local_path)
                if local_content:
                    return local_content
            
            # Both failed, raise the original blob error
            raise blob_error
    
    def validate_json_structure(self, json_content: Dict[str, Any]) -> bool:
        """
        Validate that the JSON has the expected structure for STTM comparison
        Checks for actual Azure Blob JSON format with executive_summary and detailed_changes
        
        Args:
            json_content: JSON content to validate
            
        Returns:
            True if structure is valid, False otherwise
        """
        try:
            # Check for expected top-level keys from actual Azure Blob format
            required_keys = ['executive_summary', 'detailed_changes']
            
            for key in required_keys:
                if key not in json_content:
                    logger.warning(f"Missing required key in JSON: {key}")
                    return False
            
            # Check executive_summary structure
            executive_summary = json_content.get('executive_summary', {})
            if not isinstance(executive_summary, dict):
                logger.warning("Invalid executive_summary structure in JSON")
                return False
            
            # Check detailed_changes structure
            detailed_changes = json_content.get('detailed_changes', {})
            if not isinstance(detailed_changes, dict):
                logger.warning("Invalid detailed_changes structure in JSON")
                return False
            
            # Check for changed_tabs and unchanged_tabs within detailed_changes
            changed_tabs = detailed_changes.get('changed_tabs', [])
            unchanged_tabs = detailed_changes.get('unchanged_tabs', [])
            
            if not isinstance(changed_tabs, list):
                logger.warning("Invalid changed_tabs structure in JSON")
                return False
                
            if not isinstance(unchanged_tabs, list):
                logger.warning("Invalid unchanged_tabs structure in JSON")
                return False
            
            logger.info("JSON structure validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating JSON structure: {e}")
            return False
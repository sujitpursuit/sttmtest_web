"""
STTM Parser - Format-agnostic parser using adapter pattern.

This parser is completely isolated from STTM format changes. When formats change,
only the adapter needs to be updated, not this parser or any other components.
"""

import json
import logging
from typing import Optional
from pathlib import Path

from models.sttm_models import STTMDocument
from parsers.sttm_format_adapter import STTMFormatAdapterFactory, STTMDataConverter


class STTMParser:
    """Format-agnostic STTM parser using adapter pattern"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.adapter_factory = STTMFormatAdapterFactory(logger)
        self.data_converter = STTMDataConverter(logger)
    
    def parse_file(self, file_path: str) -> STTMDocument:
        """Parse STTM file regardless of format version"""
        
        self.logger.info(f"Parsing STTM file: {file_path}")
        
        try:
            # Load JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Get appropriate adapter for this format
            adapter = self.adapter_factory.get_adapter(json_data)
            
            # Extract format-agnostic raw data
            raw_tabs = adapter.extract_raw_data(json_data)
            
            # Convert to domain models
            document = self.data_converter.convert_to_document(raw_tabs)
            
            self.logger.info(f"Successfully parsed STTM document using {adapter.get_format_version()}")
            self.logger.info(f"Found {len(document.changed_tabs)} changed tabs, "
                           f"{len(document.unchanged_tabs)} unchanged tabs")
            
            return document
            
        except FileNotFoundError:
            raise FileNotFoundError(f"STTM file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in STTM file: {e}")
        except Exception as e:
            raise Exception(f"Error parsing STTM file: {e}")
    
    def register_format_adapter(self, adapter):
        """Register a new format adapter for handling new STTM formats"""
        self.adapter_factory.register_adapter(adapter)
        self.logger.info(f"Registered new format adapter: {adapter.get_format_version()}")
    
    def get_supported_formats(self) -> list:
        """Get list of supported STTM formats"""
        return [adapter.get_format_version() for adapter in self.adapter_factory._adapters]


def parse_sttm_file(file_path: str, logger: Optional[logging.Logger] = None) -> STTMDocument:
    """Convenience function to parse an STTM file using adapter pattern"""
    parser = STTMParser(logger)
    return parser.parse_file(file_path)
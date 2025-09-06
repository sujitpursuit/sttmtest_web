"""
QTEST Parser - Format-agnostic parser using adapter pattern.

This parser is completely isolated from Excel format changes. When formats change,
only the adapter needs to be updated, not this parser or any other components.
"""

import pandas as pd
import logging
from typing import Optional
from pathlib import Path

from models.test_models import QTestDocument
from parsers.excel_format_adapter import ExcelFormatAdapterFactory, ExcelDataConverter
from parsers.id_pattern_detector import IDPatternDetector


class QTestParser:
    """Format-agnostic QTEST parser using adapter pattern"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.adapter_factory = ExcelFormatAdapterFactory(logger)
        self.data_converter = ExcelDataConverter(logger)
        self.id_detector = IDPatternDetector(logger)
    
    def parse_file(self, file_path: str) -> QTestDocument:
        """Parse Excel test case file regardless of format version"""
        
        self.logger.info(f"Parsing QTEST file: {file_path}")
        
        try:
            # Read Excel file and get sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            self.logger.info(f"Found sheets: {sheet_names}")
            
            # Get appropriate adapter for this format
            adapter = self.adapter_factory.get_adapter(excel_file)
            
            # Find the main test sheet using adapter
            main_sheet = adapter.find_test_sheet(sheet_names)
            self.logger.info(f"Using main sheet: {main_sheet}")
            
            # Read the main sheet
            df = pd.read_excel(file_path, sheet_name=main_sheet)
            
            # Extract format-agnostic raw data using adapter
            parsing_result = adapter.extract_test_cases(df, sheet_names)
            
            # Convert to domain models
            test_cases = self.data_converter.convert_to_test_cases(parsing_result.test_cases)
            
            # Create document
            document = QTestDocument(
                test_cases=test_cases,
                sheet_names=sheet_names
            )
            
            # Detect ID pattern
            test_ids = [tc.id for tc in test_cases]
            id_analysis = self.id_detector.analyze_ids(test_ids)
            
            document.detected_id_pattern = id_analysis.pattern
            document.id_format_description = id_analysis.format_description
            
            # Update document statistics
            document.total_test_cases = len(test_cases)
            document.total_test_steps = sum(tc.get_step_count() for tc in test_cases)
            
            self.logger.info(f"Successfully parsed using {adapter.get_format_name()}")
            self.logger.info(f"Parsed {document.total_test_cases} test cases with "
                           f"{document.total_test_steps} total steps")
            self.logger.info(f"Detected ID pattern: {document.id_format_description}")
            
            return document
            
        except FileNotFoundError:
            raise FileNotFoundError(f"QTEST file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error parsing QTEST file: {e}")
    
    def register_format_adapter(self, adapter):
        """Register a new Excel format adapter for handling new formats"""
        self.adapter_factory.register_adapter(adapter)
        self.logger.info(f"Registered new Excel format adapter: {adapter.get_format_name()}")
    
    def get_supported_formats(self) -> list:
        """Get list of supported Excel formats"""
        return [adapter.get_format_name() for adapter in self.adapter_factory._adapters]


def parse_qtest_file(file_path: str, logger: Optional[logging.Logger] = None) -> QTestDocument:
    """Convenience function to parse a QTEST file using adapter pattern"""
    parser = QTestParser(logger)
    return parser.parse_file(file_path)
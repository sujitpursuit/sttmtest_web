"""
Excel Format Adapter - Isolates Excel format changes from the test case parser.

This adapter pattern ensures that when Excel export formats change, only the 
adapter needs to be updated, not the core test case parser or other components.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import pandas as pd
import logging

from models.test_models import TestCase, TestStep


@dataclass
class RawTestCaseData:
    """Raw test case data extracted from any Excel format - format-agnostic"""
    id: str
    name: str
    description: str
    precondition: str
    raw_steps: List[Dict[str, Any]] = None  # Raw step data from Excel
    
    def __post_init__(self):
        if self.raw_steps is None:
            self.raw_steps = []


@dataclass
class RawTestStepData:
    """Raw test step data extracted from any Excel format - format-agnostic"""
    step_number: int
    description: str
    expected_result: str


@dataclass
class ExcelParsingResult:
    """Result of Excel parsing with metadata"""
    test_cases: List[RawTestCaseData]
    detected_id_pattern: Optional[str] = None
    sheet_names: List[str] = None
    total_rows_processed: int = 0
    
    def __post_init__(self):
        if self.sheet_names is None:
            self.sheet_names = []


class ExcelFormatAdapter(ABC):
    """Abstract adapter for different Excel test case formats"""
    
    @abstractmethod
    def get_format_name(self) -> str:
        """Get the name/version of this Excel format"""
        pass
    
    @abstractmethod
    def validate_format(self, excel_file: pd.ExcelFile) -> bool:
        """Validate if this adapter can handle the given Excel format"""
        pass
    
    @abstractmethod
    def find_test_sheet(self, sheet_names: List[str]) -> str:
        """Find the main sheet containing test cases"""
        pass
    
    @abstractmethod
    def get_column_mappings(self) -> Dict[str, List[str]]:
        """Get column name mappings for this format"""
        pass
    
    @abstractmethod
    def extract_test_cases(self, df: pd.DataFrame, sheet_names: List[str]) -> ExcelParsingResult:
        """Extract test cases from the Excel dataframe"""
        pass


class QTestExcelFormatAdapter(ExcelFormatAdapter):
    """Adapter for QTEST Excel export format"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def get_format_name(self) -> str:
        return "QTEST Excel Export Format"
    
    def validate_format(self, excel_file: pd.ExcelFile) -> bool:
        """Validate QTEST format - look for typical QTEST characteristics"""
        sheet_names = excel_file.sheet_names
        
        # QTEST typically has these characteristics:
        # 1. Multiple sheets with one being test data
        # 2. Specific column patterns
        # 3. Test case ID patterns
        
        # For now, accept any Excel file (QTEST is quite flexible)
        return len(sheet_names) > 0
    
    def find_test_sheet(self, sheet_names: List[str]) -> str:
        """Find the main sheet containing test cases in QTEST format"""
        
        # Skip obvious non-test sheets
        skip_patterns = ['cover', 'summary', 'index', 'readme', 'instruction']
        
        # QTEST-specific patterns (in priority order)
        test_sheet_patterns = [
            'vendor', 'inbound', 'test', 'testcase', 'test case', 'tests', 
            'tc', 'qtest', 'md-', 'main', 'data'
        ]
        
        # Filter out cover/summary sheets first
        candidate_sheets = []
        for sheet in sheet_names:
            sheet_lower = sheet.lower()
            is_skip = any(skip in sheet_lower for skip in skip_patterns)
            if not is_skip:
                candidate_sheets.append(sheet)
        
        if not candidate_sheets:
            candidate_sheets = sheet_names
        
        # First try exact matches on candidates
        for pattern in test_sheet_patterns:
            for sheet in candidate_sheets:
                if pattern.lower() == sheet.lower():
                    return sheet
        
        # Then try partial matches on candidates
        for pattern in test_sheet_patterns:
            for sheet in candidate_sheets:
                if pattern.lower() in sheet.lower():
                    return sheet
        
        # Default to first non-cover sheet, or first sheet
        return candidate_sheets[0] if candidate_sheets else sheet_names[0]
    
    def get_column_mappings(self) -> Dict[str, List[str]]:
        """Get QTEST column name mappings"""
        return {
            'name': ['name', 'test_name', 'test case name', 'testcase name'],
            'id': ['id', 'test_id', 'testcase id', 'test case id'],
            'description': ['description', 'test_description', 'test case description'],
            'precondition': ['precondition', 'preconditions', 'pre-condition', 'prerequisite'],
            'step_number': ['test step #', 'step #', 'step number', 'step_number'],
            'step_description': ['test step description', 'step description', 'step_description'],
            'step_expected': ['test step expected result', 'expected result', 'expected_result', 'step_expected_result']
        }
    
    def extract_test_cases(self, df: pd.DataFrame, sheet_names: List[str]) -> ExcelParsingResult:
        """Extract test cases from QTEST Excel format"""
        
        self.logger.debug(f"Extracting test cases from QTEST format with {len(df)} rows")
        
        # Map columns
        column_mapping = self._map_columns(df.columns.tolist())
        self.logger.info(f"Column mapping: {column_mapping}")
        
        # Validate required columns
        missing_columns = []
        for required_col in ['id', 'name']:
            if column_mapping.get(required_col) is None:
                missing_columns.append(required_col)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Handle merged cells by forward-filling test case information
        df_copy = df.copy()
        
        # Forward fill test case metadata columns (these are typically merged)
        metadata_columns = []
        for col_key in ['id', 'name', 'description', 'precondition']:
            col_name = column_mapping.get(col_key)
            if col_name:
                metadata_columns.append(col_name)
                # Forward fill the values from merged cells
                df_copy[col_name] = df_copy[col_name].ffill()
        
        self.logger.debug(f"Forward-filled merged cell columns: {metadata_columns}")
        
        # Extract test cases
        raw_test_cases = []
        test_case_groups = df_copy.groupby(column_mapping['id'])
        
        for test_id, group in test_case_groups:
            if pd.isna(test_id) or str(test_id).strip() == '':
                continue
            
            raw_test_case = self._extract_test_case_group(str(test_id), group, column_mapping)
            if raw_test_case:
                raw_test_cases.append(raw_test_case)
        
        self.logger.debug(f"Extracted {len(raw_test_cases)} test cases from QTEST format")
        
        return ExcelParsingResult(
            test_cases=raw_test_cases,
            sheet_names=sheet_names,
            total_rows_processed=len(df)
        )
    
    def _map_columns(self, actual_columns: List[str]) -> Dict[str, str]:
        """Map actual column names to expected column names"""
        column_mapping = {}
        expected_columns = self.get_column_mappings()
        
        for expected_col, possible_names in expected_columns.items():
            for actual_col in actual_columns:
                if actual_col.lower().strip() in [name.lower() for name in possible_names]:
                    column_mapping[expected_col] = actual_col
                    break
        
        return column_mapping
    
    def _extract_test_case_group(self, test_id: str, group: pd.DataFrame, 
                                column_mapping: Dict[str, str]) -> Optional[RawTestCaseData]:
        """Extract a single test case from grouped rows"""
        
        try:
            # Get basic test case information from first row
            first_row = group.iloc[0]
            
            raw_test_case = RawTestCaseData(
                id=test_id.strip(),
                name=self._safe_get_value(first_row, column_mapping.get('name'), ''),
                description=self._safe_get_value(first_row, column_mapping.get('description'), ''),
                precondition=self._safe_get_value(first_row, column_mapping.get('precondition'), '')
            )
            
            # Extract test steps
            raw_test_case.raw_steps = self._extract_test_steps(group, column_mapping)
            
            return raw_test_case
            
        except Exception as e:
            self.logger.error(f"Error extracting test case {test_id}: {e}")
            return None
    
    def _extract_test_steps(self, group: pd.DataFrame, 
                           column_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract test steps from grouped rows"""
        
        raw_steps = []
        step_num_col = column_mapping.get('step_number')
        step_desc_col = column_mapping.get('step_description')
        step_expected_col = column_mapping.get('step_expected')
        
        for _, row in group.iterrows():
            # Get step number
            step_number = self._safe_get_value(row, step_num_col)
            if pd.isna(step_number):
                continue
                
            try:
                step_number = int(float(step_number))
            except (ValueError, TypeError):
                continue
            
            # Get step description and expected result
            step_description = self._safe_get_value(row, step_desc_col, '')
            step_expected = self._safe_get_value(row, step_expected_col, '')
            
            # Skip empty steps
            if not step_description.strip() and not step_expected.strip():
                continue
            
            raw_step = {
                'step_number': step_number,
                'description': step_description.strip(),
                'expected_result': step_expected.strip()
            }
            
            raw_steps.append(raw_step)
        
        # Sort steps by step number
        raw_steps.sort(key=lambda x: x['step_number'])
        return raw_steps
    
    def _safe_get_value(self, row: pd.Series, column: Optional[str], 
                       default: str = '') -> str:
        """Safely get a value from a pandas row"""
        if column is None or column not in row:
            return default
        
        value = row[column]
        if pd.isna(value):
            return default
        
        return str(value).strip()


class ExcelFormatAdapterFactory:
    """Factory to create the appropriate Excel format adapter"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._adapters = [
            QTestExcelFormatAdapter(logger),
            # Future adapters can be added here:
            # TestRailExcelFormatAdapter(logger),
            # ZephyrExcelFormatAdapter(logger),
        ]
    
    def get_adapter(self, excel_file: pd.ExcelFile) -> ExcelFormatAdapter:
        """Get the appropriate adapter for the given Excel file"""
        
        for adapter in self._adapters:
            if adapter.validate_format(excel_file):
                self.logger.info(f"Using Excel adapter: {adapter.get_format_name()}")
                return adapter
        
        # Default to QTEST adapter
        self.logger.warning("No specific Excel adapter found, using QTEST adapter")
        return self._adapters[0]
    
    def register_adapter(self, adapter: ExcelFormatAdapter):
        """Register a new Excel format adapter"""
        self._adapters.insert(0, adapter)  # Insert at beginning for priority


class ExcelDataConverter:
    """Converts format-agnostic raw Excel data to domain models"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def convert_to_test_cases(self, raw_test_cases: List[RawTestCaseData]) -> List[TestCase]:
        """Convert raw test case data to TestCase domain models"""
        
        test_cases = []
        
        for raw_tc in raw_test_cases:
            test_case = TestCase(
                id=raw_tc.id,
                name=raw_tc.name,
                description=raw_tc.description,
                precondition=raw_tc.precondition
            )
            
            # Convert test steps
            for raw_step in raw_tc.raw_steps:
                test_step = TestStep(
                    step_number=raw_step['step_number'],
                    description=raw_step['description'],
                    expected_result=raw_step['expected_result']
                )
                test_case.test_steps.append(test_step)
            
            # Perform basic content analysis (from original parser)
            self._analyze_test_case_content(test_case)
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _analyze_test_case_content(self, test_case: TestCase):
        """Perform basic content analysis to identify references"""
        
        # Get all text content
        all_content = test_case.get_all_text_content().lower()
        
        # Look for common test-related terms
        system_terms = [
            'vendor', 'proxy', 'netsuite', 'd365', 'dynamics',
            'inbound', 'outbound', 'mapping', 'field', 'target', 'source',
            'dealer', 'consumer', 'request', 'response'
        ]
        
        # Basic keyword extraction
        for term in system_terms:
            if term in all_content:
                if term not in test_case.referenced_systems:
                    test_case.referenced_systems.append(term)
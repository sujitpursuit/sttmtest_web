"""
Test case data models for representing parsed QTEST data.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re


@dataclass
class TestStep:
    """Represents a single test step within a test case"""
    step_number: int
    description: str
    expected_result: str
    
    def __str__(self) -> str:
        return f"Step {self.step_number}: {self.description[:50]}..."


@dataclass
class TestCase:
    """Represents a complete test case from QTEST"""
    id: str
    name: str
    description: str
    precondition: str
    test_steps: List[TestStep] = field(default_factory=list)
    
    # Analysis fields (populated during parsing)
    referenced_tabs: List[str] = field(default_factory=list)
    referenced_fields: List[str] = field(default_factory=list)
    referenced_systems: List[str] = field(default_factory=list)
    
    def get_step_count(self) -> int:
        """Get the number of test steps"""
        return len(self.test_steps)
    
    def get_step_by_number(self, step_number: int) -> Optional[TestStep]:
        """Get a specific test step by its number"""
        for step in self.test_steps:
            if step.step_number == step_number:
                return step
        return None
    
    def get_all_text_content(self) -> str:
        """Get all text content from the test case for analysis"""
        content_parts = [self.name, self.description, self.precondition]
        
        for step in self.test_steps:
            content_parts.extend([step.description, step.expected_result])
        
        return " ".join(filter(None, content_parts))
    
    def contains_text(self, search_text: str, case_sensitive: bool = False) -> bool:
        """Check if the test case contains specific text"""
        content = self.get_all_text_content()
        if not case_sensitive:
            content = content.lower()
            search_text = search_text.lower()
        return search_text in content
    
    def find_text_in_steps(self, search_text: str, case_sensitive: bool = False) -> List[int]:
        """Find which step numbers contain the search text"""
        matching_steps = []
        
        for step in self.test_steps:
            step_content = f"{step.description} {step.expected_result}"
            if not case_sensitive:
                step_content = step_content.lower()
                search_text = search_text.lower()
            
            if search_text in step_content:
                matching_steps.append(step.step_number)
        
        return matching_steps


@dataclass
class QTestDocument:
    """Represents the complete QTEST export document"""
    test_cases: List[TestCase] = field(default_factory=list)
    
    # Metadata discovered during parsing
    detected_id_pattern: Optional[str] = None
    id_format_description: Optional[str] = None
    sheet_names: List[str] = field(default_factory=list)
    
    # Statistics
    total_test_cases: int = 0
    total_test_steps: int = 0
    
    def get_test_case_by_id(self, test_id: str) -> Optional[TestCase]:
        """Find a test case by its ID"""
        for test_case in self.test_cases:
            if test_case.id == test_id:
                return test_case
        return None
    
    def get_test_cases_containing_text(self, search_text: str, case_sensitive: bool = False) -> List[TestCase]:
        """Get all test cases that contain specific text"""
        return [tc for tc in self.test_cases if tc.contains_text(search_text, case_sensitive)]
    
    def get_all_test_ids(self) -> List[str]:
        """Get all test case IDs"""
        return [tc.id for tc in self.test_cases]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the QTEST document"""
        return {
            "total_test_cases": len(self.test_cases),
            "total_test_steps": sum(tc.get_step_count() for tc in self.test_cases),
            "detected_id_pattern": self.detected_id_pattern,
            "id_format_description": self.id_format_description,
            "sheet_names": self.sheet_names,
            "average_steps_per_test": round(sum(tc.get_step_count() for tc in self.test_cases) / len(self.test_cases), 2) if self.test_cases else 0
        }


@dataclass
class IDPatternAnalysis:
    """Results of analyzing test case ID patterns"""
    pattern: str
    format_description: str
    confidence: float
    sample_ids: List[str] = field(default_factory=list)
    
    # Pattern components
    prefix: Optional[str] = None
    separator: Optional[str] = None
    number_part: Optional[str] = None
    
    def generate_new_id(self, suffix: str = "NEW") -> str:
        """Generate a new test case ID based on detected pattern"""
        if self.prefix and self.separator:
            return f"{self.prefix}{self.separator}9999{self.separator}{suffix}"
        elif self.prefix:
            return f"{self.prefix}9999{suffix}"
        else:
            return f"TC-9999-{suffix}"
    
    def is_valid_pattern(self) -> bool:
        """Check if the detected pattern is valid/reliable"""
        return self.confidence >= 0.7 and bool(self.pattern)
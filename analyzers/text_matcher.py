"""
Simple Text Matching Engine - Find references to STTM changes in test cases

This module provides simple, understandable text matching algorithms to find
references to STTM tab names, field names, and sample data in test case content.
"""

import re
from typing import List, Set, Optional, Tuple
from dataclasses import dataclass
import logging

from models.test_models import TestCase, TestStep
from models.sttm_models import STTMTab, STTMMapping
from models.impact_models import MatchResult, MatchType


class SimpleTextMatcher:
    """Simple text matching engine for finding STTM references in test cases"""
    
    def __init__(self, case_sensitive: bool = False, min_keyword_length: int = 3,
                 logger: Optional[logging.Logger] = None):
        self.case_sensitive = case_sensitive
        self.min_keyword_length = min_keyword_length
        self.logger = logger or logging.getLogger(__name__)
    
    def find_tab_references(self, test_case: TestCase, tab_name: str) -> List[MatchResult]:
        """Find references to STTM tab name in test case content"""
        matches = []
        
        # Extract keywords from tab name (split by space, filter short words)
        tab_keywords = self._extract_keywords(tab_name)
        
        # Search in test case name
        name_matches = self._find_keywords_in_text(
            test_case.name, tab_keywords, "test_name"
        )
        matches.extend(name_matches)
        
        # Search in test case description  
        desc_matches = self._find_keywords_in_text(
            test_case.description, tab_keywords, "description"
        )
        matches.extend(desc_matches)
        
        # Search in test case precondition
        precond_matches = self._find_keywords_in_text(
            test_case.precondition, tab_keywords, "precondition"
        )
        matches.extend(precond_matches)
        
        # Search in test steps
        for i, step in enumerate(test_case.test_steps):
            step_desc_matches = self._find_keywords_in_text(
                step.description, tab_keywords, f"step_{i+1}_description"
            )
            matches.extend(step_desc_matches)
            
            step_result_matches = self._find_keywords_in_text(
                step.expected_result, tab_keywords, f"step_{i+1}_expected_result"
            )
            matches.extend(step_result_matches)
        
        # Determine match type based on keyword coverage
        if matches:
            coverage = self._calculate_keyword_coverage(matches, tab_keywords)
            match_type = self._determine_tab_match_type(coverage)
            
            # Update match types based on coverage
            for match in matches:
                match.match_type = match_type
        
        return matches
    
    def find_field_references(self, test_case: TestCase, mappings: List[STTMMapping]) -> List[MatchResult]:
        """Find references to field names in test case content"""
        matches = []
        
        # Collect all field names to search for
        field_names = set()
        for mapping in mappings:
            if mapping.source_field:
                field_names.add(mapping.source_field)
            if mapping.target_field:
                field_names.add(mapping.target_field)
        
        # Search for each field name
        for field_name in field_names:
            field_matches = self._find_exact_text_matches(test_case, field_name, "field_name")
            matches.extend(field_matches)
        
        return matches
    
    def find_sample_data_references(self, test_case: TestCase, mappings: List[STTMMapping]) -> List[MatchResult]:
        """Find references to sample data values in test case content"""
        matches = []
        
        # Collect all sample data values
        sample_values = set()
        for mapping in mappings:
            if mapping.source_sample_data and len(mapping.source_sample_data.strip()) >= 2:
                sample_values.add(mapping.source_sample_data.strip())
        
        # Search for each sample data value
        for sample_value in sample_values:
            sample_matches = self._find_exact_text_matches(test_case, sample_value, "sample_data")
            matches.extend(sample_matches)
        
        return matches
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        if not text:
            return []
        
        # Split by common delimiters and clean up
        words = re.split(r'[\s\-_\.]+', text)
        
        # Filter keywords
        keywords = []
        for word in words:
            word = word.strip()
            if (len(word) >= self.min_keyword_length and 
                not word.isdigit() and 
                word.lower() not in ['the', 'and', 'for', 'with', 'from', 'into']):
                keywords.append(word)
        
        return keywords
    
    def _find_keywords_in_text(self, text: str, keywords: List[str], location: str) -> List[MatchResult]:
        """Find keywords in a piece of text"""
        if not text or not keywords:
            return []
        
        matches = []
        search_text = text if self.case_sensitive else text.lower()
        
        for keyword in keywords:
            search_keyword = keyword if self.case_sensitive else keyword.lower()
            
            if search_keyword in search_text:
                # Find the actual matched text for evidence
                pattern = re.escape(search_keyword)
                if not self.case_sensitive:
                    pattern = f"(?i){pattern}"
                
                match = re.search(pattern, text)
                matched_text = match.group() if match else keyword
                
                matches.append(MatchResult(
                    match_type=MatchType.PARTIAL_TAB_MATCH,  # Will be updated later
                    confidence_score=0.8,  # High confidence for keyword matches
                    matched_text=matched_text,
                    location=location,
                    reasoning=f"Found keyword '{keyword}' in {location}"
                ))
        
        return matches
    
    def _find_exact_text_matches(self, test_case: TestCase, search_text: str, 
                                match_category: str) -> List[MatchResult]:
        """Find exact text matches in test case content"""
        matches = []
        
        # Define search locations with their content
        search_locations = [
            ("test_name", test_case.name),
            ("description", test_case.description),
            ("precondition", test_case.precondition)
        ]
        
        # Add test steps
        for i, step in enumerate(test_case.test_steps):
            search_locations.append((f"step_{i+1}_description", step.description))
            search_locations.append((f"step_{i+1}_expected_result", step.expected_result))
        
        # Search in each location
        for location, content in search_locations:
            if not content:
                continue
                
            search_content = content if self.case_sensitive else content.lower()
            search_target = search_text if self.case_sensitive else search_text.lower()
            
            if search_target in search_content:
                # Determine match type based on category
                if match_category == "field_name":
                    match_type = MatchType.FIELD_NAME_MATCH
                    reasoning = f"Found field name '{search_text}' in {location}"
                elif match_category == "sample_data":
                    match_type = MatchType.SAMPLE_DATA_MATCH  
                    reasoning = f"Found sample data '{search_text}' in {location}"
                else:
                    match_type = MatchType.PARTIAL_TAB_MATCH
                    reasoning = f"Found text '{search_text}' in {location}"
                
                matches.append(MatchResult(
                    match_type=match_type,
                    confidence_score=0.9,  # High confidence for exact matches
                    matched_text=search_text,
                    location=location,
                    reasoning=reasoning
                ))
        
        return matches
    
    def _calculate_keyword_coverage(self, matches: List[MatchResult], 
                                  total_keywords: List[str]) -> float:
        """Calculate what percentage of keywords were found"""
        if not total_keywords:
            return 0.0
        
        # Get unique matched keywords
        matched_keywords = set()
        for match in matches:
            # The matched_text might be the actual keyword found
            matched_keywords.add(match.matched_text.lower())
        
        # Count how many of the original keywords were matched
        original_keywords_lower = [k.lower() for k in total_keywords]
        matches_count = 0
        
        for keyword in original_keywords_lower:
            for matched in matched_keywords:
                if keyword in matched or matched in keyword:
                    matches_count += 1
                    break
        
        return matches_count / len(total_keywords)
    
    def _determine_tab_match_type(self, keyword_coverage: float) -> MatchType:
        """Determine match type based on keyword coverage"""
        if keyword_coverage >= 0.8:  # 80% or more keywords matched
            return MatchType.EXACT_TAB_MATCH
        elif keyword_coverage > 0.0:  # Some keywords matched
            return MatchType.PARTIAL_TAB_MATCH
        else:
            return MatchType.NO_MATCH


class MatchResultAnalyzer:
    """Analyzer to process and summarize match results"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def get_best_tab_match(self, matches: List[MatchResult]) -> Optional[MatchResult]:
        """Get the best tab match from a list of matches"""
        if not matches:
            return None
        
        # Sort by match type priority and confidence
        type_priority = {
            MatchType.EXACT_TAB_MATCH: 3,
            MatchType.PARTIAL_TAB_MATCH: 2,
            MatchType.FIELD_NAME_MATCH: 1,
            MatchType.SAMPLE_DATA_MATCH: 1,
            MatchType.NO_MATCH: 0
        }
        
        best_match = max(matches, key=lambda m: (
            type_priority.get(m.match_type, 0),
            m.confidence_score
        ))
        
        return best_match
    
    def get_match_summary(self, matches: List[MatchResult]) -> str:
        """Get a human-readable summary of matches"""
        if not matches:
            return "No matches found"
        
        # Group by match type
        by_type = {}
        for match in matches:
            match_type = match.match_type
            if match_type not in by_type:
                by_type[match_type] = []
            by_type[match_type].append(match)
        
        # Create summary
        summary_parts = []
        for match_type, type_matches in by_type.items():
            count = len(type_matches)
            type_name = match_type.value.replace('_', ' ').title()
            summary_parts.append(f"{count} {type_name}")
        
        return ", ".join(summary_parts)
    
    def calculate_overall_confidence(self, matches: List[MatchResult]) -> float:
        """Calculate overall confidence from multiple matches"""
        if not matches:
            return 0.0
        
        # Use the highest confidence score, but boost if multiple matches
        max_confidence = max(match.confidence_score for match in matches)
        
        # Boost confidence if we have multiple types of matches
        unique_types = len(set(match.match_type for match in matches))
        confidence_boost = min(0.1 * (unique_types - 1), 0.2)  # Max 20% boost
        
        final_confidence = min(max_confidence + confidence_boost, 1.0)
        return final_confidence
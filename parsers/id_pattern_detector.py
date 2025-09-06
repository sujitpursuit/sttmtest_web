"""
Test Case ID Pattern Detector - Auto-discovers test case ID formats from QTEST exports.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from collections import Counter

from models.test_models import IDPatternAnalysis


class IDPatternDetector:
    """Detects and analyzes test case ID patterns from QTEST exports"""
    
    # Common ID patterns to look for
    ID_PATTERNS = [
        # Pattern, Description, Regex
        (r'^TC-?\d+$', 'TC-#### format', r'(TC)-?(\d+)'),
        (r'^TEST-?\d+$', 'TEST-#### format', r'(TEST)-?(\d+)'),
        (r'^T-?\d+$', 'T-#### format', r'(T)-?(\d+)'),
        (r'^[A-Z]+-\d+$', 'PREFIX-#### format', r'([A-Z]+)-(\d+)'),
        (r'^\d+$', 'Numeric only format', r'(\d+)'),
        (r'^[A-Z]{2,4}\d+$', 'ALPHA#### format', r'([A-Z]{2,4})(\d+)'),
        (r'^.+-\w+$', 'Complex format', r'(.+)-(\w+)'),
    ]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def analyze_ids(self, test_ids: List[str]) -> IDPatternAnalysis:
        """Analyze test case IDs and determine the most likely pattern"""
        
        if not test_ids:
            return IDPatternAnalysis(
                pattern="",
                format_description="No test IDs found",
                confidence=0.0
            )
        
        self.logger.info(f"Analyzing {len(test_ids)} test case IDs")
        
        # Clean and filter IDs
        clean_ids = [str(id_val).strip() for id_val in test_ids if id_val]
        clean_ids = [id_val for id_val in clean_ids if id_val and id_val.lower() != 'nan']
        
        if not clean_ids:
            return IDPatternAnalysis(
                pattern="",
                format_description="No valid test IDs found",
                confidence=0.0
            )
        
        # Find pattern matches
        pattern_matches = self._find_pattern_matches(clean_ids)
        
        # Determine best pattern
        best_pattern = self._select_best_pattern(pattern_matches, clean_ids)
        
        # Analyze pattern components
        components = self._analyze_pattern_components(best_pattern, clean_ids)
        
        # Create analysis result
        analysis = IDPatternAnalysis(
            pattern=best_pattern['regex'] if best_pattern else "",
            format_description=best_pattern['description'] if best_pattern else "Unknown format",
            confidence=best_pattern['confidence'] if best_pattern else 0.0,
            sample_ids=clean_ids[:5],  # First 5 as samples
            prefix=components.get('prefix'),
            separator=components.get('separator'),
            number_part=components.get('number_part')
        )
        
        self.logger.info(f"Detected pattern: {analysis.format_description} "
                        f"(confidence: {analysis.confidence:.2f})")
        
        return analysis
    
    def _find_pattern_matches(self, test_ids: List[str]) -> Dict[str, Dict]:
        """Find which patterns match the test IDs"""
        pattern_matches = {}
        
        for pattern_regex, description, extract_regex in self.ID_PATTERNS:
            matches = []
            for test_id in test_ids:
                if re.match(pattern_regex, test_id, re.IGNORECASE):
                    matches.append(test_id)
            
            if matches:
                confidence = len(matches) / len(test_ids)
                pattern_matches[description] = {
                    'pattern': pattern_regex,
                    'extract_regex': extract_regex,
                    'description': description,
                    'matches': matches,
                    'match_count': len(matches),
                    'confidence': confidence
                }
                
                self.logger.debug(f"Pattern '{description}': {len(matches)}/{len(test_ids)} matches "
                                f"({confidence:.2f} confidence)")
        
        return pattern_matches
    
    def _select_best_pattern(self, pattern_matches: Dict[str, Dict], 
                           test_ids: List[str]) -> Optional[Dict]:
        """Select the best matching pattern based on confidence and coverage"""
        
        if not pattern_matches:
            # Try to create a custom pattern for unrecognized format
            return self._create_custom_pattern(test_ids)
        
        # Sort by confidence (highest first)
        sorted_patterns = sorted(
            pattern_matches.values(),
            key=lambda x: x['confidence'],
            reverse=True
        )
        
        best = sorted_patterns[0]
        
        # Ensure the best pattern has 'regex' key for compatibility
        if 'extract_regex' in best:
            best['regex'] = best['extract_regex']
        
        # If confidence is too low, try custom pattern
        if best['confidence'] < 0.5:
            custom = self._create_custom_pattern(test_ids)
            if custom and custom['confidence'] > best['confidence']:
                return custom
        
        return best
    
    def _create_custom_pattern(self, test_ids: List[str]) -> Optional[Dict]:
        """Create a custom pattern for unrecognized ID formats"""
        
        if not test_ids:
            return None
        
        # Analyze common characteristics
        sample_ids = test_ids[:10]  # Use first 10 for analysis
        
        # Look for common prefixes
        prefixes = []
        separators = []
        
        for test_id in sample_ids:
            # Find letters followed by numbers or separators
            match = re.match(r'^([A-Za-z]+)([^A-Za-z\d]*)(\d*)', test_id)
            if match:
                prefix, sep, num = match.groups()
                if prefix:
                    prefixes.append(prefix)
                if sep:
                    separators.append(sep)
        
        # Find most common prefix and separator
        common_prefix = self._most_common(prefixes) if prefixes else None
        common_separator = self._most_common(separators) if separators else None
        
        if common_prefix:
            # Create pattern based on common structure
            if common_separator:
                pattern = f"^{re.escape(common_prefix)}{re.escape(common_separator)}\\d+$"
                description = f"{common_prefix}{common_separator}#### format"
                extract_regex = f"({re.escape(common_prefix)}){re.escape(common_separator)}(\\d+)"
            else:
                pattern = f"^{re.escape(common_prefix)}\\d*.*$"
                description = f"{common_prefix}#### format (custom)"
                extract_regex = f"({re.escape(common_prefix)})(.*)"
            
            # Test pattern against all IDs
            matches = [tid for tid in test_ids if re.match(pattern, tid, re.IGNORECASE)]
            confidence = len(matches) / len(test_ids)
            
            return {
                'pattern': pattern,
                'extract_regex': extract_regex,
                'regex': extract_regex,  # Add compatibility key
                'description': description,
                'matches': matches,
                'match_count': len(matches),
                'confidence': confidence
            }
        
        return None
    
    def _analyze_pattern_components(self, pattern: Optional[Dict], 
                                  test_ids: List[str]) -> Dict[str, str]:
        """Analyze the components of the detected pattern"""
        components = {}
        
        if not pattern or not pattern.get('extract_regex'):
            return components
        
        extract_regex = pattern['extract_regex']
        
        # Extract components from sample IDs
        for test_id in test_ids[:5]:
            match = re.match(extract_regex, test_id, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 1:
                    components['prefix'] = groups[0]
                if len(groups) >= 2:
                    # Check if second group is separator or number
                    second_group = groups[1]
                    if second_group.isdigit():
                        components['number_part'] = second_group
                    else:
                        components['separator'] = second_group
                        if len(groups) >= 3:
                            components['number_part'] = groups[2]
                break
        
        return components
    
    def _most_common(self, items: List[str]) -> Optional[str]:
        """Find the most common item in a list"""
        if not items:
            return None
        
        counter = Counter(items)
        most_common = counter.most_common(1)
        return most_common[0][0] if most_common else None
    
    def generate_new_id(self, analysis: IDPatternAnalysis, suffix: str = "NEW") -> str:
        """Generate a new test case ID based on the analysis"""
        return analysis.generate_new_id(suffix)
    
    def validate_id_format(self, test_id: str, analysis: IDPatternAnalysis) -> bool:
        """Validate if a test ID matches the detected pattern"""
        if not analysis.pattern:
            return False
        
        try:
            return bool(re.match(analysis.pattern, test_id, re.IGNORECASE))
        except re.error:
            return False
"""
Step Reference Finder

Finds existing test steps that reference specific fields or terms.
Used to identify steps that need to be deleted when fields are removed from STTM.
"""

import re
import logging
from typing import List, Dict, Any, Set, Optional
from models.test_models import TestCase, TestStep


class StepReferenceFinder:
    """Finds test steps that reference specific fields, tabs, or other STTM elements"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def find_steps_referencing_field(self, test_case: TestCase, field_name: str) -> List[Dict[str, Any]]:
        """Find steps that reference a specific field name"""
        if not field_name or not field_name.strip():
            return []
        
        referenced_steps = []
        
        for step in test_case.test_steps:
            if self._step_references_field(step, field_name):
                referenced_steps.append({
                    'step_number': step.step_number,
                    'description': step.description,
                    'expected_result': step.expected_result or '',
                    'reference_type': 'field_reference',
                    'referenced_field': field_name,
                    'match_locations': self._get_field_match_locations(step, field_name)
                })
        
        if referenced_steps:
            self.logger.info(f"Found {len(referenced_steps)} steps referencing field '{field_name}' in test case {test_case.id}")
        
        return referenced_steps
    
    def find_steps_referencing_multiple_fields(self, test_case: TestCase, field_names: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Find steps that reference any of the specified field names"""
        results = {}
        
        for field_name in field_names:
            if field_name and field_name.strip():
                steps = self.find_steps_referencing_field(test_case, field_name.strip())
                if steps:
                    results[field_name] = steps
        
        return results
    
    def find_steps_referencing_deleted_fields(self, test_case: TestCase, deleted_mappings: List) -> Dict[str, List[Dict[str, Any]]]:
        """Find steps that reference fields that have been deleted"""
        deleted_fields = set()
        
        # Collect all deleted field names
        for mapping in deleted_mappings:
            if hasattr(mapping, 'source_field') and mapping.source_field:
                deleted_fields.add(mapping.source_field.strip())
            if hasattr(mapping, 'target_field') and mapping.target_field:
                deleted_fields.add(mapping.target_field.strip())
        
        self.logger.debug(f"Searching for steps referencing deleted fields: {list(deleted_fields)}")
        
        return self.find_steps_referencing_multiple_fields(test_case, list(deleted_fields))
    
    def _step_references_field(self, step: TestStep, field_name: str) -> bool:
        """Check if a test step references a specific field name (exact match or plural forms)"""
        if not field_name or not field_name.strip():
            return False
        
        field_name = field_name.strip()
        
        # Combine step description and expected result for searching
        step_text = f"{step.description} {step.expected_result or ''}"
        
        # Create patterns for exact match and common plural forms
        patterns = [
            r'\b' + re.escape(field_name) + r'\b',           # Exact match: SpinId
            r'\b' + re.escape(field_name) + r's\b',          # Plural with 's': SpinIds  
            r'\b' + re.escape(field_name) + r'S\b'           # Plural with 'S': SpinIDs
        ]
        
        # Check if any pattern matches (case-insensitive)
        for pattern in patterns:
            if re.search(pattern, step_text, re.IGNORECASE):
                return True
        
        return False
    
    def _get_field_match_locations(self, step: TestStep, field_name: str) -> List[str]:
        """Get locations where field name is found in the step (exact match or plural forms)"""
        locations = []
        
        # Create patterns for exact match and common plural forms
        patterns = [
            r'\b' + re.escape(field_name) + r'\b',           # Exact match: SpinId
            r'\b' + re.escape(field_name) + r's\b',          # Plural with 's': SpinIds  
            r'\b' + re.escape(field_name) + r'S\b'           # Plural with 'S': SpinIDs
        ]
        
        # Check description
        for pattern in patterns:
            if re.search(pattern, step.description, re.IGNORECASE):
                locations.append('description')
                break
        
        # Check expected result
        if step.expected_result:
            for pattern in patterns:
                if re.search(pattern, step.expected_result, re.IGNORECASE):
                    locations.append('expected_result')
                    break
        
        return locations
    
    def find_steps_for_modification(self, test_case: TestCase, modified_field: str) -> List[Dict[str, Any]]:
        """Find all steps that should be modified for a changed field"""
        candidates = self.find_steps_referencing_field(test_case, modified_field)
        
        if not candidates:
            return []
        
        # Return all candidates - modify all steps that reference the field
        # This ensures comprehensive test coverage for field changes
        self.logger.info(f"Found {len(candidates)} steps to modify for field '{modified_field}' in test case {test_case.id}")
        return candidates
    
    def _calculate_modification_score(self, step_data: Dict[str, Any], field_name: str) -> int:
        """Calculate score for how suitable a step is for modification"""
        score = 0
        
        # Prefer steps that reference the field in expected result (validation steps)
        if 'expected_result' in step_data['match_locations']:
            score += 10
        
        # Prefer steps that reference the field in description (action steps)
        if 'description' in step_data['match_locations']:
            score += 5
        
        # Prefer steps with shorter descriptions (more focused)
        description_length = len(step_data.get('description', ''))
        if description_length < 100:
            score += 3
        elif description_length < 200:
            score += 1
        
        # Prefer steps that appear to be validation steps
        validation_keywords = ['verify', 'validate', 'check', 'confirm', 'ensure']
        description_lower = step_data.get('description', '').lower()
        for keyword in validation_keywords:
            if keyword in description_lower:
                score += 2
                break
        
        return score
    
    def get_reference_summary(self, test_case: TestCase, sttm_changes: Dict[str, List]) -> Dict[str, Any]:
        """Get comprehensive summary of field references for all STTM changes"""
        summary = {
            'test_case_id': test_case.id,
            'test_case_name': test_case.name,
            'total_steps': len(test_case.test_steps),
            'references_found': {}
        }
        
        # Check deleted fields
        if 'deleted' in sttm_changes:
            deleted_refs = self.find_steps_referencing_deleted_fields(test_case, sttm_changes['deleted'])
            if deleted_refs:
                summary['references_found']['deleted_fields'] = deleted_refs
        
        # Check modified fields
        if 'modified' in sttm_changes:
            modified_refs = {}
            for mapping in sttm_changes['modified']:
                if hasattr(mapping, 'source_field') and mapping.source_field:
                    step_ref = self.find_steps_for_modification(test_case, mapping.source_field)
                    if step_ref:
                        modified_refs[mapping.source_field] = step_ref
                if hasattr(mapping, 'target_field') and mapping.target_field:
                    step_ref = self.find_steps_for_modification(test_case, mapping.target_field)
                    if step_ref:
                        modified_refs[mapping.target_field] = step_ref
            
            if modified_refs:
                summary['references_found']['modified_fields'] = modified_refs
        
        # Log summary
        total_references = sum(len(refs) if isinstance(refs, list) else 1 
                             for refs in summary['references_found'].values() 
                             for refs in (refs.values() if isinstance(refs, dict) else [refs]))
        
        self.logger.info(f"Reference summary for {test_case.id}: {total_references} field references found")
        
        return summary
    
    def validate_field_references(self, test_case: TestCase, field_name: str) -> bool:
        """Validate that field references are found correctly (for testing)"""
        references = self.find_steps_referencing_field(test_case, field_name)
        
        # Manual validation - check each reference
        for ref in references:
            step_num = ref['step_number']
            step = next((s for s in test_case.test_steps if s.step_number == step_num), None)
            if not step:
                self.logger.error(f"Validation failed: Step {step_num} not found in test case")
                return False
            
            if not self._step_references_field(step, field_name):
                self.logger.error(f"Validation failed: Step {step_num} does not actually reference '{field_name}'")
                return False
        
        return True
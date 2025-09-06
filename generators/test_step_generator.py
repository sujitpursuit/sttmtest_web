"""
Test Step Generator

Core engine for generating test step modifications based on STTM changes.
Implements the confirmed approach:
- ADD: New verification steps for deleted fields and validation steps for added fields
- MODIFY: Update existing steps that reference modified fields
- DELETE: Flag existing steps that reference deleted fields for removal
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.sttm_models import STTMTab, STTMMapping
from models.test_models import TestCase
from models.impact_models import ImpactAnalysisReport, TabImpactSummary, TestCaseImpactAssessment
from templates.step_templates import StepTemplates, GeneratedTestStep
from generators.step_reference_finder import StepReferenceFinder


class TestStepGenerator:
    """Generates test step modifications based on STTM changes and impact analysis results"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.templates = StepTemplates()
        self.reference_finder = StepReferenceFinder(logger)
    
    def generate_test_modifications(self, impact_report: ImpactAnalysisReport, 
                                  test_cases: List[TestCase]) -> List[GeneratedTestStep]:
        """Generate all test step modifications from impact analysis results"""
        
        self.logger.info("Starting test step generation from impact analysis results")
        start_time = datetime.now()
        
        all_generated_steps = []
        test_case_lookup = {tc.id: tc for tc in test_cases}
        
        # Process each tab's impact summary
        for tab_summary in impact_report.tab_summaries:
            self.logger.info(f"Generating steps for tab: {tab_summary.tab_name}")
            
            # Get the STTM tab data (need to reconstruct from summary)
            sttm_tab = self._reconstruct_sttm_tab_from_summary(tab_summary)
            
            # Process all impacted test cases for this tab
            all_assessments = (tab_summary.critical_impact_tests + 
                             tab_summary.high_impact_tests + 
                             tab_summary.medium_impact_tests + 
                             tab_summary.low_impact_tests)
            
            for assessment in all_assessments:
                if assessment.test_case_id in test_case_lookup:
                    test_case = test_case_lookup[assessment.test_case_id]
                    generated_steps = self._generate_steps_for_test_case(
                        test_case, sttm_tab, assessment
                    )
                    all_generated_steps.extend(generated_steps)
        
        duration = datetime.now() - start_time
        self.logger.info(f"Generated {len(all_generated_steps)} test step modifications in {duration.total_seconds():.2f} seconds")
        
        return all_generated_steps
    
    def _reconstruct_sttm_tab_from_summary(self, tab_summary: TabImpactSummary) -> STTMTab:
        """Reconstruct STTM tab data from impact summary (limited data available)"""
        # Note: This is a simplified reconstruction since we don't have full STTM data in the summary
        # In a full implementation, we'd pass the original STTM document to have complete mapping details
        
        from models.sttm_models import TabChangeCategory
        
        # Determine change category from summary
        change_category = TabChangeCategory.MIXED  # Default, could be inferred from change_type
        if hasattr(tab_summary, 'change_type'):
            if tab_summary.change_type == 'modifications_only':
                change_category = TabChangeCategory.MODIFICATIONS_ONLY
        
        return STTMTab(
            name=tab_summary.tab_name,
            change_category=change_category,
            # Note: We don't have detailed mapping data in the summary
            # This is a limitation that would be resolved by passing the full STTM document
            added_mappings=[],
            deleted_mappings=[],
            modified_mappings=[]
        )
    
    def _generate_steps_for_test_case(self, test_case: TestCase, sttm_tab: STTMTab, 
                                    assessment: TestCaseImpactAssessment) -> List[GeneratedTestStep]:
        """Generate test step modifications for a specific test case"""
        
        generated_steps = []
        next_step_number = self._get_next_available_step_number(test_case)
        
        self.logger.info(f"Generating steps for test case {test_case.id}, starting from step {next_step_number}")
        
        # Note: Since we don't have detailed STTM mapping data in the assessment,
        # we'll use a simplified approach based on the change summary and scoring reasons
        
        # Extract change information from the assessment
        change_info = self._extract_change_info_from_assessment(assessment)
        self.logger.info(f"Extracted change info: {change_info}")
        
        # Generate steps for deleted fields
        for deleted_field in change_info.get('deleted_fields', []):
            # Generate verification step for deleted field
            verification_step = self.templates.generate_deleted_field_step(
                field_name=deleted_field,
                target_entity=self._extract_target_entity(assessment),
                step_number=next_step_number
            )
            generated_steps.append(verification_step)
            next_step_number += 1
            
            # Find existing steps that reference this deleted field for deletion
            deletion_steps = self._generate_deletion_flags_for_field(test_case, deleted_field)
            generated_steps.extend(deletion_steps)
        
        # Generate steps for added fields
        for added_field in change_info.get('added_fields', []):
            # Create a mock mapping for the added field
            mock_mapping = self._create_mock_mapping_for_field(added_field, assessment)
            added_step = self.templates.generate_added_field_step(
                mapping=mock_mapping,
                step_number=next_step_number
            )
            generated_steps.append(added_step)
            next_step_number += 1
        
        # Generate modifications for existing steps
        for modified_field in change_info.get('modified_fields', []):
            modification_steps = self._generate_modification_for_field(
                test_case, modified_field, assessment
            )
            if modification_steps:
                generated_steps.extend(modification_steps)
        
        self.logger.debug(f"Generated {len(generated_steps)} steps for test case {test_case.id}")
        return generated_steps
    
    def _extract_change_info_from_assessment(self, assessment: TestCaseImpactAssessment) -> Dict[str, List[str]]:
        """Extract field change information from impact assessment scoring reasons"""
        change_info = {
            'deleted_fields': [],
            'modified_fields': [], 
            'added_fields': []
        }
        
        # Parse scoring reasons to extract field information
        self.logger.debug(f"Analyzing {len(assessment.impact_score.scoring_reasons)} scoring reasons for {assessment.test_case_id}")
        
        for reason in assessment.impact_score.scoring_reasons:
            evidence = reason.evidence or ''
            reason_text = reason.reason or ''
            
            self.logger.debug(f"Processing reason: '{reason_text}' with evidence: '{evidence}'")
            
            if 'field(s) were deleted' in reason_text.lower():
                # Extract deleted fields from evidence like "Deleted fields: ['PostCode']"
                fields = self._extract_fields_from_evidence(evidence, 'deleted')
                self.logger.debug(f"Extracted deleted fields: {fields}")
                change_info['deleted_fields'].extend(fields)
            
            elif 'field(s) were modified' in reason_text.lower():
                # Extract modified fields from evidence like "Modified fields: ['OnHoldStatus', 'IsPrimary']"
                fields = self._extract_fields_from_evidence(evidence, 'modified')
                self.logger.debug(f"Extracted modified fields: {fields}")
                change_info['modified_fields'].extend(fields)
            
            elif 'field(s) were added' in reason_text.lower():
                # Extract added fields from evidence like "Added fields: ['LineThree', 'LineFour']"
                fields = self._extract_fields_from_evidence(evidence, 'added')
                self.logger.debug(f"Extracted added fields: {fields}")
                change_info['added_fields'].extend(fields)
            
            elif 'field name references' in reason_text.lower():
                # Extract field references from evidence like "Test references changed field names: VIN"
                fields = self._extract_field_references(evidence)
                self.logger.debug(f"Extracted field references: {fields}")
                # These are typically modified fields being referenced
                change_info['modified_fields'].extend(fields)
        
        # Remove duplicates
        for key in change_info:
            change_info[key] = list(set(change_info[key]))
        
        return change_info
    
    def _extract_fields_from_evidence(self, evidence: str, change_type: str) -> List[str]:
        """Extract field names from evidence strings like "Deleted fields: ['PostCode']" """
        import re
        
        # Look for patterns like ['field1', 'field2'] or ["field1", "field2"]
        pattern = r'\[([^\]]+)\]'
        match = re.search(pattern, evidence)
        
        if match:
            fields_str = match.group(1)
            # Extract individual field names, handling quotes
            field_pattern = r"['\"]([^'\"]+)['\"]"
            fields = re.findall(field_pattern, fields_str)
            return [f.strip() for f in fields if f.strip()]
        
        return []
    
    def _extract_field_references(self, evidence: str) -> List[str]:
        """Extract field references from evidence strings"""
        # Look for patterns after 'field name references:' or similar
        import re
        
        # Pattern like "Test references changed field names: ZipCode"
        pattern = r'field names?\s*:\s*([^\s,]+)'
        match = re.search(pattern, evidence, re.IGNORECASE)
        
        if match:
            return [match.group(1).strip()]
        
        return []
    
    def _extract_target_entity(self, assessment: TestCaseImpactAssessment) -> str:
        """Extract target entity from assessment context"""
        # Try to extract from tab name or use generic fallback
        tab_name = assessment.sttm_tab_name
        
        if 'vendor' in tab_name.lower():
            return 'Vendor system'
        elif 'netsuite' in tab_name.lower():
            return 'NetSuite system'
        elif 'd365' in tab_name.lower():
            return 'D365 system'
        else:
            return 'target system'
    
    def _create_mock_mapping_for_field(self, field_name: str, assessment: TestCaseImpactAssessment) -> STTMMapping:
        """Create a mock STTM mapping for added field (limited information available)"""
        from models.sttm_models import ChangeType
        
        return STTMMapping(
            source_field=field_name,
            target_field=f"target_{field_name}",  # Generic target field name
            change_type=ChangeType.ADDED,
            target_entity=self._extract_target_entity(assessment)
        )
    
    def _generate_deletion_flags_for_field(self, test_case: TestCase, deleted_field: str) -> List[GeneratedTestStep]:
        """Generate deletion flags for existing steps that reference a deleted field"""
        
        referenced_steps = self.reference_finder.find_steps_referencing_field(test_case, deleted_field)
        deletion_steps = []
        
        for step_data in referenced_steps:
            deletion_step = self.templates.create_deletion_flag_step(step_data, deleted_field)
            deletion_steps.append(deletion_step)
        
        if deletion_steps:
            self.logger.info(f"Flagged {len(deletion_steps)} existing steps for deletion (reference deleted field '{deleted_field}')")
        
        return deletion_steps
    
    def _generate_modification_for_field(self, test_case: TestCase, modified_field: str,
                                       assessment: TestCaseImpactAssessment) -> List[GeneratedTestStep]:
        """Generate modifications for all existing steps that reference a modified field"""
        
        # Find all steps to modify
        steps_to_modify = self.reference_finder.find_steps_for_modification(test_case, modified_field)
        
        if not steps_to_modify:
            self.logger.debug(f"No existing steps found to modify for field '{modified_field}'")
            return []
        
        # Extract change details from assessment (simplified)
        change_details = self._extract_modification_details(modified_field, assessment)
        
        # Generate modification steps for all matching steps
        modification_steps = []
        for step_to_modify in steps_to_modify:
            modification_step = self.templates.generate_modified_field_step(
                field_name=modified_field,
                change_details=change_details,
                step_number=step_to_modify['step_number'],
                existing_step_data=step_to_modify
            )
            modification_steps.append(modification_step)
        
        return modification_steps
    
    def _extract_modification_details(self, field_name: str, assessment: TestCaseImpactAssessment) -> Dict[str, Any]:
        """Extract modification details from assessment for a specific field"""
        # This is simplified since we don't have detailed change information in the assessment
        # In a full implementation, we'd have access to the detailed STTM mapping changes
        
        # Look through matches_found for specific field changes
        for match in assessment.impact_score.matches_found:
            if match.matched_text == field_name:
                # Try to infer change type from reasoning
                reasoning = match.reasoning or ''
                if 'sample' in reasoning.lower():
                    # Sample data change
                    return {
                        'source_sample_data': {
                            'old_value': 'previous sample value',
                            'new_value': 'updated sample value'
                        }
                    }
        
        # Default to general modification
        return {
            'general_modification': {
                'old_value': 'previous value',
                'new_value': 'updated value'
            }
        }
    
    def _get_next_available_step_number(self, test_case: TestCase) -> int:
        """Get the next available step number for a test case"""
        if not test_case.test_steps:
            return 1
        
        max_step = max(step.step_number for step in test_case.test_steps)
        return max_step + 1
    
    def generate_summary_report(self, generated_steps: List[GeneratedTestStep]) -> Dict[str, Any]:
        """Generate summary report of all generated test steps"""
        
        summary = {
            'generation_timestamp': datetime.now().isoformat(),
            'total_steps_generated': len(generated_steps),
            'action_breakdown': {
                'ADD': 0,
                'MODIFY': 0,
                'DELETE': 0
            },
            'step_types': {
                'deleted_field_verification': 0,
                'added_field_validation': 0,
                'modified_field_update': 0,
                'deletion_flags': 0
            }
        }
        
        for step in generated_steps:
            # Count by action
            summary['action_breakdown'][step.action] += 1
            
            # Count by type (inferred from notes/description)
            if step.action == 'DELETE':
                summary['step_types']['deletion_flags'] += 1
            elif 'deleted field' in step.notes.lower():
                summary['step_types']['deleted_field_verification'] += 1
            elif 'new field mapping' in step.notes.lower():
                summary['step_types']['added_field_validation'] += 1
            elif step.action == 'MODIFY':
                summary['step_types']['modified_field_update'] += 1
        
        self.logger.info(f"Generation summary: {summary['total_steps_generated']} steps "
                        f"(ADD: {summary['action_breakdown']['ADD']}, "
                        f"MODIFY: {summary['action_breakdown']['MODIFY']}, "
                        f"DELETE: {summary['action_breakdown']['DELETE']})")
        
        return summary
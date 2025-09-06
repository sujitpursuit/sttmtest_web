"""
Test Step Templates

Provides standardized templates for generating test step descriptions and expected results
based on different types of STTM changes (added, deleted, modified fields).
"""

from typing import Dict, Any
from dataclasses import dataclass
from models.sttm_models import STTMMapping


@dataclass
class GeneratedTestStep:
    """Represents a generated test step with all required information"""
    step_number: int
    description: str
    expected_result: str
    action: str  # ADD, MODIFY, DELETE
    notes: str = ""
    original_step_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.original_step_data is None:
            self.original_step_data = {}


class StepTemplates:
    """Template generator for different types of test step modifications"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize all step templates"""
        return {
            'deleted_field_verification': {
                'description': "Verify {field_name} field has been removed from {target_entity}",
                'expected': "{field_name} field should not exist in target system",
                'notes': "Verification step for deleted field: {field_name}"
            },
            'added_field_validation': {
                'description': "Validate {source_field} mapping to {target_field} field",
                'expected': "{source_field} value correctly mapped to {target_entity}.{target_field}",
                'notes': "New field mapping validation: {source_field} → {target_field}"
            },
            'modified_field_update': {
                'description': "Validate updated {field_name} with new {change_type}",
                'expected': "Field {field_name} reflects changes: {old_value} → {new_value}",
                'notes': "Updated validation for modified field: {field_name}"
            },
            'sample_data_change': {
                'description': "Validate {field_name} with updated sample data",
                'expected': "{field_name} contains new sample value: {new_sample_data}",
                'notes': "Sample data change for field: {field_name}"
            },
            'type_change': {
                'description': "Validate {field_name} type change from {old_type} to {new_type}",
                'expected': "{field_name} field accepts {new_type} values and rejects {old_type} format",
                'notes': "Type validation for field: {field_name} ({old_type} → {new_type})"
            },
            'default_value_change': {
                'description': "Validate {field_name} default value change",
                'expected': "{field_name} defaults to '{new_default}' when not specified",
                'notes': "Default value change for field: {field_name}"
            }
        }
    
    def generate_deleted_field_step(self, field_name: str, target_entity: str, 
                                   step_number: int) -> GeneratedTestStep:
        """Generate verification step for deleted field"""
        template = self.templates['deleted_field_verification']
        
        return GeneratedTestStep(
            step_number=step_number,
            description=template['description'].format(
                field_name=field_name,
                target_entity=target_entity
            ),
            expected_result=template['expected'].format(
                field_name=field_name
            ),
            action="ADD",
            notes=template['notes'].format(field_name=field_name)
        )
    
    def generate_added_field_step(self, mapping: STTMMapping, 
                                 step_number: int) -> GeneratedTestStep:
        """Generate validation step for added field"""
        template = self.templates['added_field_validation']
        
        # Get target entity, fallback to target field if not available
        target_entity = getattr(mapping, 'target_entity', mapping.target_field) or 'target system'
        
        return GeneratedTestStep(
            step_number=step_number,
            description=template['description'].format(
                source_field=mapping.source_field,
                target_field=mapping.target_field
            ),
            expected_result=template['expected'].format(
                source_field=mapping.source_field,
                target_entity=target_entity,
                target_field=mapping.target_field
            ),
            action="ADD",
            notes=template['notes'].format(
                source_field=mapping.source_field,
                target_field=mapping.target_field
            )
        )
    
    def generate_modified_field_step(self, field_name: str, change_details: Dict[str, Any],
                                   step_number: int, existing_step_data: Dict[str, Any] = None) -> GeneratedTestStep:
        """Generate modification step for changed field"""
        
        # Determine the type of modification
        if 'source_sample_data' in change_details:
            return self._generate_sample_data_change_step(
                field_name, change_details, step_number, existing_step_data
            )
        elif 'source_type' in change_details:
            return self._generate_type_change_step(
                field_name, change_details, step_number, existing_step_data
            )
        elif 'source_description' in change_details and 'default' in str(change_details.get('source_description', '')).lower():
            return self._generate_default_change_step(
                field_name, change_details, step_number, existing_step_data
            )
        else:
            # General modification
            return self._generate_general_modification_step(
                field_name, change_details, step_number, existing_step_data
            )
    
    def _generate_sample_data_change_step(self, field_name: str, change_details: Dict[str, Any],
                                        step_number: int, existing_step_data: Dict[str, Any]) -> GeneratedTestStep:
        """Generate step for sample data changes"""
        template = self.templates['sample_data_change']
        
        old_sample = change_details['source_sample_data'].get('old_value', '')
        new_sample = change_details['source_sample_data'].get('new_value', '')
        
        return GeneratedTestStep(
            step_number=step_number,
            description=existing_step_data.get('description', template['description'].format(field_name=field_name)),
            expected_result=template['expected'].format(
                field_name=field_name,
                new_sample_data=new_sample
            ),
            action="MODIFY",
            notes=f"Sample data change: '{old_sample}' → '{new_sample}'",
            original_step_data=existing_step_data
        )
    
    def _generate_type_change_step(self, field_name: str, change_details: Dict[str, Any],
                                 step_number: int, existing_step_data: Dict[str, Any]) -> GeneratedTestStep:
        """Generate step for field type changes"""
        template = self.templates['type_change']
        
        old_type = change_details['source_type'].get('old_value', '')
        new_type = change_details['source_type'].get('new_value', '')
        
        return GeneratedTestStep(
            step_number=step_number,
            description=template['description'].format(
                field_name=field_name,
                old_type=old_type,
                new_type=new_type
            ),
            expected_result=template['expected'].format(
                field_name=field_name,
                new_type=new_type,
                old_type=old_type
            ),
            action="MODIFY",
            notes=template['notes'].format(
                field_name=field_name,
                old_type=old_type,
                new_type=new_type
            ),
            original_step_data=existing_step_data
        )
    
    def _generate_default_change_step(self, field_name: str, change_details: Dict[str, Any],
                                    step_number: int, existing_step_data: Dict[str, Any]) -> GeneratedTestStep:
        """Generate step for default value changes"""
        template = self.templates['default_value_change']
        
        # Extract default values from description change
        old_desc = change_details.get('source_description', {}).get('old_value', '')
        new_desc = change_details.get('source_description', {}).get('new_value', '')
        
        # Try to extract default values
        old_default = self._extract_default_value(old_desc)
        new_default = self._extract_default_value(new_desc)
        
        return GeneratedTestStep(
            step_number=step_number,
            description=template['description'].format(field_name=field_name),
            expected_result=template['expected'].format(
                field_name=field_name,
                new_default=new_default
            ),
            action="MODIFY",
            notes=f"Default value change: {old_default} → {new_default}",
            original_step_data=existing_step_data
        )
    
    def _generate_general_modification_step(self, field_name: str, change_details: Dict[str, Any],
                                          step_number: int, existing_step_data: Dict[str, Any]) -> GeneratedTestStep:
        """Generate general modification step"""
        template = self.templates['modified_field_update']
        
        # Build change summary
        changes = []
        for field, change_data in change_details.items():
            if isinstance(change_data, dict) and 'old_value' in change_data:
                changes.append(f"{field}: {change_data['old_value']} → {change_data['new_value']}")
        
        change_summary = '; '.join(changes) if changes else 'field modifications'
        
        return GeneratedTestStep(
            step_number=step_number,
            description=self._append_to_description(
                existing_step_data.get('description', ''),
                template['description'].format(field_name=field_name, change_type='modifications'),
                field_name
            ),
            expected_result=self._append_to_expected_result(
                existing_step_data.get('expected_result', ''),
                template['expected'].format(
                    field_name=field_name,
                    old_value='previous values',
                    new_value='updated values'
                )
            ),
            action="MODIFY",
            notes=f"Field modifications: {change_summary}",
            original_step_data=existing_step_data
        )
    
    def _append_to_description(self, existing_description: str, template_description: str, field_name: str) -> str:
        """Append modification info to existing description or use template"""
        if existing_description:
            return f"{existing_description} [MODIFIED: {field_name} field updated]"
        else:
            return template_description
    
    def _append_to_expected_result(self, existing_expected: str, template_expected: str) -> str:
        """Append modification info to existing expected result or use template"""
        if existing_expected:
            return f"{existing_expected}\n[MODIFIED] {template_expected}"
        else:
            return template_expected
    
    def _extract_default_value(self, description: str) -> str:
        """Extract default value from description text"""
        import re
        
        # Look for patterns like "Defaulted in Gateway to 5" or "default = 7"
        patterns = [
            r'defaulted.*?to\s+(\w+)',
            r'default.*?=\s*(\w+)',
            r'defaults?\s+to\s+[\'"]?(\w+)[\'"]?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'value not specified'
    
    def create_deletion_flag_step(self, existing_step: Dict[str, Any], 
                                 deleted_field: str) -> GeneratedTestStep:
        """Create step marked for deletion because it references deleted field"""
        return GeneratedTestStep(
            step_number=existing_step.get('step_number', 0),
            description=existing_step.get('description', ''),
            expected_result=existing_step.get('expected_result', ''),
            action="DELETE",
            notes=f"Step references deleted field '{deleted_field}' - should be removed",
            original_step_data=existing_step
        )
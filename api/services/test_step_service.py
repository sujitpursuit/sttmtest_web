"""
Test Step Service for FastAPI

Provides test step generation functionality through the API.
Wraps the existing TestStepGenerator to provide API-friendly interfaces.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json

from generators.test_step_generator import TestStepGenerator
from generators.test_modification_exporter import TestModificationExporter
from models.impact_models import ImpactAnalysisReport
from models.test_models import TestCase
from templates.step_templates import GeneratedTestStep
from api.utils.exceptions import TestStepGenerationError


class TestStepService:
    """Service for managing test step generation through the API"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.generator = TestStepGenerator(self.logger)
        self.exporter = TestModificationExporter(output_dir="output_files", logger=self.logger)
        self.output_dir = "output_files"
        
    def generate_test_steps(self, impact_report: ImpactAnalysisReport, 
                          test_cases: List[TestCase], 
                          generation_mode: str = "delta") -> Dict[str, Any]:
        """
        Generate test steps based on impact analysis results
        
        Args:
            impact_report: Impact analysis results
            test_cases: List of test cases to process
            generation_mode: "delta" for new steps only, "in_place" for full test case updates
            
        Returns:
            Dictionary containing generated steps and metadata
        """
        try:
            self.logger.info(f"Starting test step generation in {generation_mode} mode")
            start_time = datetime.now()
            
            # Generate test step modifications
            generated_steps = self.generator.generate_test_modifications(impact_report, test_cases)
            
            # Create generation metadata
            generation_metadata = {
                "generation_timestamp": start_time.isoformat(),
                "generation_mode": generation_mode,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "total_test_cases_processed": len(test_cases),
                "total_steps_generated": len(generated_steps)
            }
            
            # Generate summary report
            summary_report = self.generator.generate_summary_report(generated_steps)
            
            if generation_mode == "delta":
                # Return just the generated steps
                result = {
                    "generation_mode": "delta",
                    "generated_steps": [self._serialize_generated_step(step) for step in generated_steps],
                    "summary": summary_report,
                    "metadata": generation_metadata
                }
            else:
                # Return updated test cases with steps integrated
                updated_test_cases = self._integrate_steps_into_test_cases(
                    test_cases, generated_steps
                )
                result = {
                    "generation_mode": "in_place",
                    "updated_test_cases": [self._serialize_test_case(tc) for tc in updated_test_cases],
                    "generated_steps": [self._serialize_generated_step(step) for step in generated_steps],
                    "summary": summary_report,
                    "metadata": generation_metadata
                }
            
            self.logger.info(f"Generated {len(generated_steps)} test steps in {generation_metadata['duration_seconds']:.2f} seconds")
            return result
            
        except Exception as e:
            self.logger.error(f"Test step generation failed: {str(e)}", exc_info=True)
            raise TestStepGenerationError(f"Test step generation failed: {str(e)}")
    
    def save_generated_steps(self, generated_steps_data: Dict[str, Any], 
                           qtest_file: Optional[str] = None,
                           filename: Optional[str] = None) -> str:
        """
        Save generated test steps as Excel file using TestModificationExporter
        
        Args:
            generated_steps_data: Generated steps data to save
            qtest_file: Path to original QTEST file (required for Excel generation)
            filename: Optional custom filename
            
        Returns:
            Path to saved Excel file
        """
        try:
            # Extract generated steps from the data
            generated_steps_list = generated_steps_data.get("generated_steps", [])
            generation_mode = generated_steps_data.get("generation_mode", "delta")
            
            if not generated_steps_list:
                self.logger.warning("No generated steps found in data")
                return ""
            
            # Convert serialized steps back to GeneratedTestStep objects
            from templates.step_templates import GeneratedTestStep
            
            steps_objects = []
            for step_data in generated_steps_list:
                step = GeneratedTestStep(
                    step_number=step_data.get('step_number', 1),
                    description=step_data.get('action_description', ''),
                    expected_result=step_data.get('expected_result', ''),
                    action=step_data.get('action', 'ADD'),
                    notes=step_data.get('notes', '')
                )
                # Add any additional attributes
                if 'field_name' in step_data:
                    step.field_name = step_data['field_name']
                if 'change_type' in step_data:
                    step.change_type = step_data['change_type']
                steps_objects.append(step)
            
            self.logger.info(f"Converting {len(steps_objects)} steps to Excel format")
            
            # Use TestModificationExporter to generate Excel file
            if qtest_file and os.path.exists(qtest_file):
                if generation_mode == "delta":
                    # For delta mode, export with original test data
                    output_file = self.exporter.export_with_original_test_data(steps_objects, qtest_file)
                    # Add instructions sheet for delta files
                    if output_file:
                        self.exporter.create_instructions_sheet(output_file)
                else:
                    # For in-place mode, copy and modify original
                    output_file = self.exporter.copy_and_modify_original(steps_objects, qtest_file)
                    
                self.logger.info(f"Generated Excel file: {output_file}")
                return output_file
            else:
                # Fallback: create basic Excel export without original test data
                self.logger.warning(f"QTEST file not found: {qtest_file}. Creating basic export.")
                
                # Create basic test case data structure
                base_test_case_data = {
                    'name': 'Generated Test Case',
                    'id': 'GENERATED_001',
                    'description': 'Auto-generated test case from STTM impact analysis',
                    'precondition': 'System setup completed'
                }
                
                suffix = f"{generation_mode}_mode"
                output_file = self.exporter.export_to_excel(steps_objects, base_test_case_data, suffix)
                
                self.logger.info(f"Generated basic Excel file: {output_file}")
                return output_file
            
        except Exception as e:
            self.logger.error(f"Failed to save generated steps as Excel: {str(e)}", exc_info=True)
            raise TestStepGenerationError(f"Failed to save generated steps as Excel: {str(e)}")
    
    def _serialize_generated_step(self, step: GeneratedTestStep, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Serialize a GeneratedTestStep to dictionary"""
        from datetime import datetime
        
        # Extract context information if provided
        test_case_id = "Unknown"
        sttm_tab_name = "Unknown"
        if context:
            test_case_id = context.get('test_case_id', 'Unknown') 
            sttm_tab_name = context.get('sttm_tab_name', 'Unknown')
        
        return {
            "step_number": step.step_number,
            "action": step.action,
            "action_description": step.description,
            "test_case_id": test_case_id,
            "sttm_tab_name": sttm_tab_name,
            "notes": step.notes if hasattr(step, 'notes') else "",
            "generated_timestamp": datetime.now().isoformat(),
            "field_name": getattr(step, 'field_name', None),
            "change_type": getattr(step, 'change_type', None),
            "expected_result": step.expected_result if hasattr(step, 'expected_result') else ""
        }
    
    def _serialize_test_case(self, test_case: TestCase) -> Dict[str, Any]:
        """Serialize a TestCase to dictionary"""
        return {
            "id": test_case.id,
            "test_name": test_case.name,  # TestCase has 'name' attribute, not 'test_name'
            "total_steps": len(test_case.test_steps),
            "test_steps": [
                {
                    "step_number": step.step_number,
                    "description": step.description,
                    "expected_result": step.expected_result
                }
                for step in test_case.test_steps
            ]
        }
    
    def _integrate_steps_into_test_cases(self, test_cases: List[TestCase], 
                                       generated_steps: List[GeneratedTestStep]) -> List[TestCase]:
        """
        Integrate generated steps into test cases (in-place mode)
        
        This creates updated copies of test cases with generated steps integrated
        """
        # Since template GeneratedTestStep doesn't have test_case_id, 
        # we'll associate all steps with the first test case (common scenario)
        # For more sophisticated association, we'd need to enhance the step generation
        steps_by_test_case = {}
        if test_cases and generated_steps:
            primary_test_case_id = test_cases[0].id
            steps_by_test_case[primary_test_case_id] = generated_steps
        
        updated_test_cases = []
        
        for test_case in test_cases:
            # Create a copy of the test case
            updated_test_case = TestCase(
                id=test_case.id,
                name=test_case.name,
                description=test_case.description,
                precondition=test_case.precondition,
                test_steps=test_case.test_steps.copy() if test_case.test_steps else []
            )
            
            # Add generated steps for this test case
            if test_case.id in steps_by_test_case:
                for generated_step in steps_by_test_case[test_case.id]:
                    if generated_step.action == "ADD":
                        # Convert GeneratedTestStep to TestStep format
                        from models.test_models import TestStep
                        new_step = TestStep(
                            step_number=generated_step.step_number,
                            description=generated_step.description,
                            expected_result=generated_step.expected_result
                        )
                        updated_test_case.test_steps.append(new_step)
                    
                    elif generated_step.action == "MODIFY":
                        # Find and update existing step
                        for existing_step in updated_test_case.test_steps:
                            if existing_step.step_number == generated_step.step_number:
                                existing_step.description = generated_step.description
                                existing_step.expected_result = generated_step.expected_result
                                break
                    
                    elif generated_step.action == "DELETE":
                        # Mark step for deletion (add note instead of actually removing)
                        for existing_step in updated_test_case.test_steps:
                            if existing_step.step_number == generated_step.step_number:
                                existing_step.description = f"[FLAGGED FOR DELETION] {existing_step.description}"
                                break
            
            updated_test_cases.append(updated_test_case)
        
        return updated_test_cases
    
    def get_generation_statistics(self, generated_steps_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics about generated test steps"""
        try:
            summary = generated_steps_data.get("summary", {})
            metadata = generated_steps_data.get("metadata", {})
            
            stats = {
                "total_steps": summary.get("total_steps_generated", 0),
                "actions": summary.get("action_breakdown", {}),
                "step_types": summary.get("step_types", {}),
                "generation_time": metadata.get("duration_seconds", 0),
                "test_cases_processed": metadata.get("total_test_cases_processed", 0),
                "generation_mode": metadata.get("generation_mode", "unknown"),
                "timestamp": metadata.get("generation_timestamp", "")
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get generation statistics: {str(e)}")
            return {"error": str(e)}
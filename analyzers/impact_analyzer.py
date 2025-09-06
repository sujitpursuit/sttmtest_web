"""
Impact Analyzer - Main orchestrator for STTM impact analysis

This module combines STTM parsing, test case parsing, text matching, and impact scoring
to produce comprehensive impact analysis reports.
"""

from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import json

from models.sttm_models import STTMDocument, STTMTab
from models.test_models import QTestDocument, TestCase
from models.impact_models import (
    ImpactAnalysisReport, TabImpactSummary, TestCaseImpactAssessment,
    ImpactAnalysisConfig, ImpactLevel
)
from analyzers.impact_scorer import DataDrivenImpactScorer
from parsers.sttm_parser import STTMParser
from parsers.qtest_parser import QTestParser


class ImpactAnalyzer:
    """Main impact analyzer that orchestrates the complete analysis process"""
    
    def __init__(self, config: ImpactAnalysisConfig, 
                 logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize components
        self.impact_scorer = DataDrivenImpactScorer(config, logger)
        self.sttm_parser = STTMParser(logger)
        self.qtest_parser = QTestParser(logger)
    
    def analyze_impact(self, sttm_file_path: str, qtest_file_path: str) -> ImpactAnalysisReport:
        """Perform complete impact analysis between STTM changes and test cases"""
        
        self.logger.info(f"Starting impact analysis: STTM={sttm_file_path}, QTEST={qtest_file_path}")
        start_time = datetime.now()
        
        # Parse input files
        self.logger.info("Parsing STTM document...")
        sttm_document = self.sttm_parser.parse_file(sttm_file_path)
        
        self.logger.info("Parsing QTEST document...")
        qtest_document = self.qtest_parser.parse_file(qtest_file_path)
        
        self.logger.info(f"Loaded {sttm_document.total_tabs} STTM tabs and {qtest_document.total_test_cases} test cases")
        
        # Create analysis report
        report = ImpactAnalysisReport(
            analysis_timestamp=start_time.isoformat(),
            sttm_file=sttm_file_path,
            qtest_file=qtest_file_path,
            scoring_config=self._config_to_dict(),
            total_sttm_tabs_analyzed=len(sttm_document.changed_tabs),
            total_test_cases_analyzed=qtest_document.total_test_cases,
            total_sttm_changes=sttm_document.total_changes
        )
        
        # Analyze each changed STTM tab against all test cases
        for sttm_tab in sttm_document.changed_tabs:
            self.logger.info(f"Analyzing impact for STTM tab: {sttm_tab.get_display_name()}")
            
            tab_summary = self._analyze_tab_impact(sttm_tab, qtest_document.test_cases)
            report.tab_summaries.append(tab_summary)
        
        # Update report statistics
        report.update_summary_statistics()
        
        # Log completion
        duration = datetime.now() - start_time
        self.logger.info(f"Impact analysis completed in {duration.total_seconds():.2f} seconds")
        self.logger.info(f"Results: {report.total_high_impact + report.total_critical_impact} high-priority impacts found")
        
        return report
    
    def analyze_single_test_case(self, test_case: TestCase, sttm_tab: STTMTab) -> TestCaseImpactAssessment:
        """Analyze impact of a single STTM tab on a single test case"""
        
        # Calculate impact score
        impact_score = self.impact_scorer.calculate_impact(test_case, sttm_tab)
        
        # Find affected step numbers (steps that contain references to changed fields)
        affected_steps = self._find_affected_steps(test_case, sttm_tab)
        
        # Create assessment
        assessment = TestCaseImpactAssessment(
            test_case_id=test_case.id,
            test_case_name=test_case.name,
            sttm_tab_name=sttm_tab.get_display_name(),
            sttm_change_summary=self._create_change_summary(sttm_tab),
            impact_score=impact_score,
            affected_step_numbers=affected_steps,
            processing_timestamp=datetime.now().isoformat(),
            analyzer_version="2.0"
        )
        
        return assessment
    
    def _analyze_tab_impact(self, sttm_tab: STTMTab, test_cases: List[TestCase]) -> TabImpactSummary:
        """Analyze impact of a single STTM tab on all test cases"""
        
        tab_summary = TabImpactSummary(
            tab_name=sttm_tab.get_display_name(),
            change_type=sttm_tab.change_category.value,
            total_changes=sttm_tab.get_total_changes()
        )
        
        # Analyze each test case against this STTM tab
        for test_case in test_cases:
            assessment = self.analyze_single_test_case(test_case, sttm_tab)
            
            # Categorize by impact level
            impact_level = assessment.impact_score.impact_level
            
            if impact_level == ImpactLevel.CRITICAL:
                tab_summary.critical_impact_tests.append(assessment)
            elif impact_level == ImpactLevel.HIGH:
                tab_summary.high_impact_tests.append(assessment)
            elif impact_level == ImpactLevel.MEDIUM:
                tab_summary.medium_impact_tests.append(assessment)
            elif impact_level == ImpactLevel.LOW:
                tab_summary.low_impact_tests.append(assessment)
        
        self.logger.info(f"Tab '{sttm_tab.get_display_name()}': {tab_summary.get_total_affected_tests()} test cases affected")
        
        return tab_summary
    
    def _find_affected_steps(self, test_case: TestCase, sttm_tab: STTMTab) -> List[int]:
        """Find which test steps are affected by STTM changes based on exact field names or tab names"""
        import re
        affected_steps = []
        
        # Collect exact field names that changed (no partial matching)
        exact_field_names = set()
        for mapping in sttm_tab.get_all_changed_mappings():
            if mapping.source_field:
                exact_field_names.add(mapping.source_field)
            if mapping.target_field:
                exact_field_names.add(mapping.target_field)
        
        # Collect exact tab names (both physical and logical)
        exact_tab_names = set()
        if sttm_tab.logical_name:
            exact_tab_names.add(sttm_tab.logical_name)
        if sttm_tab.physical_name_v1:
            exact_tab_names.add(sttm_tab.physical_name_v1)
        if sttm_tab.physical_name_v2:
            exact_tab_names.add(sttm_tab.physical_name_v2)
        # Also add the main tab name
        exact_tab_names.add(sttm_tab.name)
        
        self.logger.debug(f"Searching for exact field names: {list(exact_field_names)}")
        self.logger.debug(f"Searching for exact tab names: {list(exact_tab_names)}")
        
        # Check each test step for exact matches ONLY
        for i, step in enumerate(test_case.test_steps):
            step_text = step.description + " " + (step.expected_result or "")
            step_affected = False
            matched_terms = []
            
            # Check for field name matches - unquoted field names with word boundaries
            for field_name in exact_field_names:
                if field_name:
                    # Field names appear unquoted like: "ConsumerFirstname      String"
                    # Use word boundaries to match exact field names
                    pattern = r'\b' + re.escape(field_name) + r'\b'
                    if re.search(pattern, step_text, re.IGNORECASE):
                        step_affected = True
                        matched_terms.append(f"field '{field_name}'")
            
            # Check for tab name matches (plain text, case-insensitive)
            for tab_name in exact_tab_names:
                if tab_name:
                    # Tab names appear as plain text like "Vendor Inbound DACH VenProxy"
                    if re.search(re.escape(tab_name), step_text, re.IGNORECASE):
                        step_affected = True
                        matched_terms.append(f"tab '{tab_name}'")
            
            if step_affected:
                affected_steps.append(i + 1)  # 1-based step numbering
                self.logger.debug(f"Step {i+1} affected by: {', '.join(matched_terms)}")
        
        # Remove duplicates and sort
        affected_steps = sorted(list(set(affected_steps)))
        
        if affected_steps:
            self.logger.info(f"Identified affected steps for {sttm_tab.get_display_name()}: {affected_steps}")
        else:
            self.logger.debug(f"No specific steps identified for {sttm_tab.get_display_name()}")
        
        return affected_steps
    
    def _create_change_summary(self, sttm_tab: STTMTab) -> str:
        """Create human-readable summary of STTM tab changes"""
        summary_parts = []
        
        if sttm_tab.added_mappings:
            summary_parts.append(f"{len(sttm_tab.added_mappings)} fields added")
        
        if sttm_tab.deleted_mappings:
            summary_parts.append(f"{len(sttm_tab.deleted_mappings)} fields deleted")
        
        if sttm_tab.modified_mappings:
            summary_parts.append(f"{len(sttm_tab.modified_mappings)} fields modified")
        
        if not summary_parts:
            return "No changes detected"
        
        return ", ".join(summary_parts)
    
    def _config_to_dict(self) -> Dict[str, any]:
        """Convert configuration to dictionary for report inclusion"""
        return {
            "tab_name_match_points": self.config.tab_name_match_points,
            "deleted_field_points": self.config.deleted_field_points,
            "modified_field_points": self.config.modified_field_points,
            "added_field_points": self.config.added_field_points,
            "exact_tab_match_points": self.config.exact_tab_match_points,
            "partial_tab_match_points": self.config.partial_tab_match_points,
            "field_name_match_points": self.config.field_name_match_points,
            "sample_data_match_points": self.config.sample_data_match_points,
            "critical_threshold": self.config.critical_threshold,
            "high_threshold": self.config.high_threshold,
            "medium_threshold": self.config.medium_threshold,
            "low_threshold": self.config.low_threshold
        }


class QuickImpactAnalyzer:
    """Simplified analyzer for quick impact checks"""
    
    def __init__(self, config: Optional[ImpactAnalysisConfig] = None):
        self.config = config or ImpactAnalysisConfig()
        self.analyzer = ImpactAnalyzer(self.config)
    
    def quick_check(self, sttm_file: str, qtest_file: str) -> str:
        """Perform quick impact analysis and return summary"""
        
        try:
            report = self.analyzer.analyze_impact(sttm_file, qtest_file)
            return report.get_executive_summary()
        
        except Exception as e:
            return f"Error during impact analysis: {str(e)}"
    
    def get_priority_actions(self, sttm_file: str, qtest_file: str) -> List[str]:
        """Get list of priority actions needed"""
        
        try:
            report = self.analyzer.analyze_impact(sttm_file, qtest_file)
            actions = []
            
            for tab_summary in report.tab_summaries:
                for assessment in tab_summary.get_priority_tests():
                    action = f"Update {assessment.test_case_id}: {assessment.test_case_name}"
                    actions.append(action)
            
            return actions
        
        except Exception as e:
            return [f"Error: {str(e)}"]
    
    def test_scoring_config(self) -> str:
        """Test the current scoring configuration with examples"""
        
        from analyzers.impact_scorer import BusinessFriendlyScorer
        
        business_scorer = BusinessFriendlyScorer(self.config)
        
        explanation = business_scorer.explain_scoring_config()
        explanation += "\n\nEXAMPLE SCENARIOS:\n"
        explanation += "==================\n\n"
        
        # Scenario 1: High impact
        explanation += "Scenario 1 - High Impact Test:\n"
        explanation += business_scorer.get_scoring_preview(
            deleted_fields=1, modified_fields=0, added_fields=0,
            tab_match=True, field_references=1, sample_references=0
        )
        explanation += "\n"
        
        # Scenario 2: Medium impact  
        explanation += "Scenario 2 - Medium Impact Test:\n"
        explanation += business_scorer.get_scoring_preview(
            deleted_fields=0, modified_fields=1, added_fields=0,
            tab_match=False, field_references=1, sample_references=0
        )
        explanation += "\n"
        
        # Scenario 3: Low impact
        explanation += "Scenario 3 - Low Impact Test:\n"
        explanation += business_scorer.get_scoring_preview(
            deleted_fields=0, modified_fields=0, added_fields=2,
            tab_match=False, field_references=0, sample_references=0
        )
        
        return explanation
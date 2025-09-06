"""
Impact Analysis Models - Domain models for impact analysis results

These models represent the results of impact analysis between STTM changes
and test cases, using the simplified scoring algorithm.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class ImpactLevel(Enum):
    """Impact level enumeration"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MatchType(Enum):
    """Type of match between STTM change and test case"""
    EXACT_TAB_MATCH = "exact_tab_match"
    PARTIAL_TAB_MATCH = "partial_tab_match"
    FIELD_NAME_MATCH = "field_name_match"
    SAMPLE_DATA_MATCH = "sample_data_match"
    NO_MATCH = "no_match"


class RecommendedAction(Enum):
    """Recommended actions for test cases based on impact level"""
    UPDATE_IMMEDIATELY = "UPDATE_IMMEDIATELY"
    UPDATE_REQUIRED = "UPDATE_REQUIRED"
    REVIEW_RECOMMENDED = "REVIEW_RECOMMENDED"
    MONITOR = "MONITOR"
    NO_ACTION = "NO_ACTION"


@dataclass
class MatchResult:
    """Result of matching a test case against an STTM change"""
    match_type: MatchType
    confidence_score: float  # 0.0 to 1.0
    matched_text: str       # The actual text that matched
    location: str           # Where the match was found (name, description, step_N)
    reasoning: str          # Human-readable explanation


@dataclass
class ScoringReason:
    """Reason for adding points to impact score"""
    points_added: int
    reason: str
    evidence: str          # The actual text/data that caused this scoring
    rule_name: str         # Name of the scoring rule that applied


@dataclass
class ImpactScore:
    """Complete impact scoring result for a test case"""
    total_points: int
    impact_level: ImpactLevel
    confidence: float               # Overall confidence in the assessment
    scoring_reasons: List[ScoringReason]
    matches_found: List[MatchResult]
    recommended_action: RecommendedAction
    
    def get_explanation(self) -> str:
        """Get human-readable explanation of the score"""
        explanation = f"Impact Score: {self.total_points} points = {self.impact_level.value}\n\n"
        explanation += "Why this score?\n"
        
        for reason in self.scoring_reasons:
            explanation += f"  • {reason.reason} (+{reason.points_added} points)\n"
            if reason.evidence:
                explanation += f"    Evidence: {reason.evidence}\n"
        
        explanation += f"\nRecommended Action: {self.recommended_action.value.replace('_', ' ').title()}"
        return explanation


@dataclass
class TestCaseImpactAssessment:
    """Complete impact assessment for a single test case"""
    test_case_id: str
    test_case_name: str
    sttm_tab_name: str              # The STTM tab that potentially impacts this test
    sttm_change_summary: str        # Brief summary of what changed
    
    impact_score: ImpactScore
    affected_step_numbers: List[int] = field(default_factory=list)
    
    # Additional context
    processing_timestamp: str = ""
    analyzer_version: str = "2.0"
    
    def is_high_impact(self) -> bool:
        """Check if this is high or critical impact"""
        return self.impact_score.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]
    
    def requires_immediate_action(self) -> bool:
        """Check if immediate action is required"""
        return self.impact_score.recommended_action == RecommendedAction.UPDATE_IMMEDIATELY


@dataclass  
class TabImpactSummary:
    """Summary of impact for all test cases affected by a specific STTM tab"""
    tab_name: str
    change_type: str                # "mixed", "additions_only", etc.
    total_changes: int              # Number of field changes in this tab
    
    # Test case impact breakdown
    critical_impact_tests: List[TestCaseImpactAssessment] = field(default_factory=list)
    high_impact_tests: List[TestCaseImpactAssessment] = field(default_factory=list)  
    medium_impact_tests: List[TestCaseImpactAssessment] = field(default_factory=list)
    low_impact_tests: List[TestCaseImpactAssessment] = field(default_factory=list)
    
    def get_total_affected_tests(self) -> int:
        """Get total number of affected test cases"""
        return (len(self.critical_impact_tests) + len(self.high_impact_tests) + 
                len(self.medium_impact_tests) + len(self.low_impact_tests))
    
    def get_priority_tests(self) -> List[TestCaseImpactAssessment]:
        """Get tests that require immediate attention (Critical + High)"""
        return self.critical_impact_tests + self.high_impact_tests


@dataclass
class ImpactAnalysisReport:
    """Complete impact analysis report for all STTM changes"""
    analysis_timestamp: str
    sttm_file: str
    qtest_file: str
    
    # Configuration used
    scoring_config: Dict[str, Any]
    
    # Summary statistics
    total_sttm_tabs_analyzed: int
    total_test_cases_analyzed: int
    total_sttm_changes: int
    
    # Tab-level summaries
    tab_summaries: List[TabImpactSummary] = field(default_factory=list)
    
    # Overall impact breakdown
    total_critical_impact: int = 0
    total_high_impact: int = 0
    total_medium_impact: int = 0
    total_low_impact: int = 0
    total_no_impact: int = 0
    
    def get_executive_summary(self) -> str:
        """Generate executive summary text"""
        total_affected = (self.total_critical_impact + self.total_high_impact + 
                         self.total_medium_impact + self.total_low_impact)
        
        summary = f"EXECUTIVE SUMMARY\n"
        summary += f"================\n"
        summary += f"Total Test Cases Analyzed: {self.total_test_cases_analyzed}\n"
        summary += f"Total STTM Changes: {self.total_sttm_changes}\n"
        summary += f"Test Cases Affected: {total_affected}\n\n"
        
        summary += f"IMPACT BREAKDOWN:\n"
        if self.total_critical_impact > 0:
            summary += f"Critical Impact: {self.total_critical_impact} (requires immediate attention)\n"
        summary += f"High Impact: {self.total_high_impact} (update required)\n"
        summary += f"Medium Impact: {self.total_medium_impact} (review recommended)\n"
        summary += f"Low Impact: {self.total_low_impact} (monitor)\n"
        
        # Top priority actions
        priority_count = self.total_critical_impact + self.total_high_impact
        if priority_count > 0:
            summary += f"\nIMMEDIATE ACTION REQUIRED: {priority_count} test cases need updates\n"
        
        return summary
    
    def get_all_assessments(self) -> List[TestCaseImpactAssessment]:
        """Get all test case assessments across all tabs"""
        all_assessments = []
        for tab_summary in self.tab_summaries:
            all_assessments.extend(tab_summary.critical_impact_tests)
            all_assessments.extend(tab_summary.high_impact_tests)
            all_assessments.extend(tab_summary.medium_impact_tests)
            all_assessments.extend(tab_summary.low_impact_tests)
        return all_assessments
    
    def update_summary_statistics(self):
        """Update summary statistics from tab summaries"""
        self.total_critical_impact = sum(len(tab.critical_impact_tests) for tab in self.tab_summaries)
        self.total_high_impact = sum(len(tab.high_impact_tests) for tab in self.tab_summaries)
        self.total_medium_impact = sum(len(tab.medium_impact_tests) for tab in self.tab_summaries)
        self.total_low_impact = sum(len(tab.low_impact_tests) for tab in self.tab_summaries)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary with detailed test case and step information"""
        return {
            "analysis_metadata": {
                "timestamp": self.analysis_timestamp,
                "sttm_file": self.sttm_file,
                "qtest_file": self.qtest_file,
                "scoring_config": self.scoring_config
            },
            "summary_statistics": {
                "total_sttm_tabs_analyzed": self.total_sttm_tabs_analyzed,
                "total_test_cases_analyzed": self.total_test_cases_analyzed,
                "total_sttm_changes": self.total_sttm_changes,
                "total_critical_impact": self.total_critical_impact,
                "total_high_impact": self.total_high_impact,
                "total_medium_impact": self.total_medium_impact,
                "total_low_impact": self.total_low_impact,
                "total_no_impact": self.total_no_impact
            },
            "executive_summary": self.get_executive_summary(),
            "detailed_tab_analysis": [
                {
                    "tab_name": tab.tab_name,
                    "change_type": tab.change_type,
                    "total_changes": tab.total_changes,
                    "impact_breakdown": {
                        "critical_impact": len(tab.critical_impact_tests),
                        "high_impact": len(tab.high_impact_tests),
                        "medium_impact": len(tab.medium_impact_tests),
                        "low_impact": len(tab.low_impact_tests)
                    },
                    "affected_test_cases": {
                        "critical": [self._assessment_to_dict(tc) for tc in tab.critical_impact_tests],
                        "high": [self._assessment_to_dict(tc) for tc in tab.high_impact_tests],
                        "medium": [self._assessment_to_dict(tc) for tc in tab.medium_impact_tests],
                        "low": [self._assessment_to_dict(tc) for tc in tab.low_impact_tests]
                    }
                }
                for tab in self.tab_summaries
            ]
        }
    
    def _assessment_to_dict(self, assessment: 'TestCaseImpactAssessment') -> Dict[str, Any]:
        """Convert TestCaseImpactAssessment to dictionary"""
        return {
            "test_case_id": assessment.test_case_id,
            "test_case_name": assessment.test_case_name,
            "sttm_tab_name": assessment.sttm_tab_name,
            "sttm_change_summary": assessment.sttm_change_summary,
            "impact_score": {
                "total_points": assessment.impact_score.total_points,
                "impact_level": assessment.impact_score.impact_level.value,
                "confidence": assessment.impact_score.confidence,
                "recommended_action": assessment.impact_score.recommended_action.value,
                "scoring_reasons": [
                    {
                        "points_added": reason.points_added,
                        "reason": reason.reason,
                        "evidence": reason.evidence,
                        "rule_name": reason.rule_name
                    } for reason in assessment.impact_score.scoring_reasons
                ],
                "matches_found": [
                    {
                        "match_type": match.match_type.value,
                        "confidence_score": match.confidence_score,
                        "matched_text": match.matched_text,
                        "location": match.location,
                        "reasoning": match.reasoning
                    } for match in assessment.impact_score.matches_found
                ]
            },
            "affected_step_numbers": assessment.affected_step_numbers,
            "processing_timestamp": assessment.processing_timestamp,
            "analyzer_version": assessment.analyzer_version
        }


@dataclass
class ImpactAnalysisConfig:
    """Configuration for the simplified impact analysis"""
    
    # Basic scoring weights (the simple approach)
    tab_name_match_points: int = 3
    deleted_field_points: int = 5
    modified_field_points: int = 3
    added_field_points: int = 1
    
    # Match confidence points
    exact_tab_match_points: int = 2
    partial_tab_match_points: int = 1
    field_name_match_points: int = 2
    sample_data_match_points: int = 3
    
    # Impact level thresholds
    critical_threshold: int = 12
    high_threshold: int = 8
    medium_threshold: int = 4
    low_threshold: int = 0
    
    # Matching sensitivity
    partial_match_min_keywords: int = 1
    case_sensitive_matching: bool = False
    minimum_keyword_length: int = 3
    
    def get_impact_level(self, points: int) -> ImpactLevel:
        """Determine impact level based on points"""
        if points >= self.critical_threshold:
            return ImpactLevel.CRITICAL
        elif points >= self.high_threshold:
            return ImpactLevel.HIGH
        elif points >= self.medium_threshold:
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW
    
    def get_recommended_action(self, impact_level: ImpactLevel) -> RecommendedAction:
        """Get recommended action for impact level"""
        action_map = {
            ImpactLevel.CRITICAL: RecommendedAction.UPDATE_IMMEDIATELY,
            ImpactLevel.HIGH: RecommendedAction.UPDATE_REQUIRED,
            ImpactLevel.MEDIUM: RecommendedAction.REVIEW_RECOMMENDED,
            ImpactLevel.LOW: RecommendedAction.MONITOR
        }
        return action_map.get(impact_level, RecommendedAction.NO_ACTION)
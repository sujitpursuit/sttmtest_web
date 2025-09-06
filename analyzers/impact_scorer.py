"""
Data-Driven Impact Scorer - Simple scoring algorithm based on available data

This module implements the simplified, question-based scoring algorithm that
business users can easily understand and configure.
"""

from typing import List, Dict, Optional
import logging
from datetime import datetime

from models.test_models import TestCase
from models.sttm_models import STTMTab, STTMMapping, ChangeType
from models.impact_models import (
    ImpactScore, ImpactLevel, ScoringReason, MatchResult, 
    RecommendedAction, ImpactAnalysisConfig, MatchType
)
from analyzers.text_matcher import SimpleTextMatcher, MatchResultAnalyzer


class DataDrivenImpactScorer:
    """Simple impact scorer using configurable question-based algorithm"""
    
    def __init__(self, config: ImpactAnalysisConfig, 
                 logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize text matcher and analyzer
        self.text_matcher = SimpleTextMatcher(
            case_sensitive=config.case_sensitive_matching,
            min_keyword_length=config.minimum_keyword_length,
            logger=logger
        )
        self.match_analyzer = MatchResultAnalyzer(logger)
    
    def calculate_impact(self, test_case: TestCase, sttm_tab: STTMTab) -> ImpactScore:
        """Calculate impact score for a test case against an STTM tab"""
        
        total_points = 0
        scoring_reasons = []
        all_matches = []
        
        self.logger.debug(f"Calculating impact for test case {test_case.id} against tab {sttm_tab.name}")
        
        # Question 1: Does test case mention the changed STTM tab name?
        tab_matches = self.text_matcher.find_tab_references(test_case, sttm_tab.name)
        if tab_matches:
            best_tab_match = self.match_analyzer.get_best_tab_match(tab_matches)
            points = self._score_tab_matches(best_tab_match)
            total_points += points
            all_matches.extend(tab_matches)
            
            if points > 0:
                scoring_reasons.append(ScoringReason(
                    points_added=points,
                    reason=f"Test mentions the changed tab '{sttm_tab.name}'",
                    evidence=best_tab_match.matched_text,
                    rule_name="tab_name_reference"
                ))
        
        # Question 2: What type of changes happened? (Base impact scoring)
        change_points = self._score_change_types(sttm_tab)
        total_points += change_points
        scoring_reasons.extend(self._get_change_type_reasons(sttm_tab))
        
        # Question 3: Does test case mention specific field names that changed?
        all_mappings = sttm_tab.get_all_changed_mappings()
        field_matches = self.text_matcher.find_field_references(test_case, all_mappings)
        if field_matches:
            field_points = len(field_matches) * self.config.field_name_match_points
            total_points += field_points
            all_matches.extend(field_matches)
            
            field_names = [match.matched_text for match in field_matches]
            scoring_reasons.append(ScoringReason(
                points_added=field_points,
                reason=f"Test references changed field names: {', '.join(field_names)}",
                evidence=f"Found {len(field_matches)} field name references",
                rule_name="field_name_reference"
            ))
        
        # Question 4: Does test case mention sample data that changed?
        sample_matches = self.text_matcher.find_sample_data_references(test_case, all_mappings)
        if sample_matches:
            sample_points = len(sample_matches) * self.config.sample_data_match_points
            total_points += sample_points
            all_matches.extend(sample_matches)
            
            sample_values = [match.matched_text for match in sample_matches]
            scoring_reasons.append(ScoringReason(
                points_added=sample_points,
                reason=f"Test references changed sample data: {', '.join(sample_values)}",
                evidence=f"Found {len(sample_matches)} sample data references",
                rule_name="sample_data_reference"
            ))
        
        # Calculate overall confidence
        confidence = self.match_analyzer.calculate_overall_confidence(all_matches)
        
        # Determine impact level and recommended action
        impact_level = self.config.get_impact_level(total_points)
        recommended_action = self.config.get_recommended_action(impact_level)
        
        # Create impact score result
        impact_score = ImpactScore(
            total_points=total_points,
            impact_level=impact_level,
            confidence=confidence,
            scoring_reasons=scoring_reasons,
            matches_found=all_matches,
            recommended_action=recommended_action
        )
        
        self.logger.info(f"Impact calculated: {test_case.id} = {total_points} points ({impact_level.value})")
        return impact_score
    
    def _score_tab_matches(self, best_match: MatchResult) -> int:
        """Score tab name matches based on match type"""
        if not best_match:
            return 0
        
        if best_match.match_type == MatchType.EXACT_TAB_MATCH:
            return self.config.exact_tab_match_points
        elif best_match.match_type == MatchType.PARTIAL_TAB_MATCH:
            return self.config.partial_tab_match_points
        else:
            return 0
    
    def _score_change_types(self, sttm_tab: STTMTab) -> int:
        """Score based on types of changes in the STTM tab"""
        total_points = 0
        
        # Count different types of changes
        deleted_count = len(sttm_tab.deleted_mappings)
        modified_count = len(sttm_tab.modified_mappings) 
        added_count = len(sttm_tab.added_mappings)
        
        # Apply scoring
        total_points += deleted_count * self.config.deleted_field_points
        total_points += modified_count * self.config.modified_field_points
        total_points += added_count * self.config.added_field_points
        
        return total_points
    
    def _get_change_type_reasons(self, sttm_tab: STTMTab) -> List[ScoringReason]:
        """Get scoring reasons for change types"""
        reasons = []
        
        deleted_count = len(sttm_tab.deleted_mappings)
        if deleted_count > 0:
            points = deleted_count * self.config.deleted_field_points
            reasons.append(ScoringReason(
                points_added=points,
                reason=f"{deleted_count} field(s) were deleted",
                evidence=f"Deleted fields: {[m.source_field for m in sttm_tab.deleted_mappings]}",
                rule_name="deleted_fields"
            ))
        
        modified_count = len(sttm_tab.modified_mappings)
        if modified_count > 0:
            points = modified_count * self.config.modified_field_points
            reasons.append(ScoringReason(
                points_added=points,
                reason=f"{modified_count} field(s) were modified",
                evidence=f"Modified fields: {[m.source_field for m in sttm_tab.modified_mappings]}",
                rule_name="modified_fields"
            ))
        
        added_count = len(sttm_tab.added_mappings)
        if added_count > 0:
            points = added_count * self.config.added_field_points
            reasons.append(ScoringReason(
                points_added=points,
                reason=f"{added_count} field(s) were added",
                evidence=f"Added fields: {[m.source_field for m in sttm_tab.added_mappings]}",
                rule_name="added_fields"
            ))
        
        return reasons


class BusinessFriendlyScorer:
    """Wrapper class that provides business-friendly interface to impact scoring"""
    
    def __init__(self, config: ImpactAnalysisConfig):
        self.config = config
        self.scorer = DataDrivenImpactScorer(config)
    
    def explain_scoring_config(self) -> str:
        """Generate business-friendly explanation of scoring configuration"""
        explanation = "IMPACT SCORING CONFIGURATION\n"
        explanation += "===========================\n\n"
        
        explanation += "Questions we ask for each test case:\n\n"
        
        explanation += f"1. Does test mention the changed tab name?\n"
        explanation += f"   • Exact match: +{self.config.exact_tab_match_points} points\n"
        explanation += f"   • Partial match: +{self.config.partial_tab_match_points} points\n\n"
        
        explanation += f"2. What type of changes happened?\n"
        explanation += f"   • Each deleted field: +{self.config.deleted_field_points} points\n"
        explanation += f"   • Each modified field: +{self.config.modified_field_points} points\n"
        explanation += f"   • Each added field: +{self.config.added_field_points} points\n\n"
        
        explanation += f"3. Does test mention changed field names?\n"
        explanation += f"   • Each field name found: +{self.config.field_name_match_points} points\n\n"
        
        explanation += f"4. Does test mention changed sample data?\n"
        explanation += f"   • Each sample data found: +{self.config.sample_data_match_points} points\n\n"
        
        explanation += "Impact Levels:\n"
        if self.config.critical_threshold > 0:
            explanation += f"• {self.config.critical_threshold}+ points = CRITICAL (Update Immediately)\n"
        explanation += f"• {self.config.high_threshold}+ points = HIGH (Update Required)\n"
        explanation += f"• {self.config.medium_threshold}+ points = MEDIUM (Review Recommended)\n"
        explanation += f"• Below {self.config.medium_threshold} points = LOW (Monitor)\n"
        
        return explanation
    
    def get_scoring_preview(self, deleted_fields: int, modified_fields: int, 
                          added_fields: int, tab_match: bool = False,
                          field_references: int = 0, sample_references: int = 0) -> str:
        """Preview what the score would be for given inputs"""
        
        total_points = 0
        breakdown = []
        
        if tab_match:
            total_points += self.config.exact_tab_match_points
            breakdown.append(f"Tab name match: +{self.config.exact_tab_match_points}")
        
        if deleted_fields > 0:
            points = deleted_fields * self.config.deleted_field_points
            total_points += points
            breakdown.append(f"{deleted_fields} deleted fields: +{points}")
        
        if modified_fields > 0:
            points = modified_fields * self.config.modified_field_points
            total_points += points
            breakdown.append(f"{modified_fields} modified fields: +{points}")
        
        if added_fields > 0:
            points = added_fields * self.config.added_field_points
            total_points += points
            breakdown.append(f"{added_fields} added fields: +{points}")
        
        if field_references > 0:
            points = field_references * self.config.field_name_match_points
            total_points += points
            breakdown.append(f"{field_references} field name references: +{points}")
        
        if sample_references > 0:
            points = sample_references * self.config.sample_data_match_points
            total_points += points
            breakdown.append(f"{sample_references} sample data references: +{points}")
        
        impact_level = self.config.get_impact_level(total_points)
        action = self.config.get_recommended_action(impact_level)
        
        preview = f"SCORING PREVIEW\n"
        preview += f"===============\n"
        preview += f"Total Points: {total_points}\n"
        preview += f"Impact Level: {impact_level.value}\n"
        preview += f"Recommended Action: {action.value.replace('_', ' ')}\n\n"
        preview += f"Point Breakdown:\n"
        for item in breakdown:
            preview += f"  • {item}\n"
        
        return preview
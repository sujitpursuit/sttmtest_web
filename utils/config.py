"""
Configuration management for the STTM impact analysis tool.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


@dataclass
class MatchingConfig:
    """Configuration for matching algorithms"""
    
    # Fuzzy matching thresholds
    tab_name_threshold: float = 0.8
    field_name_threshold: float = 0.7
    content_matching_threshold: float = 0.6
    
    # Case sensitivity settings
    case_sensitive_tab_matching: bool = False
    case_sensitive_field_matching: bool = False
    
    # Matching algorithms
    use_fuzzy_matching: bool = True
    use_keyword_extraction: bool = True
    use_partial_matching: bool = True


@dataclass
class ImpactScoringConfig:
    """Configuration for impact scoring algorithms (LEGACY - use SimplifiedScoringConfig for Phase 2)"""
    
    # Impact weights for different change types
    deleted_mapping_weight: float = 10.0
    modified_mapping_weight: float = 5.0
    added_mapping_weight: float = 3.0
    
    # Field-specific weights
    sample_data_change_weight: float = 8.0
    canonical_name_change_weight: float = 6.0
    field_name_change_weight: float = 4.0
    
    # Confidence multipliers
    high_confidence_multiplier: float = 1.2
    medium_confidence_multiplier: float = 1.0
    low_confidence_multiplier: float = 0.8
    
    # Impact level thresholds
    high_impact_threshold: float = 8.0
    medium_impact_threshold: float = 4.0


@dataclass
class SimplifiedScoringConfig:
    """Phase 2: Simplified, business-friendly scoring configuration"""
    
    # Basic scoring weights (the simple checklist approach)
    tab_name_match_points: int = 3          # Points for mentioning changed tab
    deleted_field_points: int = 5           # Points per deleted field
    modified_field_points: int = 3          # Points per modified field  
    added_field_points: int = 1             # Points per added field
    
    # Match confidence points (partial vs exact matches)
    exact_tab_match_points: int = 2         # Exact tab name match
    partial_tab_match_points: int = 1       # Partial tab name match
    field_name_match_points: int = 2        # Field name mentioned in test
    sample_data_match_points: int = 3       # Sample data mentioned in test
    
    # Impact level thresholds (configurable boundaries)
    critical_threshold: int = 12            # 12+ points = CRITICAL
    high_threshold: int = 8                 # 8-11 points = HIGH
    medium_threshold: int = 4               # 4-7 points = MEDIUM
    low_threshold: int = 0                  # 0-3 points = LOW
    
    # Text matching sensitivity
    partial_match_min_keywords: int = 1     # Min keywords for partial match
    case_sensitive_matching: bool = False   # Case sensitive text matching
    minimum_keyword_length: int = 3         # Ignore short words
    
    def get_impact_level_name(self, points: int) -> str:
        """Get impact level name for given points"""
        if points >= self.critical_threshold:
            return "CRITICAL"
        elif points >= self.high_threshold:
            return "HIGH"
        elif points >= self.medium_threshold:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_action_for_level(self, level: str) -> str:
        """Get recommended action for impact level"""
        action_map = {
            "CRITICAL": "UPDATE_IMMEDIATELY",
            "HIGH": "UPDATE_REQUIRED", 
            "MEDIUM": "REVIEW_RECOMMENDED",
            "LOW": "MONITOR"
        }
        return action_map.get(level, "NO_ACTION")


@dataclass
class ParsingConfig:
    """Configuration for file parsing"""
    
    # Excel parsing settings
    skip_empty_rows: bool = True
    trim_whitespace: bool = True
    case_insensitive_columns: bool = True
    
    # ID pattern detection
    min_confidence_for_pattern: float = 0.7
    max_sample_ids_for_analysis: int = 50
    
    # Error handling
    continue_on_parsing_errors: bool = True
    log_parsing_warnings: bool = True


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    
    # Output formats
    generate_json: bool = True
    generate_html: bool = False
    generate_markdown: bool = False
    generate_excel: bool = False
    
    # Report content
    include_executive_summary: bool = True
    include_detailed_analysis: bool = True
    include_new_test_generation: bool = True
    include_gap_analysis: bool = True
    
    # Formatting
    max_description_length: int = 500
    show_confidence_scores: bool = True
    group_by_impact_level: bool = True


@dataclass
class STTMConfig:
    """Main configuration class for the STTM analysis tool (LEGACY - Phase 1)"""
    
    matching: MatchingConfig = field(default_factory=MatchingConfig)
    impact_scoring: ImpactScoringConfig = field(default_factory=ImpactScoringConfig)
    parsing: ParsingConfig = field(default_factory=ParsingConfig)
    reporting: ReportConfig = field(default_factory=ReportConfig)
    
    # General settings
    log_level: str = "INFO"
    output_directory: str = "./output"
    temp_directory: str = "./temp"
    
    # Processing options
    parallel_processing: bool = False
    max_workers: int = 4


@dataclass
class Phase2Config:
    """Phase 2: Simplified configuration for business users"""
    
    # Core impact analysis settings
    scoring: SimplifiedScoringConfig = field(default_factory=SimplifiedScoringConfig)
    matching: MatchingConfig = field(default_factory=MatchingConfig)  
    parsing: ParsingConfig = field(default_factory=ParsingConfig)
    reporting: ReportConfig = field(default_factory=ReportConfig)
    
    # General settings
    log_level: str = "INFO"
    output_directory: str = "./output"
    
    def save_to_file(self, file_path: str):
        """Save simplified configuration to JSON file"""
        config_dict = {
            "scoring": {
                "tab_name_match_points": self.scoring.tab_name_match_points,
                "deleted_field_points": self.scoring.deleted_field_points,
                "modified_field_points": self.scoring.modified_field_points,
                "added_field_points": self.scoring.added_field_points,
                "exact_tab_match_points": self.scoring.exact_tab_match_points,
                "partial_tab_match_points": self.scoring.partial_tab_match_points,
                "field_name_match_points": self.scoring.field_name_match_points,
                "sample_data_match_points": self.scoring.sample_data_match_points,
                "critical_threshold": self.scoring.critical_threshold,
                "high_threshold": self.scoring.high_threshold,
                "medium_threshold": self.scoring.medium_threshold,
                "low_threshold": self.scoring.low_threshold,
                "case_sensitive_matching": self.scoring.case_sensitive_matching,
                "minimum_keyword_length": self.scoring.minimum_keyword_length
            },
            "log_level": self.log_level,
            "output_directory": self.output_directory
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'Phase2Config':
        """Load simplified configuration from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        # Create scoring config from dictionary, filtering out documentation keys
        scoring_data = config_dict.get('scoring', {})
        
        # Filter out documentation keys (start with underscore)
        clean_scoring_data = {
            key: value for key, value in scoring_data.items() 
            if not key.startswith('_')
        }
        
        scoring_config = SimplifiedScoringConfig(**clean_scoring_data)
        
        return cls(
            scoring=scoring_config,
            log_level=config_dict.get('log_level', 'INFO'),
            output_directory=config_dict.get('output_directory', './output')
        )


@dataclass
class STTMConfig:
    """Main configuration class for the STTM analysis tool (LEGACY - Phase 1)"""
    
    matching: MatchingConfig = field(default_factory=MatchingConfig)
    impact_scoring: ImpactScoringConfig = field(default_factory=ImpactScoringConfig)
    parsing: ParsingConfig = field(default_factory=ParsingConfig)
    reporting: ReportConfig = field(default_factory=ReportConfig)
    
    # General settings
    log_level: str = "INFO"
    output_directory: str = "./output"
    temp_directory: str = "./temp"
    
    # Processing options
    parallel_processing: bool = False
    max_workers: int = 4

    def save_to_file(self, file_path: str):
        """Save configuration to JSON file"""
        config_dict = self.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'STTMConfig':
        """Load configuration from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return cls.from_dict(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'matching': {
                'tab_name_threshold': self.matching.tab_name_threshold,
                'field_name_threshold': self.matching.field_name_threshold,
                'content_matching_threshold': self.matching.content_matching_threshold,
                'case_sensitive_tab_matching': self.matching.case_sensitive_tab_matching,
                'case_sensitive_field_matching': self.matching.case_sensitive_field_matching,
                'use_fuzzy_matching': self.matching.use_fuzzy_matching,
                'use_keyword_extraction': self.matching.use_keyword_extraction,
                'use_partial_matching': self.matching.use_partial_matching
            },
            'impact_scoring': {
                'deleted_mapping_weight': self.impact_scoring.deleted_mapping_weight,
                'modified_mapping_weight': self.impact_scoring.modified_mapping_weight,
                'added_mapping_weight': self.impact_scoring.added_mapping_weight,
                'sample_data_change_weight': self.impact_scoring.sample_data_change_weight,
                'canonical_name_change_weight': self.impact_scoring.canonical_name_change_weight,
                'field_name_change_weight': self.impact_scoring.field_name_change_weight,
                'high_confidence_multiplier': self.impact_scoring.high_confidence_multiplier,
                'medium_confidence_multiplier': self.impact_scoring.medium_confidence_multiplier,
                'low_confidence_multiplier': self.impact_scoring.low_confidence_multiplier,
                'high_impact_threshold': self.impact_scoring.high_impact_threshold,
                'medium_impact_threshold': self.impact_scoring.medium_impact_threshold
            },
            'parsing': {
                'skip_empty_rows': self.parsing.skip_empty_rows,
                'trim_whitespace': self.parsing.trim_whitespace,
                'case_insensitive_columns': self.parsing.case_insensitive_columns,
                'min_confidence_for_pattern': self.parsing.min_confidence_for_pattern,
                'max_sample_ids_for_analysis': self.parsing.max_sample_ids_for_analysis,
                'continue_on_parsing_errors': self.parsing.continue_on_parsing_errors,
                'log_parsing_warnings': self.parsing.log_parsing_warnings
            },
            'reporting': {
                'generate_json': self.reporting.generate_json,
                'generate_html': self.reporting.generate_html,
                'generate_markdown': self.reporting.generate_markdown,
                'generate_excel': self.reporting.generate_excel,
                'include_executive_summary': self.reporting.include_executive_summary,
                'include_detailed_analysis': self.reporting.include_detailed_analysis,
                'include_new_test_generation': self.reporting.include_new_test_generation,
                'include_gap_analysis': self.reporting.include_gap_analysis,
                'max_description_length': self.reporting.max_description_length,
                'show_confidence_scores': self.reporting.show_confidence_scores,
                'group_by_impact_level': self.reporting.group_by_impact_level
            },
            'log_level': self.log_level,
            'output_directory': self.output_directory,
            'temp_directory': self.temp_directory,
            'parallel_processing': self.parallel_processing,
            'max_workers': self.max_workers
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'STTMConfig':
        """Create configuration from dictionary"""
        
        matching = MatchingConfig(**config_dict.get('matching', {}))
        impact_scoring = ImpactScoringConfig(**config_dict.get('impact_scoring', {}))
        parsing = ParsingConfig(**config_dict.get('parsing', {}))
        reporting = ReportConfig(**config_dict.get('reporting', {}))
        
        return cls(
            matching=matching,
            impact_scoring=impact_scoring,
            parsing=parsing,
            reporting=reporting,
            log_level=config_dict.get('log_level', 'INFO'),
            output_directory=config_dict.get('output_directory', './output'),
            temp_directory=config_dict.get('temp_directory', './temp'),
            parallel_processing=config_dict.get('parallel_processing', False),
            max_workers=config_dict.get('max_workers', 4)
        )


def get_default_config() -> STTMConfig:
    """Get the default configuration"""
    return STTMConfig()


def load_config(config_file: Optional[str] = None) -> STTMConfig:
    """Load configuration from file or return default"""
    
    if config_file and Path(config_file).exists():
        try:
            return STTMConfig.load_from_file(config_file)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            print("Using default configuration")
    
    return get_default_config()


def save_default_config(output_file: str = "sttm_config.json"):
    """Save default configuration to file for customization"""
    config = get_default_config()
    config.save_to_file(output_file)
    print(f"Default configuration saved to: {output_file}")


# LEGACY: Predefined configuration presets (Phase 1)
PRESET_CONFIGS = {
    "strict": STTMConfig(
        matching=MatchingConfig(
            tab_name_threshold=0.9,
            field_name_threshold=0.85,
            content_matching_threshold=0.8,
            case_sensitive_tab_matching=True
        ),
        impact_scoring=ImpactScoringConfig(
            high_impact_threshold=6.0,
            medium_impact_threshold=3.0
        )
    ),
    
    "lenient": STTMConfig(
        matching=MatchingConfig(
            tab_name_threshold=0.6,
            field_name_threshold=0.5,
            content_matching_threshold=0.4
        ),
        impact_scoring=ImpactScoringConfig(
            high_impact_threshold=10.0,
            medium_impact_threshold=6.0
        )
    ),
    
    "balanced": STTMConfig()  # Default is balanced
}


# Phase 2: Simplified configuration presets for business users
PHASE2_PRESET_CONFIGS = {
    "conservative": Phase2Config(
        scoring=SimplifiedScoringConfig(
            # Lower thresholds = more tests flagged as high impact
            critical_threshold=10,
            high_threshold=6, 
            medium_threshold=3,
            # Higher points for changes
            deleted_field_points=6,
            modified_field_points=4,
            added_field_points=2
        )
    ),
    
    "balanced": Phase2Config(
        scoring=SimplifiedScoringConfig()  # Uses defaults
    ),
    
    "aggressive": Phase2Config(
        scoring=SimplifiedScoringConfig(
            # Higher thresholds = fewer tests flagged as high impact
            critical_threshold=15,
            high_threshold=10,
            medium_threshold=6,
            # Standard points for changes
            deleted_field_points=5,
            modified_field_points=3,
            added_field_points=1
        )
    ),
    
    "strict": Phase2Config(
        scoring=SimplifiedScoringConfig(
            # Very high thresholds = only obvious impacts flagged
            critical_threshold=20,
            high_threshold=12,
            medium_threshold=8,
            # Standard points but case sensitive
            case_sensitive_matching=True,
            minimum_keyword_length=4
        )
    )
}


def get_preset_config(preset_name: str) -> STTMConfig:
    """Get a predefined configuration preset (LEGACY - Phase 1)"""
    if preset_name in PRESET_CONFIGS:
        return PRESET_CONFIGS[preset_name]
    else:
        available_presets = list(PRESET_CONFIGS.keys())
        raise ValueError(f"Unknown preset '{preset_name}'. Available presets: {available_presets}")


def get_phase2_preset_config(preset_name: str) -> Phase2Config:
    """Get a Phase 2 simplified configuration preset"""
    if preset_name in PHASE2_PRESET_CONFIGS:
        return PHASE2_PRESET_CONFIGS[preset_name]
    else:
        available_presets = list(PHASE2_PRESET_CONFIGS.keys())
        raise ValueError(f"Unknown Phase 2 preset '{preset_name}'. Available presets: {available_presets}")


def get_default_phase2_config() -> Phase2Config:
    """Get the default Phase 2 configuration"""
    return Phase2Config()


def save_phase2_config(output_file: str = "phase2_config.json", preset: str = "balanced", include_documentation: bool = False):
    """Save Phase 2 configuration to file for customization"""
    config = get_phase2_preset_config(preset)
    
    if include_documentation:
        # Create documented version with comments
        config_dict = {
            "_documentation": {
                "title": "STTM Impact Analysis - Scoring Configuration",
                "description": "This file controls how test cases are scored for impact when STTM changes occur",
                "preset_used": preset,
                "version": "Phase 2"
            },
            
            "scoring": {
                "_comment": "Points awarded for different types of evidence that a test case is affected",
                
                "tab_name_match_points": config.scoring.tab_name_match_points,
                "_tab_name_match_explanation": "Points when test case mentions the changed STTM tab name",
                
                "deleted_field_points": config.scoring.deleted_field_points,
                "_deleted_field_explanation": "Points per deleted field (high impact - deleted fields usually break tests)",
                
                "modified_field_points": config.scoring.modified_field_points,
                "_modified_field_explanation": "Points per modified field (medium impact - field changed but still exists)",
                
                "added_field_points": config.scoring.added_field_points,
                "_added_field_explanation": "Points per added field (low impact - new fields rarely break existing tests)",
                
                "exact_tab_match_points": config.scoring.exact_tab_match_points,
                "_exact_tab_match_explanation": "Bonus points when test mentions the complete STTM tab name",
                
                "partial_tab_match_points": config.scoring.partial_tab_match_points,
                "_partial_tab_match_explanation": "Points when test mentions some keywords from STTM tab name",
                
                "field_name_match_points": config.scoring.field_name_match_points,
                "_field_name_match_explanation": "Points for each field name mentioned in test case content",
                
                "sample_data_match_points": config.scoring.sample_data_match_points,
                "_sample_data_match_explanation": "Points when test mentions specific sample data values that changed",
                
                "_thresholds_comment": "Point thresholds that determine final impact level",
                
                "critical_threshold": config.scoring.critical_threshold,
                "_critical_explanation": f"{config.scoring.critical_threshold}+ points = CRITICAL impact (update immediately)",
                
                "high_threshold": config.scoring.high_threshold,
                "_high_explanation": f"{config.scoring.high_threshold}-{config.scoring.critical_threshold-1} points = HIGH impact (update required)",
                
                "medium_threshold": config.scoring.medium_threshold,
                "_medium_explanation": f"{config.scoring.medium_threshold}-{config.scoring.high_threshold-1} points = MEDIUM impact (review recommended)",
                
                "low_threshold": config.scoring.low_threshold,
                "_low_explanation": f"{config.scoring.low_threshold}-{config.scoring.medium_threshold-1} points = LOW impact (monitor)",
                
                "case_sensitive_matching": config.scoring.case_sensitive_matching,
                "_case_sensitive_explanation": "false = 'VendorID' matches 'vendorid' | true = exact case required",
                
                "minimum_keyword_length": config.scoring.minimum_keyword_length,
                "_minimum_keyword_explanation": "Ignore short words when matching (e.g., ignore 'ID' but match 'Vendor')"
            },
            
            "log_level": config.log_level,
            "_log_level_explanation": "INFO=normal output | DEBUG=detailed matching info | WARNING=errors only",
            
            "output_directory": config.output_directory,
            "_output_directory_explanation": "Where to save impact analysis reports"
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    else:
        # Standard configuration without documentation
        config.save_to_file(output_file)
    
    print(f"Phase 2 '{preset}' configuration saved to: {output_file}")
    if include_documentation:
        print("   [INFO] Documentation and explanations included")


def load_phase2_config(config_file: Optional[str] = None) -> Phase2Config:
    """Load Phase 2 configuration from file or return default"""
    
    if config_file and Path(config_file).exists():
        try:
            return Phase2Config.load_from_file(config_file)
        except Exception as e:
            print(f"Warning: Could not load Phase 2 config file {config_file}: {e}")
            print("Using default Phase 2 configuration")
    
    return get_default_phase2_config()
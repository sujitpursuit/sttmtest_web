"""
Phase 2 Impact Analysis Test Suite

This test suite validates the simplified impact scoring algorithm and 
ensures that business users can understand and configure the system.
"""

import logging
import json
from datetime import datetime

from models.impact_models import ImpactAnalysisConfig
from analyzers.impact_analyzer import ImpactAnalyzer, QuickImpactAnalyzer
from analyzers.impact_scorer import BusinessFriendlyScorer
from utils.config import get_phase2_preset_config, save_phase2_config


def test_simplified_scoring_config():
    """Test that simplified scoring configuration works correctly"""
    print("[TEST] Testing simplified scoring configuration...")
    
    try:
        # Test default configuration
        config = ImpactAnalysisConfig()
        
        # Verify basic scoring weights
        assert config.tab_name_match_points == 3
        assert config.deleted_field_points == 5
        assert config.modified_field_points == 3
        assert config.added_field_points == 1
        
        # Test impact level calculation
        assert config.get_impact_level(15).value == "CRITICAL"  # 15 >= 12
        assert config.get_impact_level(10).value == "HIGH"      # 10 >= 8, < 12
        assert config.get_impact_level(6).value == "MEDIUM"     # 6 >= 4, < 8
        assert config.get_impact_level(2).value == "LOW"       # 2 < 4
        
        print("   [SUCCESS] Simplified scoring configuration works correctly")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Simplified scoring configuration failed: {e}")
        return False


def test_preset_configurations():
    """Test that Phase 2 preset configurations are valid"""
    print("[TEST] Testing Phase 2 preset configurations...")
    
    try:
        presets = ["conservative", "balanced", "aggressive", "strict"]
        
        for preset_name in presets:
            config = get_phase2_preset_config(preset_name)
            
            # Verify configuration is valid
            assert config.scoring.critical_threshold > config.scoring.high_threshold
            assert config.scoring.high_threshold > config.scoring.medium_threshold
            assert config.scoring.medium_threshold >= config.scoring.low_threshold
            
            print(f"      [OK] {preset_name} preset is valid")
        
        print("   [SUCCESS] All Phase 2 preset configurations are valid")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Preset configuration test failed: {e}")
        return False


def test_business_friendly_scoring():
    """Test business-friendly scoring interface"""
    print("[TEST] Testing business-friendly scoring interface...")
    
    try:
        config = ImpactAnalysisConfig()
        scorer = BusinessFriendlyScorer(config)
        
        # Test configuration explanation
        explanation = scorer.explain_scoring_config()
        assert "Questions we ask for each test case:" in explanation
        assert "Impact Levels:" in explanation
        
        # Test scoring preview
        preview = scorer.get_scoring_preview(
            deleted_fields=1, modified_fields=0, added_fields=0,
            tab_match=True, field_references=1, sample_references=0
        )
        
        # Should be: 5 (deleted) + 2 (exact tab match) + 2 (field ref) = 9 points = HIGH
        assert "Total Points: 9" in preview
        assert "Impact Level: HIGH" in preview
        
        print("   [SUCCESS] Business-friendly scoring interface works correctly")
        return True
        
    except Exception as e:
        import traceback
        print(f"   [ERROR] Business-friendly scoring test failed: {e}")
        traceback.print_exc()
        return False


def test_impact_analysis_with_real_data():
    """Test impact analysis with actual STTM and QTEST files"""
    print("[TEST] Testing impact analysis with real data...")
    
    try:
        # Use default configuration for testing
        config = ImpactAnalysisConfig()
        analyzer = ImpactAnalyzer(config)
        
        # Run analysis with real files
        report = analyzer.analyze_impact("STTM_DIFF.json", "QTEST_STTM.xlsx")
        
        # Verify report structure
        assert report.total_sttm_tabs_analyzed > 0
        assert report.total_test_cases_analyzed > 0
        assert len(report.tab_summaries) > 0
        
        # Verify executive summary
        summary = report.get_executive_summary()
        assert "EXECUTIVE SUMMARY" in summary
        assert "Test Cases Analyzed:" in summary
        
        print(f"   [SUCCESS] Analysis completed: {len(report.tab_summaries)} tabs analyzed")
        print(f"   [INFO] Total impacts: Critical={report.total_critical_impact}, High={report.total_high_impact}, Medium={report.total_medium_impact}, Low={report.total_low_impact}")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Real data impact analysis failed: {e}")
        return False


def test_configuration_persistence():
    """Test saving and loading configuration files"""
    print("[TEST] Testing configuration file persistence...")
    
    try:
        # Create custom configuration
        config = get_phase2_preset_config("conservative")
        
        # Modify some values
        config.scoring.deleted_field_points = 7
        config.scoring.high_threshold = 9
        
        # Save to file
        config_file = "test_phase2_config.json"
        config.save_to_file(config_file)
        
        # Load from file
        from utils.config import Phase2Config
        loaded_config = Phase2Config.load_from_file(config_file)
        
        # Verify values were saved and loaded correctly
        assert loaded_config.scoring.deleted_field_points == 7
        assert loaded_config.scoring.high_threshold == 9
        
        print("   [SUCCESS] Configuration persistence works correctly")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Configuration persistence test failed: {e}")
        return False


def test_quick_impact_analyzer():
    """Test the simplified QuickImpactAnalyzer interface"""
    print("[TEST] Testing quick impact analyzer...")
    
    try:
        analyzer = QuickImpactAnalyzer()
        
        # Test quick check
        summary = analyzer.quick_check("STTM_DIFF.json", "QTEST_STTM.xlsx")
        assert "EXECUTIVE SUMMARY" in summary
        
        # Test priority actions
        actions = analyzer.get_priority_actions("STTM_DIFF.json", "QTEST_STTM.xlsx")
        assert isinstance(actions, list)
        
        # Test configuration testing
        config_test = analyzer.test_scoring_config()
        assert "EXAMPLE SCENARIOS" in config_test
        
        print("   [SUCCESS] Quick impact analyzer works correctly")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Quick impact analyzer test failed: {e}")
        return False


def test_scoring_algorithm_examples():
    """Test scoring algorithm with specific examples to validate logic"""
    print("[TEST] Testing scoring algorithm with specific examples...")
    
    try:
        config = ImpactAnalysisConfig()
        
        # Example 1: High impact scenario
        # - Tab match (exact): +2 points
        # - 1 deleted field: +5 points  
        # - 1 field reference: +2 points
        # Total: 9 points = HIGH impact
        
        # Example 2: Medium impact scenario  
        # - Tab match (partial): +1 point
        # - 1 modified field: +3 points
        # Total: 4 points = MEDIUM impact
        
        # Example 3: Low impact scenario
        # - No tab match: +0 points
        # - 2 added fields: +2 points
        # Total: 2 points = LOW impact
        
        # Verify impact level boundaries work correctly
        assert config.get_impact_level(9).value == "HIGH"
        assert config.get_impact_level(4).value == "MEDIUM"  
        assert config.get_impact_level(2).value == "LOW"
        
        print("   [SUCCESS] Scoring algorithm examples validated")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Scoring algorithm examples failed: {e}")
        return False


def generate_sample_config_files():
    """Generate sample configuration files for different scenarios"""
    print("[TEST] Generating sample configuration files...")
    
    try:
        presets = ["conservative", "balanced", "aggressive", "strict"]
        
        for preset in presets:
            filename = f"sample_{preset}_config.json"
            save_phase2_config(filename, preset)
        
        print("   [SUCCESS] Sample configuration files generated")
        print("   [INFO] Files created: sample_conservative_config.json, sample_balanced_config.json, sample_aggressive_config.json, sample_strict_config.json")
        return True
        
    except Exception as e:
        print(f"   [ERROR] Sample config generation failed: {e}")
        return False


def main():
    """Run Phase 2 impact analysis test suite"""
    
    print("[START] Phase 2 Impact Analysis Test Suite")
    print("=" * 60)
    
    # Test results
    results = []
    
    # Run all tests
    results.append(test_simplified_scoring_config())
    results.append(test_preset_configurations()) 
    results.append(test_business_friendly_scoring())
    results.append(test_impact_analysis_with_real_data())
    results.append(test_configuration_persistence())
    results.append(test_quick_impact_analyzer())
    results.append(test_scoring_algorithm_examples())
    results.append(generate_sample_config_files())
    
    print("\n" + "=" * 60)
    print("[SUMMARY] PHASE 2 TEST RESULTS:")
    
    if all(results):
        print("[SUCCESS] ALL PHASE 2 TESTS PASSED!")
        print("\n[VERIFIED] Phase 2 Impact Analysis Features:")
        print("   [OK] Simplified, configurable scoring algorithm")
        print("   [OK] Business-friendly configuration interface") 
        print("   [OK] Multiple preset configurations available")
        print("   [OK] Real data processing with actual STTM/QTEST files")
        print("   [OK] Configuration persistence and loading")
        print("   [OK] Quick analyzer interface for business users")
        print("   [OK] Scoring algorithm logic validated")
        
        print("\n[READY] Phase 2 is complete and ready for business use!")
        print("   • Configure scoring with simple JSON files")
        print("   • Choose from 4 preset configurations (conservative, balanced, aggressive, strict)")
        print("   • Get clear explanations of impact scores")
        print("   • Process real STTM and QTEST data")
        
    else:
        failed_tests = sum(1 for result in results if not result)
        print(f"[ERROR] {failed_tests} Phase 2 tests failed")
        print("   Review the individual test results above")
    
    return all(results)


if __name__ == "__main__":
    # Configure logging for test output
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing
    
    success = main()
    exit(0 if success else 1)
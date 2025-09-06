"""
Main entry point for the STTM Impact Analysis Tool - Phase 1
Command-line interface for parsing and validating STTM and QTEST files.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from utils.logger import get_logger, setup_logging
from utils.config import load_config, save_default_config, save_phase2_config, load_phase2_config
from parsers.sttm_parser import parse_sttm_file
from parsers.qtest_parser import parse_qtest_file
from models.sttm_models import STTMDocument
from models.test_models import QTestDocument
from models.impact_models import ImpactAnalysisConfig
from analyzers.impact_analyzer import ImpactAnalyzer
from generators.test_step_generator import TestStepGenerator
from generators.test_modification_exporter import TestModificationExporter


def setup_cli_parser() -> argparse.ArgumentParser:
    """Setup command-line argument parser for Phase 1"""
    
    parser = argparse.ArgumentParser(
        description="STTM Impact Analysis Tool - Phase 1: Data Parsing and Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Phase 1 Examples (Parsing & Validation):
  # Parse STTM file only
  python main.py --parse-sttm STTM_DIFF.json
  
  # Parse QTEST file only  
  python main.py --parse-qtest QTEST_STTM.xlsx
  
  # Parse both files
  python main.py --parse-both STTM_DIFF.json QTEST_STTM.xlsx
  
  # Validate both files
  python main.py --validate STTM_DIFF.json QTEST_STTM.xlsx

Phase 2 Examples (Impact Analysis):
  # Run impact analysis with default settings
  python main.py --analyze-impact STTMDIFF_V2.json QTEST_STTM.xlsx
  
  # Generate configuration file
  python main.py --generate-config balanced --config-output my_config.json
  
  # Run impact analysis with custom configuration
  python main.py --analyze-impact STTMDIFF_V2.json QTEST_STTM.xlsx --config my_config.json

Phase 3B Examples (Test Step Generation):
  # Generate test step modifications based on STTM changes
  python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx
  
  # Generate test steps with custom configuration
  python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx --config my_config.json
  
  # Modify original QTEST file directly instead of generating delta file
  python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx --modify-in-place
        """
    )
    
    # Main action arguments
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        '--parse-sttm', 
        type=str,
        help='Parse STTM difference JSON file'
    )
    action_group.add_argument(
        '--parse-qtest',
        type=str, 
        help='Parse QTEST Excel file'
    )
    action_group.add_argument(
        '--parse-both',
        nargs=2,
        metavar=('STTM_FILE', 'QTEST_FILE'),
        help='Parse both STTM JSON and QTEST Excel files'
    )
    action_group.add_argument(
        '--validate',
        nargs=2,
        metavar=('STTM_FILE', 'QTEST_FILE'),
        help='Validate both files and show parsing results'
    )
    action_group.add_argument(
        '--save-default-config',
        action='store_true',
        help='Save default configuration to file'
    )
    action_group.add_argument(
        '--analyze-impact',
        nargs=2,
        metavar=('STTM_FILE', 'QTEST_FILE'),
        help='Run Phase 2 impact analysis between STTM and QTEST files'
    )
    action_group.add_argument(
        '--generate-config',
        metavar='PRESET',
        choices=['balanced', 'conservative', 'aggressive', 'strict'],
        help='Generate a Phase 2 configuration file with documentation'
    )
    action_group.add_argument(
        '--generate-test-steps',
        nargs=2,
        metavar=('STTM_FILE', 'QTEST_FILE'),
        help='Generate test step modifications based on STTM changes (Phase 3B)'
    )
    
    # Output options
    parser.add_argument(
        '--output-format',
        choices=['json', 'summary', 'detailed'],
        default='summary',
        help='Output format (default: summary)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file path (default: stdout)'
    )
    
    # Analysis options
    parser.add_argument(
        '--detect-id-pattern',
        action='store_true',
        help='Focus on ID pattern detection and display detailed results'
    )
    parser.add_argument(
        '--show-samples',
        action='store_true',
        help='Show sample data in output'
    )
    parser.add_argument('--config-output', metavar='FILE', default='my_config.json',
                       help='Output file for generated configuration (default: my_config.json)')
    
    # Phase 3B options
    parser.add_argument(
        '--modify-in-place',
        action='store_true',
        help='Modify original QTEST file directly instead of generating separate delta file (Phase 3B)'
    )
    
    # Configuration  
    parser.add_argument(
        '--config',
        type=str,
        help='Configuration file path'
    )
    
    # Logging
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Log file path'
    )
    
    return parser


def parse_sttm_command(file_path: str, logger, output_format: str, 
                      output_file: Optional[str] = None) -> dict:
    """Handle STTM parsing command"""
    
    logger.info("=== STTM File Parsing (Adapter Pattern) ===")
    
    try:
        # Parse the file using adapter pattern parser
        sttm_doc = parse_sttm_file(file_path, logger)
        
        # Generate results
        result = {
            "success": True,
            "file_type": "STTM",
            "file_path": file_path,
            "summary": sttm_doc.get_summary(),
            "details": {
                "changed_tabs": [tab.name for tab in sttm_doc.changed_tabs],
                "unchanged_tabs": [tab.name for tab in sttm_doc.unchanged_tabs],
                "tabs_with_changes": [tab.name for tab in sttm_doc.get_tabs_with_changes()]
            }
        }
        
        # Add detailed tab information if requested
        if output_format == 'detailed':
            result["tab_details"] = []
            for tab in sttm_doc.get_tabs_with_changes():
                tab_info = {
                    "name": tab.name,
                    "change_category": tab.change_category.value,
                    "change_summary": tab.get_change_summary(),
                    "mappings": {
                        "added": len(tab.added_mappings),
                        "deleted": len(tab.deleted_mappings),
                        "modified": len(tab.modified_mappings)
                    }
                }
                result["tab_details"].append(tab_info)
        
        logger.info(f"[SUCCESS] Successfully parsed STTM file")
        logger.info(f"   - {result['summary']['total_tabs']} tabs total")
        logger.info(f"   - {result['summary']['changed_tabs']} changed tabs")
        logger.info(f"   - {result['summary']['total_changes']} total changes")
        
        return result
        
    except Exception as e:
        error_result = {
            "success": False,
            "file_type": "STTM", 
            "file_path": file_path,
            "error": str(e)
        }
        logger.error(f"[ERROR] Failed to parse STTM file: {e}")
        return error_result


def parse_qtest_command(file_path: str, logger, output_format: str,
                       detect_id_pattern: bool = False,
                       output_file: Optional[str] = None) -> dict:
    """Handle QTEST parsing command"""
    
    logger.info("=== QTEST File Parsing ===")
    
    try:
        # Parse the file
        qtest_doc = parse_qtest_file(file_path, logger)
        
        # Generate results
        result = {
            "success": True,
            "file_type": "QTEST",
            "file_path": file_path,
            "summary": qtest_doc.get_summary(),
            "id_pattern": {
                "pattern": qtest_doc.detected_id_pattern,
                "description": qtest_doc.id_format_description
            }
        }
        
        # Add detailed information if requested
        if output_format == 'detailed' or detect_id_pattern:
            result["test_case_samples"] = []
            for i, tc in enumerate(qtest_doc.test_cases[:5]):  # First 5 as samples
                tc_info = {
                    "id": tc.id,
                    "name": tc.name[:100] + "..." if len(tc.name) > 100 else tc.name,
                    "step_count": tc.get_step_count(),
                    "referenced_systems": tc.referenced_systems
                }
                result["test_case_samples"].append(tc_info)
        
        logger.info(f"[SUCCESS] Successfully parsed QTEST file")
        logger.info(f"   - {result['summary']['total_test_cases']} test cases")
        logger.info(f"   - {result['summary']['total_test_steps']} total test steps")
        logger.info(f"   - ID Pattern: {qtest_doc.id_format_description}")
        
        return result
        
    except Exception as e:
        error_result = {
            "success": False,
            "file_type": "QTEST",
            "file_path": file_path, 
            "error": str(e)
        }
        logger.error(f"[ERROR] Failed to parse QTEST file: {e}")
        return error_result


def parse_both_command(sttm_file: str, qtest_file: str, logger,
                      output_format: str, output_file: Optional[str] = None) -> dict:
    """Handle parsing both files command"""
    
    logger.info("=== Parsing Both Files ===")
    
    # Parse STTM file
    sttm_result = parse_sttm_command(sttm_file, logger, output_format)
    
    # Parse QTEST file  
    qtest_result = parse_qtest_command(qtest_file, logger, output_format)
    
    # Combine results
    combined_result = {
        "success": sttm_result["success"] and qtest_result["success"],
        "files_parsed": 2,
        "sttm_result": sttm_result,
        "qtest_result": qtest_result
    }
    
    if combined_result["success"]:
        logger.info("[SUCCESS] Successfully parsed both files!")
    else:
        logger.warning("[WARNING] Some files failed to parse - see individual results")
    
    return combined_result


def output_results(results: dict, output_format: str, output_file: Optional[str], logger):
    """Output results in the specified format"""
    
    if output_format == 'json':
        output_content = json.dumps(results, indent=2)
    elif output_format == 'summary':
        output_content = format_summary_output(results)
    else:  # detailed
        output_content = format_detailed_output(results)
    
    # Write to file or stdout
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_content)
            logger.info(f"[OUTPUT] Results written to: {output_file}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to write output file: {e}")
            print(output_content)
    else:
        print("\n" + "="*60)
        print("RESULTS:")
        print("="*60)
        print(output_content)


def format_summary_output(results: dict) -> str:
    """Format results as summary output"""
    
    lines = []
    
    if "files_parsed" in results:
        # Combined results
        lines.append("COMBINED PARSING RESULTS:")
        lines.append(f"Files processed: {results['files_parsed']}")
        lines.append(f"Overall success: {results['success']}")
        lines.append("")
        
        if results["sttm_result"]["success"]:
            sttm = results["sttm_result"]["summary"]
            lines.append("STTM Results:")
            lines.append(f"  - Total tabs: {sttm['total_tabs']}")
            lines.append(f"  - Changed tabs: {sttm['changed_tabs']}")
            lines.append(f"  - Total changes: {sttm['total_changes']}")
            lines.append("")
        
        if results["qtest_result"]["success"]:
            qtest = results["qtest_result"]["summary"]
            lines.append("QTEST Results:")
            lines.append(f"  - Test cases: {qtest['total_test_cases']}")
            lines.append(f"  - Test steps: {qtest['total_test_steps']}")
            lines.append(f"  - ID pattern: {results['qtest_result']['id_pattern']['description']}")
            lines.append("")
    
    else:
        # Single file results
        if results["success"]:
            if results["file_type"] == "STTM":
                summary = results["summary"]
                lines.append("STTM PARSING RESULTS:")
                lines.append(f"  - Total tabs: {summary['total_tabs']}")
                lines.append(f"  - Changed tabs: {summary['changed_tabs']}")
                lines.append(f"  - Unchanged tabs: {summary['unchanged_tabs']}")
                lines.append(f"  - Total changes: {summary['total_changes']}")
                
                if "details" in results:
                    lines.append("\nChanged Tabs:")
                    for tab_name in results["details"]["tabs_with_changes"]:
                        lines.append(f"  - {tab_name}")
            
            elif results["file_type"] == "QTEST":
                summary = results["summary"]
                lines.append("QTEST PARSING RESULTS:")
                lines.append(f"  - Test cases: {summary['total_test_cases']}")
                lines.append(f"  - Test steps: {summary['total_test_steps']}")
                lines.append(f"  - Average steps per test: {summary['average_steps_per_test']}")
                lines.append(f"  - ID pattern: {results['id_pattern']['description']}")
            
            elif results["file_type"] == "IMPACT_ANALYSIS":
                lines.append("IMPACT ANALYSIS RESULTS:")
                lines.append("=" * 50)
                if "executive_summary" in results:
                    lines.append(results["executive_summary"])
                else:
                    summary = results["summary"]
                    lines.append(f"Files analyzed: {summary['sttm_file']} + {summary['qtest_file']}")
                    lines.append(f"STTM tabs analyzed: {summary['tabs_analyzed']}")
                    lines.append(f"Test cases analyzed: {summary['test_cases_analyzed']}")
                    lines.append(f"Total STTM changes: {summary['total_changes']}")
                    lines.append("")
                    lines.append("IMPACT BREAKDOWN:")
                    lines.append(f"  - Critical Impact: {summary['critical_impact']} (requires immediate attention)")
                    lines.append(f"  - High Impact: {summary['high_impact']} (update required)")
                    lines.append(f"  - Medium Impact: {summary['medium_impact']} (review recommended)")
                    lines.append(f"  - Low Impact: {summary['low_impact']} (monitor)")
                
                # Add report file locations
                if "reports_generated" in results:
                    lines.append("")
                    lines.append("DETAILED REPORTS GENERATED:")
                    lines.append(f"  - JSON Report: {results['reports_generated']['json_report']}")
                    lines.append(f"  - HTML Report: {results['reports_generated']['html_report']}")
                    lines.append("")
                    lines.append("The detailed reports contain:")
                    lines.append("  • Complete test case impact assessments")
                    lines.append("  • Affected step numbers for each test case")
                    lines.append("  • Detailed scoring breakdown and reasoning")
                    lines.append("  • Physical tab name information for changed tabs")
                
        else:
            lines.append(f"PARSING FAILED: {results['error']}")
    
    return "\n".join(lines)


def format_detailed_output(results: dict) -> str:
    """Format results as detailed output"""
    
    summary = format_summary_output(results)
    
    lines = [summary, "\n" + "="*60, "DETAILED INFORMATION:", "="*60]
    
    # Add detailed information based on result type
    if "files_parsed" in results:
        # Combined results - show both
        if "tab_details" in results.get("sttm_result", {}):
            lines.append("\nSTTM Tab Details:")
            for tab in results["sttm_result"]["tab_details"]:
                lines.append(f"  {tab['name']}: {tab['change_summary']}")
        
        if "test_case_samples" in results.get("qtest_result", {}):
            lines.append("\nQTEST Sample Test Cases:")
            for tc in results["qtest_result"]["test_case_samples"]:
                lines.append(f"  {tc['id']}: {tc['name']} ({tc['step_count']} steps)")
    
    else:
        # Single file detailed results
        if results.get("file_type") == "STTM" and "tab_details" in results:
            lines.append("\nTab Details:")
            for tab in results["tab_details"]:
                lines.append(f"  {tab['name']}:")
                lines.append(f"    Category: {tab['change_category']}")
                lines.append(f"    Changes: {tab['change_summary']}")
        
        elif results.get("file_type") == "QTEST" and "test_case_samples" in results:
            lines.append("\nSample Test Cases:")
            for tc in results["test_case_samples"]:
                lines.append(f"  {tc['id']}: {tc['name']}")
                lines.append(f"    Steps: {tc['step_count']}")
                if tc["referenced_systems"]:
                    lines.append(f"    Referenced systems: {', '.join(tc['referenced_systems'])}")
    
    return "\n".join(lines)


def analyze_impact_command(sttm_file: str, qtest_file: str, config_file: Optional[str], logger) -> dict:
    """Execute Phase 2 impact analysis command"""
    
    try:
        logger.info(f"[START] Phase 2 Impact Analysis: {sttm_file} + {qtest_file}")
        
        # Load configuration
        if config_file:
            config_obj = load_phase2_config(config_file)
            config = ImpactAnalysisConfig(
                tab_name_match_points=config_obj.scoring.tab_name_match_points,
                deleted_field_points=config_obj.scoring.deleted_field_points,
                modified_field_points=config_obj.scoring.modified_field_points,
                added_field_points=config_obj.scoring.added_field_points,
                exact_tab_match_points=config_obj.scoring.exact_tab_match_points,
                partial_tab_match_points=config_obj.scoring.partial_tab_match_points,
                field_name_match_points=config_obj.scoring.field_name_match_points,
                sample_data_match_points=config_obj.scoring.sample_data_match_points,
                critical_threshold=config_obj.scoring.critical_threshold,
                high_threshold=config_obj.scoring.high_threshold,
                medium_threshold=config_obj.scoring.medium_threshold,
                low_threshold=config_obj.scoring.low_threshold
            )
            logger.info(f"[CONFIG] Using configuration from: {config_file}")
        else:
            config = ImpactAnalysisConfig()
            logger.info("[CONFIG] Using default Phase 2 configuration")
        
        # Run impact analysis
        analyzer = ImpactAnalyzer(config, logger)
        report = analyzer.analyze_impact(sttm_file, qtest_file)
        
        # Generate detailed reports in reports directory
        from pathlib import Path
        from utils.report_formatters import save_json_report, save_html_report
        
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Create timestamped filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sttm_name = Path(sttm_file).stem
        
        json_file = reports_dir / f"impact_analysis_{sttm_name}_{timestamp}.json"
        html_file = reports_dir / f"impact_analysis_{sttm_name}_{timestamp}.html"
        
        # Save detailed reports
        save_json_report(report, str(json_file))
        save_html_report(report, str(html_file))
        
        logger.info(f"[REPORTS] JSON report saved to: {json_file}")
        logger.info(f"[REPORTS] HTML report saved to: {html_file}")
        
        # Format results for console output
        results = {
            "success": True,
            "file_type": "IMPACT_ANALYSIS",
            "summary": {
                "sttm_file": sttm_file,
                "qtest_file": qtest_file,
                "tabs_analyzed": report.total_sttm_tabs_analyzed,
                "test_cases_analyzed": report.total_test_cases_analyzed,
                "total_changes": report.total_sttm_changes,
                "critical_impact": report.total_critical_impact,
                "high_impact": report.total_high_impact,
                "medium_impact": report.total_medium_impact,
                "low_impact": report.total_low_impact
            },
            "executive_summary": report.get_executive_summary(),
            "reports_generated": {
                "json_report": str(json_file),
                "html_report": str(html_file)
            },
            "detailed_report_dict": report.to_dict()  # For JSON output if needed
        }
        
        logger.info(f"[SUCCESS] Impact analysis completed")
        logger.info(f"[RESULTS] Critical={report.total_critical_impact}, High={report.total_high_impact}, Medium={report.total_medium_impact}, Low={report.total_low_impact}")
        
        return results
        
    except Exception as e:
        logger.error(f"[ERROR] Impact analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_type": "IMPACT_ANALYSIS"
        }


def generate_config_command(preset: str, output_file: str, logger) -> dict:
    """Execute generate configuration command"""
    
    try:
        logger.info(f"[START] Generating '{preset}' configuration file: {output_file}")
        
        # Generate documented configuration file
        save_phase2_config(output_file, preset, include_documentation=True)
        
        results = {
            "success": True,
            "file_type": "CONFIG_GENERATION",
            "summary": {
                "preset": preset,
                "output_file": output_file,
                "documentation_included": True
            },
            "message": f"Phase 2 '{preset}' configuration saved to: {output_file}"
        }
        
        logger.info("[SUCCESS] Configuration file generated with documentation")
        
        return results
        
    except Exception as e:
        logger.error(f"[ERROR] Configuration generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_type": "CONFIG_GENERATION"
        }


def generate_test_steps_command(sttm_file: str, qtest_file: str, config_file: Optional[str], modify_in_place: bool, logger) -> dict:
    """Execute Phase 3B test step generation command"""
    
    try:
        logger.info(f"[START] Phase 3B Test Step Generation: {sttm_file} + {qtest_file}")
        
        # Load configuration (same as impact analysis)
        if config_file:
            config_obj = load_phase2_config(config_file)
            config = ImpactAnalysisConfig(
                tab_name_match_points=config_obj.scoring.tab_name_match_points,
                deleted_field_points=config_obj.scoring.deleted_field_points,
                modified_field_points=config_obj.scoring.modified_field_points,
                added_field_points=config_obj.scoring.added_field_points,
                exact_tab_match_points=config_obj.scoring.exact_tab_match_points,
                partial_tab_match_points=config_obj.scoring.partial_tab_match_points,
                field_name_match_points=config_obj.scoring.field_name_match_points,
                sample_data_match_points=config_obj.scoring.sample_data_match_points,
                critical_threshold=config_obj.scoring.critical_threshold,
                high_threshold=config_obj.scoring.high_threshold,
                medium_threshold=config_obj.scoring.medium_threshold,
                low_threshold=config_obj.scoring.low_threshold
            )
            logger.info(f"[CONFIG] Using configuration from: {config_file}")
        else:
            config = ImpactAnalysisConfig()
            logger.info("[CONFIG] Using default Phase 2 configuration")
        
        # Run impact analysis directly to get the report object
        logger.info("[IMPACT] Running impact analysis for test step generation...")
        analyzer = ImpactAnalyzer(config, logger)
        impact_report = analyzer.analyze_impact(sttm_file, qtest_file)
        
        # Parse QTEST file to get test case data for step generation
        logger.info("[QTEST] Parsing QTEST file for test case data...")
        qtest_document = parse_qtest_file(qtest_file, logger)
        
        if not qtest_document or not qtest_document.test_cases:
            return {
                "success": False,
                "error": "Failed to parse QTEST file or no test cases found",
                "file_type": "TEST_STEP_GENERATION"
            }
        
        # Generate test step modifications
        logger.info("[GENERATE] Creating test step modifications...")
        generator = TestStepGenerator(logger)
        generated_steps = generator.generate_test_modifications(impact_report, qtest_document.test_cases)
        
        if not generated_steps:
            logger.warning("[GENERATE] No test step modifications generated")
            return {
                "success": True,
                "file_type": "TEST_STEP_GENERATION",
                "summary": {
                    "sttm_file": sttm_file,
                    "qtest_file": qtest_file,
                    "steps_generated": 0
                },
                "message": "No test step modifications needed based on current impact analysis"
            }
        
        # Export to Excel
        exporter = TestModificationExporter(logger=logger)
        
        if modify_in_place:
            logger.info("[EXPORT] Modifying original QTEST file in-place...")
            output_file = exporter.copy_and_modify_original(generated_steps, qtest_file)
            logger.info(f"[EXPORT] Modified QTEST file saved to: {output_file}")
        else:
            logger.info("[EXPORT] Exporting test modifications to Excel...")
            output_file = exporter.export_with_original_test_data(generated_steps, qtest_file)
            # Add instructions sheet only for delta files
            exporter.create_instructions_sheet(output_file)
        
        # Generate summary
        summary = generator.generate_summary_report(generated_steps)
        summary_file = exporter.export_summary_report(generated_steps, summary)
        
        # Validate export format
        format_valid = exporter.validate_export_format(output_file)
        
        results = {
            "success": True,
            "file_type": "TEST_STEP_GENERATION",
            "summary": {
                "sttm_file": sttm_file,
                "qtest_file": qtest_file,
                "steps_generated": len(generated_steps),
                "add_actions": summary["action_breakdown"]["ADD"],
                "modify_actions": summary["action_breakdown"]["MODIFY"],
                "delete_actions": summary["action_breakdown"]["DELETE"],
                "format_validation": format_valid
            },
            "files_generated": {
                "test_modifications": output_file,
                "summary_report": summary_file
            },
            "generation_summary": summary
        }
        
        mode_desc = "in-place modifications" if modify_in_place else "delta file"
        logger.info(f"[SUCCESS] Generated {len(generated_steps)} test step modifications ({mode_desc})")
        logger.info(f"[RESULTS] ADD: {summary['action_breakdown']['ADD']}, "
                   f"MODIFY: {summary['action_breakdown']['MODIFY']}, "
                   f"DELETE: {summary['action_breakdown']['DELETE']}")
        
        if modify_in_place:
            logger.info(f"[EXPORT] Modified QTEST file saved to: {output_file}")
        else:
            logger.info(f"[EXPORT] Test modifications saved to: {output_file}")
        logger.info(f"[EXPORT] Summary report saved to: {summary_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"[ERROR] Test step generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_type": "TEST_STEP_GENERATION"
        }


def main():
    """Main entry point"""
    
    parser = setup_cli_parser()
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level, args.log_file)
    
    # Handle save default config command
    if args.save_default_config:
        save_default_config()
        return 0
    
    # Load configuration
    config = load_config(args.config)
    
    logger.info("[START] STTM Impact Analysis Tool - Phase 1")
    logger.info(f"Log level: {args.log_level}")
    
    try:
        # Execute the requested command
        if args.parse_sttm:
            results = parse_sttm_command(args.parse_sttm, logger, args.output_format)
        
        elif args.parse_qtest:
            results = parse_qtest_command(args.parse_qtest, logger, args.output_format, 
                                        args.detect_id_pattern)
        
        elif args.parse_both:
            sttm_file, qtest_file = args.parse_both
            results = parse_both_command(sttm_file, qtest_file, logger, args.output_format)
        
        elif args.validate:
            sttm_file, qtest_file = args.validate
            results = parse_both_command(sttm_file, qtest_file, logger, 'detailed')
        
        elif args.analyze_impact:
            sttm_file, qtest_file = args.analyze_impact
            results = analyze_impact_command(sttm_file, qtest_file, args.config, logger)
        
        elif args.generate_config:
            results = generate_config_command(args.generate_config, args.config_output, logger)
        
        elif args.generate_test_steps:
            sttm_file, qtest_file = args.generate_test_steps
            results = generate_test_steps_command(sttm_file, qtest_file, args.config, args.modify_in_place, logger)
        
        # Output results
        output_results(results, args.output_format, args.output, logger)
        
        # Return appropriate exit code
        return 0 if results.get("success", False) else 1
        
    except KeyboardInterrupt:
        logger.info("[STOP] Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"[FATAL] Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
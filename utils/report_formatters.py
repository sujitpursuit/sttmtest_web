"""
Report Formatters - Generate HTML and detailed JSON reports for impact analysis
"""

import json
from datetime import datetime
from typing import Dict, Any
from models.impact_models import ImpactAnalysisReport


def generate_html_report(report: ImpactAnalysisReport) -> str:
    """Generate HTML report from impact analysis results"""
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STTM Impact Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #007acc;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #007acc;
            margin: 0;
            font-size: 2.5em;
        }}
        .subtitle {{
            color: #666;
            font-size: 1.1em;
            margin-top: 10px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #007acc, #0099ff);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0;
            font-size: 2em;
        }}
        .summary-card p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .impact-level {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .critical {{ background-color: #dc3545; color: white; }}
        .high {{ background-color: #fd7e14; color: white; }}
        .medium {{ background-color: #ffc107; color: black; }}
        .low {{ background-color: #28a745; color: white; }}
        .tab-section {{
            margin: 40px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }}
        .tab-header {{
            background-color: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #ddd;
        }}
        .tab-header h2 {{
            margin: 0;
            color: #007acc;
            font-size: 1.5em;
        }}
        .tab-meta {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .test-cases {{
            padding: 20px;
        }}
        .test-case {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .test-case-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .test-case-id {{
            font-weight: bold;
            color: #007acc;
        }}
        .test-case-details {{
            font-size: 0.9em;
            color: #666;
        }}
        .affected-steps {{
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
        }}
        .steps-list {{
            margin: 5px 0;
            font-family: monospace;
            color: #495057;
        }}
        .score-breakdown {{
            font-size: 0.85em;
            color: #6c757d;
            margin-top: 10px;
        }}
        .no-impact {{
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 20px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>STTM Impact Analysis Report</h1>
            <div class="subtitle">
                Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
                STTM File: {report.sttm_file}<br>
                QTest File: {report.qtest_file}
            </div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>{report.total_test_cases_analyzed}</h3>
                <p>Test Cases Analyzed</p>
            </div>
            <div class="summary-card">
                <h3>{report.total_sttm_changes}</h3>
                <p>STTM Changes</p>
            </div>
            <div class="summary-card">
                <h3>{report.total_critical_impact + report.total_high_impact}</h3>
                <p>Priority Impacts</p>
            </div>
            <div class="summary-card">
                <h3>{report.total_sttm_tabs_analyzed}</h3>
                <p>STTM Tabs Analyzed</p>
            </div>
        </div>
        
        <div class="impact-summary">
            <h2>Impact Breakdown</h2>
            <div class="summary-grid">
                <div class="summary-card" style="background: linear-gradient(135deg, #dc3545, #e74c3c);">
                    <h3>{report.total_critical_impact}</h3>
                    <p>Critical Impact</p>
                </div>
                <div class="summary-card" style="background: linear-gradient(135deg, #fd7e14, #f39c12);">
                    <h3>{report.total_high_impact}</h3>
                    <p>High Impact</p>
                </div>
                <div class="summary-card" style="background: linear-gradient(135deg, #ffc107, #f1c40f);">
                    <h3>{report.total_medium_impact}</h3>
                    <p>Medium Impact</p>
                </div>
                <div class="summary-card" style="background: linear-gradient(135deg, #28a745, #27ae60);">
                    <h3>{report.total_low_impact}</h3>
                    <p>Low Impact</p>
                </div>
            </div>
        </div>
"""

    # Add detailed tab analysis
    for tab_summary in report.tab_summaries:
        html += f"""
        <div class="tab-section">
            <div class="tab-header">
                <h2>{tab_summary.tab_name}</h2>
                <div class="tab-meta">
                    Change Type: {tab_summary.change_type} | 
                    Total Changes: {tab_summary.total_changes}
                </div>
            </div>
            <div class="test-cases">
        """
        
        # Add test cases for each impact level
        impact_levels = [
            ("Critical", tab_summary.critical_impact_tests, "critical"),
            ("High", tab_summary.high_impact_tests, "high"),
            ("Medium", tab_summary.medium_impact_tests, "medium"),
            ("Low", tab_summary.low_impact_tests, "low")
        ]
        
        has_impacts = any(len(tests) > 0 for _, tests, _ in impact_levels)
        
        if not has_impacts:
            html += '<div class="no-impact">No test cases impacted by this tab</div>'
        else:
            for level_name, test_cases, level_class in impact_levels:
                if test_cases:
                    html += f'<h3>{level_name} Impact ({len(test_cases)} test cases)</h3>'
                    
                    for test_case in test_cases:
                        steps_text = f"Steps {', '.join(map(str, test_case.affected_step_numbers))}" if test_case.affected_step_numbers else "No specific steps identified"
                        
                        html += f"""
                        <div class="test-case">
                            <div class="test-case-header">
                                <span class="test-case-id">{test_case.test_case_id}</span>
                                <span class="impact-level {level_class}">{test_case.impact_score.impact_level.value}</span>
                            </div>
                            <div class="test-case-details">
                                <strong>Test Name:</strong> {test_case.test_case_name[:100]}{'...' if len(test_case.test_case_name) > 100 else ''}<br>
                                <strong>Change Summary:</strong> {test_case.sttm_change_summary}
                            </div>
                            <div class="affected-steps">
                                <strong>Affected Steps:</strong> {steps_text}
                            </div>
                            <div class="score-breakdown">
                                <strong>Score:</strong> {test_case.impact_score.total_points} points |
                                <strong>Reasoning:</strong> {', '.join([r.reason for r in test_case.impact_score.scoring_reasons]) if test_case.impact_score.scoring_reasons else 'No detailed reasoning available'}
                            </div>
                        </div>
                        """
        
        html += """
            </div>
        </div>
        """
    
    html += f"""
        <div class="footer">
            <p>Report generated by STTM Impact Analysis Tool v{report.tab_summaries[0].critical_impact_tests[0].analyzer_version if report.tab_summaries and report.tab_summaries[0].critical_impact_tests else "2.0"}</p>
            <p>Analysis completed at {report.analysis_timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def generate_detailed_json_report(report: ImpactAnalysisReport) -> str:
    """Generate detailed JSON report from impact analysis results"""
    report_dict = report.to_dict()
    return json.dumps(report_dict, indent=2, ensure_ascii=False)


def save_json_report(report: ImpactAnalysisReport, file_path: str) -> None:
    """Save JSON report to file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(generate_detailed_json_report(report))


def save_html_report(report: ImpactAnalysisReport, file_path: str) -> None:
    """Save HTML report to file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(generate_html_report(report))
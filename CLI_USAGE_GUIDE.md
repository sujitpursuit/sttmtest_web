# STTM Impact Analysis Tool - Complete CLI Usage Guide

## 🎯 **Primary Commands with Outputs**

### **1. Phase 3B Test Step Generation (Most Common)**

#### **Delta Mode (Traditional)**
```bash
python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx
```
**Arguments:**
- `--generate-test-steps`: Main Phase 3B command for test step generation
- `STTMDIFF_V2.json`: Your STTM difference file (input)
- `QTEST_STTM.xlsx`: Your QTEST test case file (input)

**Output Files:**
```
reports/
├── test_modifications_from_qtest_20250902_121653.xlsx    # Main delta file with ADD/MODIFY/DELETE actions
└── test_modifications_summary_20250902_121653.xlsx       # Summary statistics report
```

**Console Output:**
```
INFO: [SUCCESS] Generated 6 test step modifications (delta file)
INFO: [RESULTS] ADD: 4, MODIFY: 2, DELETE: 0
INFO: [EXPORT] Test modifications saved to: reports\test_modifications_from_qtest_20250902_121653.xlsx
INFO: [EXPORT] Summary report saved to: reports\test_modifications_summary_20250902_121653.xlsx
```

#### **In-Place Mode (Enhanced)** 🆕
```bash
python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx --modify-in-place
```
**Arguments:**
- `--modify-in-place`: **NEW FLAG** - Modifies copy of original QTEST file directly
- Same STTM and QTEST inputs as delta mode

**Output Files:**
```
reports/
├── modified_20250902_133639_QTEST_STTM.xlsx             # Complete updated QTEST file (ready to use)
└── test_modifications_summary_20250902_133639.xlsx      # Summary statistics report
```

**Console Output:**
```
INFO: [SUCCESS] Generated 6 test step modifications (in-place modifications)
INFO: [RESULTS] ADD: 4, MODIFY: 2, DELETE: 0
INFO: [EXPORT] Modified QTEST file saved to: reports\modified_20250902_133639_QTEST_STTM.xlsx
INFO: [EXPORT] Summary report saved to: reports\test_modifications_summary_20250902_133639.xlsx
```

---

## 🔧 **Advanced Options with Outputs**

### **With Custom Configuration**
```bash
python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx --config my_config.json
```
**Arguments:**
- `--config my_config.json`: Use custom impact analysis settings instead of defaults

**Output Files:** Same as delta mode above  
**Console Output:** Includes configuration info
```
INFO: [CONFIG] Using configuration from: my_config.json
INFO: [SUCCESS] Generated X test step modifications (delta file)
...
```

### **With Logging Options**
```bash
python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx --log-level DEBUG --log-file analysis.log
```
**Arguments:**
- `--log-level DEBUG`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--log-file analysis.log`: Save logs to specific file

**Output Files:**
```
reports/
├── test_modifications_from_qtest_YYYYMMDD_HHMMSS.xlsx   # Same as delta mode
├── test_modifications_summary_YYYYMMDD_HHMMSS.xlsx      # Same as delta mode
└── analysis.log                                         # Detailed log file
```

### **Combined Advanced Example**
```bash
python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx --modify-in-place --config balanced_config.json --log-level INFO
```

**Output Files:**
```
reports/
├── modified_YYYYMMDD_HHMMSS_QTEST_STTM.xlsx             # In-place modified file
└── test_modifications_summary_YYYYMMDD_HHMMSS.xlsx      # Summary report
```

---

## 📊 **Other Available Commands with Outputs**

### **Phase 2 Impact Analysis Only**
```bash
python main.py --analyze-impact STTMDIFF_V2.json QTEST_STTM.xlsx
```
**Purpose**: Run only impact analysis without test step generation

**Output Files:**
```
reports/
├── impact_analysis_STTMDIFF_V2_20250902_121653.json     # Detailed JSON impact report
└── impact_analysis_STTMDIFF_V2_20250902_121653.html     # Professional HTML report
```

**Console Output:**
```
INFO: Impact analysis completed in 0.43 seconds
INFO: Results: 3 high-priority impacts found
INFO: Tab 'VendorInboundVendorProxytoD365': 1 test cases affected
INFO: [EXPORT] Impact analysis report saved to: reports\impact_analysis_STTMDIFF_V2_20250902_121653.json
INFO: [EXPORT] HTML report saved to: reports\impact_analysis_STTMDIFF_V2_20250902_121653.html
```

### **File Validation**
```bash
python main.py --validate STTMDIFF_V2.json QTEST_STTM.xlsx
```
**Purpose**: Check if files can be parsed correctly

**Output Files:** None (validation only)

**Console Output:**
```
INFO: [STTM] Successfully parsed STTM document using Excel Comparison Tool v2.0
INFO: Found 3 changed tabs, 3 unchanged tabs
INFO: [QTEST] Successfully parsed using QTEST Excel Export Format
INFO: Parsed 1 test cases with 34 total steps
INFO: Detected ID pattern: TC-#### format
INFO: [SUCCESS] Both files validated successfully
```

### **Generate Configuration Files**
```bash
python main.py --generate-config balanced --config-output my_config.json
```
**Arguments:**
- `balanced`: Configuration preset (balanced, conservative, aggressive, strict)
- `--config-output my_config.json`: Output filename for generated config

**Output Files:**
```
my_config.json                                           # Generated configuration file
```

**Console Output:**
```
INFO: [CONFIG] Generated 'balanced' configuration
INFO: [EXPORT] Configuration saved to: my_config.json
INFO: [SUCCESS] Configuration file generated successfully
```

### **Parse Individual Files**
```bash
# Parse STTM file only
python main.py --parse-sttm STTMDIFF_V2.json

# Parse QTEST file only
python main.py --parse-qtest QTEST_STTM.xlsx

# Parse both files
python main.py --parse-both STTMDIFF_V2.json QTEST_STTM.xlsx
```

**Output Files:** None (parsing/validation only)

**Console Output:** Parsing results and file structure information

### **Get Help**
```bash
python main.py --help
```
**Purpose**: Show all available commands and options

**Output:** Complete help text to console

---

## 📁 **Output File Details**

### **Delta Mode Output Files**
| File | Content | Purpose |
|------|---------|---------|
| `test_modifications_from_qtest_YYYYMMDD_HHMMSS.xlsx` | ADD/MODIFY/DELETE actions in QTEST format with Action column | QA team applies changes manually |
| `test_modifications_summary_YYYYMMDD_HHMMSS.xlsx` | Statistics and breakdown of generated steps | Management reporting |

### **In-Place Mode Output Files**
| File | Content | Purpose |
|------|---------|---------|
| `modified_YYYYMMDD_HHMMSS_QTEST_STTM.xlsx` | Complete updated test case file with all changes applied | QA team uses directly |
| `test_modifications_summary_YYYYMMDD_HHMMSS.xlsx` | Statistics and breakdown of generated steps | Management reporting |

### **Impact Analysis Output Files**
| File | Content | Purpose |
|------|---------|---------|
| `impact_analysis_STTMDIFF_V2_YYYYMMDD_HHMMSS.json` | Detailed impact analysis with scoring reasons | Technical analysis |
| `impact_analysis_STTMDIFF_V2_YYYYMMDD_HHMMSS.html` | Professional formatted report with color coding | Business presentation |

### **File Naming Convention**
- `YYYYMMDD`: Date (20250902)
- `HHMMSS`: Time (121653)
- All output files in `reports/` directory
- Original files never modified (always preserved)

---

## 🎯 **Most Common Usage Scenarios with Expected Outputs**

### **Scenario 1: QA Team Wants Delta File**
```bash
python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx
```
**Expected Output:**
- Excel file with ADD/MODIFY/DELETE instructions
- QA team reviews and applies changes manually
- Instructions sheet included for guidance

### **Scenario 2: QA Team Wants Complete Updated File** 🆕
```bash
python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx --modify-in-place
```
**Expected Output:**
- Complete QTEST file with all changes already applied
- New test steps added at end (35+)
- Existing steps modified in-place
- Ready for immediate use in QA process

### **Scenario 3: Business Analyst Wants Impact Analysis**
```bash
python main.py --analyze-impact STTMDIFF_V2.json QTEST_STTM.xlsx
```
**Expected Output:**
- Professional HTML report for management
- Detailed JSON report for technical analysis
- Impact scores and affected test case identification

### **Scenario 4: First Time Setup/Validation**
```bash
python main.py --validate STTMDIFF_V2.json QTEST_STTM.xlsx
```
**Expected Output:**
- Console confirmation that files are compatible
- No output files (validation only)
- Error messages if files have issues

---

## ⚡ **Quick Start Examples with Outputs**

### **Basic In-Place Usage (Recommended)**
```bash
python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx --modify-in-place
```
**You'll Get:**
- `reports/modified_YYYYMMDD_HHMMSS_QTEST_STTM.xlsx` (ready to use)
- `reports/test_modifications_summary_YYYYMMDD_HHMMSS.xlsx` (statistics)

### **Basic Delta Usage (Traditional)**
```bash
python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx
```
**You'll Get:**
- `reports/test_modifications_from_qtest_YYYYMMDD_HHMMSS.xlsx` (instructions to apply)
- `reports/test_modifications_summary_YYYYMMDD_HHMMSS.xlsx` (statistics)

### **Impact Analysis Only**
```bash
python main.py --analyze-impact STTMDIFF_V2.json QTEST_STTM.xlsx
```
**You'll Get:**
- `reports/impact_analysis_STTMDIFF_V2_YYYYMMDD_HHMMSS.html` (business report)
- `reports/impact_analysis_STTMDIFF_V2_YYYYMMDD_HHMMSS.json` (technical details)

---

## 🔍 **Complete Argument Reference**

| Argument | Type | Required/Optional | Purpose | Example |
|----------|------|------------------|---------|---------|
| `--generate-test-steps` | Action | **Required** (main action) | Generate test step modifications | `--generate-test-steps STTM.json QTEST.xlsx` |
| `--modify-in-place` | Flag | **Optional** | Create complete updated file instead of delta | `--modify-in-place` |
| `--analyze-impact` | Action | **Required** (alternative action) | Run impact analysis only | `--analyze-impact STTM.json QTEST.xlsx` |
| `--validate` | Action | **Required** (alternative action) | Validate file parsing | `--validate STTM.json QTEST.xlsx` |
| `--config` | File path | **Optional** | Use custom configuration settings | `--config my_config.json` |
| `--log-level` | Choice | **Optional** | Control logging verbosity | `--log-level DEBUG` |
| `--log-file` | File path | **Optional** | Save logs to specific file | `--log-file analysis.log` |
| `--output` | File path | **Optional** | Custom output location | `--output my_results.json` |
| `--help` | Flag | **Optional** | Show help information | `--help` |

---

## 📋 **Expected Output Summary**

### **Success Indicators**
- Console shows: `[SUCCESS] Generated X test step modifications`
- Console shows: `[EXPORT] ... saved to: reports\filename.xlsx`
- Files appear in `reports/` directory with timestamps
- No error messages in console output

### **Common Output Patterns**
- **Delta Mode**: 2 files (modifications + summary)
- **In-Place Mode**: 2 files (modified QTEST + summary)  
- **Impact Analysis**: 2 files (JSON + HTML reports)
- **Validation**: Console output only, no files

### **File Sizes (Typical)**
- **Summary files**: 10-50KB (statistics and charts)
- **Delta files**: 20-200KB (depends on number of modifications)
- **In-place files**: Similar to original QTEST file size
- **Impact reports**: 50-500KB (depends on analysis depth)

**All output files are ready for immediate use by QA teams and management!**
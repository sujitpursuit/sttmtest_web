# STTM Impact Analysis - Configuration Guide

## 📋 **Quick Start**

The impact analysis system uses a **simple points-based scoring** approach that business users can easily understand and configure.

### **Basic Concept**
> *"For each test case, we ask simple questions. Each 'yes' adds points. More points = higher impact."*

---

## 🎯 **Scoring Parameters Explained**

### **1. Change Type Points** 
*Points awarded based on what type of STTM change occurred*

```json
"deleted_field_points": 5     // HIGH IMPACT: Deleted fields usually break tests
"modified_field_points": 3    // MEDIUM IMPACT: Changed fields might break tests  
"added_field_points": 1       // LOW IMPACT: New fields rarely break existing tests
```

**Real Examples:**
- **Deleted Field**: STTM removed "VendorID" → Existing tests checking VendorID will fail → **5 points**
- **Modified Field**: STTM changed VendorID format from "12345" to "VEND-12345" → Tests might need updating → **3 points**
- **Added Field**: STTM added new "VendorCategory" → Existing tests still work → **1 point**

### **2. Text Matching Points**
*Points awarded when test cases mention STTM changes*

```json
"tab_name_match_points": 3        // Test mentions the changed STTM tab
"exact_tab_match_points": 2       // Bonus for exact tab name match
"partial_tab_match_points": 1     // Bonus for partial tab name match  
"field_name_match_points": 2      // Test mentions changed field names
"sample_data_match_points": 3     // Test mentions changed sample data
```

**Real Examples:**
- **Tab Match**: Test "Validate DACH vendor processing" mentions "DACH" when tab "Vendor Inbound DACH VenProxy" changed → **1-2 points**
- **Field Match**: Test description contains "VendorID" and VendorID was modified → **2 points**
- **Sample Data**: Test checks for "12345" and STTM shows sample changed to "VEND-12345" → **3 points**

### **3. Impact Level Thresholds**
*Point ranges that determine final impact level*

```json
"critical_threshold": 12    // 12+ points = CRITICAL (update immediately)
"high_threshold": 8         // 8-11 points = HIGH (update required)
"medium_threshold": 4       // 4-7 points = MEDIUM (review recommended)
"low_threshold": 0          // 0-3 points = LOW (monitor)
```

---

## 🔧 **Configuration Examples**

### **Example 1: Conservative Configuration**
*Flags more tests as high impact*

```json
{
  "scoring": {
    "deleted_field_points": 6,        // Higher penalty for deletions
    "modified_field_points": 4,       // Higher penalty for modifications
    "critical_threshold": 10,         // Lower threshold = more critical tests
    "high_threshold": 6,              // Lower threshold = more high impact tests
    "medium_threshold": 3
  }
}
```

**Use When:** You want to be extra careful and review more test cases

### **Example 2: Aggressive Configuration**  
*Flags fewer tests as high impact*

```json
{
  "scoring": {
    "deleted_field_points": 4,        // Lower penalty for deletions
    "modified_field_points": 2,       // Lower penalty for modifications  
    "critical_threshold": 15,         // Higher threshold = fewer critical tests
    "high_threshold": 10,             // Higher threshold = fewer high impact tests
    "medium_threshold": 6
  }
}
```

**Use When:** You have many tests and want to focus only on the most obvious impacts

### **Example 3: Strict Matching**
*Only flags very obvious impacts*

```json
{
  "scoring": {
    "case_sensitive_matching": true,   // Exact case matching required
    "minimum_keyword_length": 4,       // Ignore short words
    "critical_threshold": 20,          // Very high thresholds
    "high_threshold": 12,
    "medium_threshold": 8
  }
}
```

**Use When:** You want very precise matching with minimal false positives

---

## 📊 **Scoring Examples**

### **High Impact Scenario**
```
STTM Change: Deleted "VendorID" field from "Vendor Inbound DACH" tab
Test Case: "TC-001: Validate DACH vendor ID processing"

Scoring:
✓ Test mentions "DACH" (partial tab match)     → +1 point
✓ Field was deleted                            → +5 points  
✓ Test mentions "vendor ID" (field reference)  → +2 points
✓ High confidence match                        → +0 points
────────────────────────────────────────────────────────
Total: 8 points = HIGH IMPACT
Action: Update Required
```

### **Medium Impact Scenario**
```
STTM Change: Modified "VendorCode" format in "Customer Processing" tab  
Test Case: "TC-002: Customer data validation"

Scoring:
✓ Test mentions "Customer" (partial tab match) → +1 point
✓ Field was modified                           → +3 points
✗ No field name references found              → +0 points
✗ No sample data references found             → +0 points  
────────────────────────────────────────────────────────
Total: 4 points = MEDIUM IMPACT
Action: Review Recommended
```

### **Low Impact Scenario**
```
STTM Change: Added "NewField" to "Payment Processing" tab
Test Case: "TC-003: User login validation"

Scoring:
✗ No tab name matches                          → +0 points
✓ Field was added                              → +1 point
✗ No field references                          → +0 points
✗ No sample data references                    → +0 points
────────────────────────────────────────────────────────
Total: 1 point = LOW IMPACT  
Action: Monitor
```

---

## ⚙️ **Tuning Your Configuration**

### **If you're getting too many HIGH impacts:**
1. **Raise thresholds**: `"high_threshold": 10` instead of `8`
2. **Lower change penalties**: `"deleted_field_points": 4` instead of `5`  
3. **Stricter matching**: `"case_sensitive_matching": true`

### **If you're missing important impacts:**
1. **Lower thresholds**: `"high_threshold": 6` instead of `8`
2. **Higher change penalties**: `"deleted_field_points": 6` instead of `5`
3. **Looser matching**: `"minimum_keyword_length": 2` instead of `3`

### **For different environments:**

| Environment | Configuration Style | Threshold Settings |
|-------------|--------------------|--------------------|
| **Production** | Conservative | Lower thresholds, higher penalties |
| **Development** | Balanced | Default settings |
| **Testing** | Aggressive | Higher thresholds, lower penalties |
| **Compliance** | Strict | Case-sensitive, high thresholds |

---

## 🔍 **Testing Your Configuration**

### **1. Use Sample Configuration Files**
```bash
# Generated sample files:
sample_conservative_config.json    # More sensitive
sample_balanced_config.json        # Default settings  
sample_aggressive_config.json      # Less sensitive
sample_strict_config.json         # High precision
```

### **2. Test with Your Data**
```python
from analyzers.impact_analyzer import QuickImpactAnalyzer

analyzer = QuickImpactAnalyzer("your_config.json")
summary = analyzer.quick_check("STTM_DIFF.json", "QTEST_STTM.xlsx")
print(summary)
```

### **3. Preview Scoring**
```python  
from analyzers.impact_scorer import BusinessFriendlyScorer
from models.impact_models import ImpactAnalysisConfig

config = ImpactAnalysisConfig.load_from_file("your_config.json")  
scorer = BusinessFriendlyScorer(config)

# Test different scenarios
preview = scorer.get_scoring_preview(
    deleted_fields=1, modified_fields=0, added_fields=0,
    tab_match=True, field_references=1, sample_references=0
)
print(preview)
```

---

## 📁 **Configuration Files**

### **Main Configuration Files:**
- `sample_documented_config.json` - Fully documented example with explanations
- `sample_balanced_config.json` - Ready-to-use balanced configuration
- `phase2_config.json` - Your customized configuration (create this)

### **Using Configuration Files:**
```bash
# Run impact analysis with custom config
python main.py --analyze-impact --config phase2_config.json

# Generate impact reports with specific settings  
python main.py --impact-report --config sample_conservative_config.json
```

---

## 🎯 **Best Practices**

1. **Start with Balanced**: Use `sample_balanced_config.json` as your starting point
2. **Test First**: Always test your configuration with sample data before using in production  
3. **Document Changes**: Keep notes on why you changed specific parameters
4. **Review Results**: Check if the impact levels match your expectations
5. **Iterate**: Adjust thresholds based on real-world results

The configuration system is designed to be **business-user friendly** - you don't need to be a programmer to tune the impact analysis for your needs!
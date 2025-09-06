# Phase 3B Final Implementation Plan - Test Step Generation

## 🎯 **Confirmed Requirements** 

**User Decision**: All requirements confirmed with finalized deleted field handling approach.

### **Core Functionality**
1. ✅ Generate NEW test steps for added STTM fields
2. ✅ MODIFY existing test steps that reference modified fields  
3. ✅ Generate NEW verification steps for deleted fields
4. ✅ **IDENTIFY and FLAG existing steps that reference deleted fields for DELETION**
5. ✅ Export to Excel with same structure as QTEST_STTM.xlsx
6. ✅ Add Action column (ADD/MODIFY/DELETE) for clear instructions

## 📊 **Excel Output Structure**

### **File**: `test_modifications_YYYYMMDD_HHMMSS.xlsx`

**Columns**: Name | Id | Description | Precondition | Test Step # | Test Step Description | Test Step Expected Result | **Action**

### **Action Types**
- **ADD**: New test step to be added
- **MODIFY**: Existing test step to be updated  
- **DELETE**: Existing test step to be removed (references deleted STTM field)

## 🔧 **Step Generation Logic - FINALIZED**

### **For DELETED Fields (e.g., ZipCode)**
1. **Generate NEW verification step**:
   - Description: "Verify ZipCode field has been removed from VendorPostalAddress"
   - Expected: "ZipCode field should not exist in target system"
   - Action: **ADD**

2. **Identify existing steps for deletion**:
   - Search current test steps for ZipCode references
   - Mark found steps with Action: **DELETE** 
   - Include note: "References deleted field ZipCode"

### **For ADDED Fields (e.g., LineThree → Street2)**
- Description: "Validate LineThree mapping to Street2 field"
- Expected: "LineThree value correctly mapped to VendorPostalAddress.Street2"  
- Step #: Next available (35, 36, 37...)
- Action: **ADD**

### **For MODIFIED Fields (e.g., VIN sample data changed)**
- Find existing step that references VIN (Step 11)
- Update expected result with new sample data
- Keep same step number (11)
- Action: **MODIFY**

## 📋 **Expected Output Example**

Based on STTMDIFF_V2.json, the generated Excel will contain:

| Step # | Description | Expected Result | Action | Reference |
|--------|-------------|-----------------|---------|-----------|
| 35 | **NEW**: Verify ZipCode field removed | ZipCode field should not exist | **ADD** | Deleted field verification |
| 34 | [Current ZipCode step] | [Current expected result] | **DELETE** | References deleted ZipCode |
| 36 | **NEW**: Validate LineThree → Street2 | LineThree mapped to Street2 | **ADD** | New field mapping |
| 37 | **NEW**: Validate LineFour → StreetNumber2 | LineFour mapped to StreetNumber2 | **ADD** | New field mapping |
| 11 | [Current VIN step] | **UPDATED**: New VIN sample data | **MODIFY** | Modified field update |

## 🏗️ **Implementation Components**

### **New Files to Create**
```
STTMQTEST/
├── generators/
│   ├── __init__.py                    # NEW
│   ├── test_step_generator.py         # NEW - Core generation logic
│   └── test_modification_exporter.py  # NEW - Excel export with Action column
│
├── templates/
│   ├── __init__.py                    # NEW  
│   └── step_templates.py              # NEW - ADD/MODIFY/DELETE templates
│
└── utils/
    └── step_reference_finder.py       # NEW - Find existing steps referencing deleted fields
```

### **New CLI Command**
```bash
python main.py --generate-test-steps STTMDIFF_V2.json QTEST_STTM.xlsx
```

### **Output Location**
```
reports/test_modifications_YYYYMMDD_HHMMSS.xlsx
```

## 🎯 **Implementation Priority**

### **Phase 1**: Core Generation Logic
- Build step generation templates for ADD/MODIFY/DELETE
- Implement field reference finder for existing test steps
- Create basic Excel export functionality

### **Phase 2**: Integration & Testing  
- Integrate with current impact analysis results
- Add CLI command to main.py
- Test with real STTMDIFF_V2.json data

### **Phase 3**: Polish & Validation
- Add Action column formatting
- Validate Excel structure matches QTEST format
- Test complete workflow end-to-end

## ✅ **Success Criteria**

1. ✅ Excel output has identical column structure to QTEST_STTM.xlsx
2. ✅ Action column clearly identifies ADD/MODIFY/DELETE operations
3. ✅ All STTM changes result in appropriate test step actions
4. ✅ Deleted field logic generates both verification steps AND identifies obsolete steps
5. ✅ No impact on existing impact analysis functionality
6. ✅ QA team can directly use output to update test cases

## 🔒 **Constraints**

- **No impact** on existing JSON/HTML report generation
- **Same CLI interface** for current functionality
- **Separate output file** - does not modify existing reports
- **Maintains** current system architecture and adapter patterns

## 📅 **Ready for Implementation**

All requirements confirmed. Implementation can proceed with:
- Clear step generation logic for all STTM change types
- Finalized deleted field handling (ADD verification + DELETE existing)
- Excel output format specification
- Action column for clear QA team instructions

**Status**: Ready to implement when development resumes.
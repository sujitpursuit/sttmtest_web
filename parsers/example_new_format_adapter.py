"""
Example: New STTM Format Adapter

This demonstrates how to add support for a new STTM format without touching
any other code. Simply create a new adapter and register it.

Example scenario: STTM tool updates to v3.0 with different JSON structure
"""

from typing import Dict, List, Any, Optional
import logging

from parsers.sttm_format_adapter import STTMFormatAdapter, RawTabData, RawMappingData


class NewSTTMFormatV3Adapter(STTMFormatAdapter):
    """
    Adapter for hypothetical STTM v3.0 format
    
    Example new format structure:
    {
        "version": "3.0",
        "comparison_result": {
            "modified_worksheets": [
                {
                    "worksheet_name": "...",
                    "change_summary": "...",
                    "row_changes": [
                        {
                            "change_action": "INSERT|UPDATE|DELETE",
                            "source_column": "...",
                            "target_column": "...",
                            "before": "...",
                            "after": "..."
                        }
                    ]
                }
            ]
        }
    }
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def get_format_version(self) -> str:
        return "STTM Comparison Tool v3.0"
    
    def validate_format(self, json_data: Dict[str, Any]) -> bool:
        """Validate v3.0 format structure"""
        return (
            json_data.get("version") == "3.0" and 
            "comparison_result" in json_data and
            "modified_worksheets" in json_data.get("comparison_result", {})
        )
    
    def extract_raw_data(self, json_data: Dict[str, Any]) -> List[RawTabData]:
        """Extract data from v3.0 format"""
        
        raw_tabs = []
        
        comparison_result = json_data.get("comparison_result", {})
        modified_worksheets = comparison_result.get("modified_worksheets", [])
        
        for worksheet in modified_worksheets:
            raw_tab = self._extract_v3_tab_data(worksheet)
            raw_tabs.append(raw_tab)
        
        self.logger.debug(f"Extracted {len(raw_tabs)} tabs from v3.0 format")
        return raw_tabs
    
    def _extract_v3_tab_data(self, worksheet_data: Dict[str, Any]) -> RawTabData:
        """Extract tab data from v3.0 format"""
        
        raw_tab = RawTabData(
            name=worksheet_data.get("worksheet_name", "Unknown"),
            change_type=self._determine_v3_change_type(worksheet_data)
        )
        
        # Extract mappings from row changes
        row_changes = worksheet_data.get("row_changes", [])
        
        # Group changes by type
        added_mappings = []
        deleted_mappings = []
        modified_mappings = []
        
        for change in row_changes:
            action = change.get("change_action", "").upper()
            
            raw_mapping = RawMappingData(
                source_field=change.get("source_column", ""),
                target_field=change.get("target_column", ""),
                change_type=action.lower()
            )
            
            if action == "INSERT":
                raw_mapping.change_type = "added"
                added_mappings.append(raw_mapping)
            elif action == "DELETE":
                raw_mapping.change_type = "deleted"
                deleted_mappings.append(raw_mapping)
            elif action == "UPDATE":
                raw_mapping.change_type = "modified"
                raw_mapping.original_values = {"value": change.get("before")}
                raw_mapping.new_values = {"value": change.get("after")}
                raw_mapping.modified_fields = ["value"]
                modified_mappings.append(raw_mapping)
        
        raw_tab.added_mappings = added_mappings
        raw_tab.deleted_mappings = deleted_mappings
        raw_tab.modified_mappings = modified_mappings
        
        return raw_tab
    
    def _determine_v3_change_type(self, worksheet_data: Dict[str, Any]) -> str:
        """Determine change type from v3.0 format data"""
        
        row_changes = worksheet_data.get("row_changes", [])
        
        actions = set(change.get("change_action", "").upper() for change in row_changes)
        
        if len(actions) > 1:
            return "mixed"
        elif "INSERT" in actions:
            return "additions_only"
        elif "DELETE" in actions:
            return "deletions_only"
        elif "UPDATE" in actions:
            return "modifications_only"
        else:
            return "unchanged"


class SimpleSTTMFormatAdapter(STTMFormatAdapter):
    """
    Adapter for a simple/minimal STTM format
    
    Example simple format:
    {
        "format": "simple",
        "tabs": [
            {
                "name": "TabName",
                "changes": [
                    {
                        "type": "add|delete|modify",
                        "from": "source_field",
                        "to": "target_field"
                    }
                ]
            }
        ]
    }
    """
    
    def get_format_version(self) -> str:
        return "Simple STTM Format v1.0"
    
    def validate_format(self, json_data: Dict[str, Any]) -> bool:
        """Validate simple format"""
        return (
            json_data.get("format") == "simple" and 
            "tabs" in json_data
        )
    
    def extract_raw_data(self, json_data: Dict[str, Any]) -> List[RawTabData]:
        """Extract data from simple format"""
        
        raw_tabs = []
        
        tabs = json_data.get("tabs", [])
        
        for tab_data in tabs:
            raw_tab = RawTabData(
                name=tab_data.get("name", "Unknown"),
                change_type="mixed"  # Assume mixed for simple format
            )
            
            changes = tab_data.get("changes", [])
            
            # Group by change type
            added_mappings = []
            deleted_mappings = []
            modified_mappings = []
            
            for change in changes:
                change_type = change.get("type", "").lower()
                
                raw_mapping = RawMappingData(
                    source_field=change.get("from", ""),
                    target_field=change.get("to", ""),
                    change_type=change_type
                )
                
                if change_type == "add":
                    raw_mapping.change_type = "added"
                    added_mappings.append(raw_mapping)
                elif change_type == "delete":
                    raw_mapping.change_type = "deleted"
                    deleted_mappings.append(raw_mapping)
                elif change_type == "modify":
                    raw_mapping.change_type = "modified"
                    modified_mappings.append(raw_mapping)
            
            raw_tab.added_mappings = added_mappings
            raw_tab.deleted_mappings = deleted_mappings
            raw_tab.modified_mappings = modified_mappings
            
            raw_tabs.append(raw_tab)
        
        return raw_tabs
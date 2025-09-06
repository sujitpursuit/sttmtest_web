"""
STTM (Source-to-Target Mapping) data models for representing parsed STTM difference data.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class ChangeType(Enum):
    """Types of changes in STTM mappings"""
    ADDED = "added"
    DELETED = "deleted" 
    MODIFIED = "modified"


class TabChangeCategory(Enum):
    """Categories of changes at tab level"""
    MIXED = "mixed"
    MODIFICATIONS_ONLY = "modifications_only"
    ADDITIONS_ONLY = "additions_only"
    DELETIONS_ONLY = "deletions_only"
    UNCHANGED = "unchanged"


@dataclass
class STTMMapping:
    """Represents a single source-to-target mapping"""
    source_field: str
    target_field: str
    
    # Core mapping fields
    source_canonical_name: Optional[str] = None
    target_canonical_name: Optional[str] = None
    target_entity: Optional[str] = None
    
    # Additional metadata from V2 format
    source_description: Optional[str] = None
    source_type: Optional[str] = None
    target_type: Optional[str] = None
    target_length: Optional[str] = None
    source_sample_data: Optional[str] = None
    target_comments: Optional[str] = None
    completion_type: Optional[str] = None
    
    # Change tracking
    change_type: Optional[ChangeType] = None
    row_number: Optional[int] = None
    original_row_number: Optional[int] = None  # For deleted mappings
    
    # Field changes for modified mappings
    field_changes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    other_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"{self.source_field} -> {self.target_field}"


@dataclass 
class STTMTab:
    """Represents a tab in the STTM document with its mappings and changes"""
    name: str
    change_category: TabChangeCategory
    
    # Version metadata (V2 format)
    logical_name: Optional[str] = None
    physical_name_v1: Optional[str] = None
    physical_name_v2: Optional[str] = None
    version_v1: Optional[int] = None
    version_v2: Optional[int] = None
    
    # System information
    source_system: Optional[str] = None
    target_system: Optional[str] = None
    
    # All mappings in the tab
    all_mappings: List[STTMMapping] = field(default_factory=list)
    
    # Categorized mappings by change type
    added_mappings: List[STTMMapping] = field(default_factory=list)
    deleted_mappings: List[STTMMapping] = field(default_factory=list)
    modified_mappings: List[STTMMapping] = field(default_factory=list)
    unchanged_mappings: List[STTMMapping] = field(default_factory=list)
    
    def get_total_changes(self) -> int:
        """Get total number of changes in this tab"""
        return len(self.added_mappings) + len(self.deleted_mappings) + len(self.modified_mappings)
    
    def has_changes(self) -> bool:
        """Check if this tab has any changes"""
        return self.get_total_changes() > 0
    
    def get_change_summary(self) -> str:
        """Get a summary of changes in this tab"""
        changes = []
        if self.added_mappings:
            changes.append(f"{len(self.added_mappings)} added")
        if self.deleted_mappings:
            changes.append(f"{len(self.deleted_mappings)} deleted")
        if self.modified_mappings:
            changes.append(f"{len(self.modified_mappings)} modified")
        
        return ", ".join(changes) if changes else "no changes"
    
    def get_all_changed_mappings(self) -> List[STTMMapping]:
        """Get all mappings that have changes (added, deleted, modified)"""
        return self.added_mappings + self.deleted_mappings + self.modified_mappings
    
    def get_display_name(self) -> str:
        """Get display name showing logical name and physical names if different"""
        if not self.logical_name:
            return self.name
        
        if self.physical_name_v1 == self.physical_name_v2:
            # Physical names are the same
            if self.logical_name == self.physical_name_v1:
                return self.logical_name
            else:
                return f"{self.logical_name} (as '{self.physical_name_v1}')"
        else:
            # Physical names are different between versions
            return f"{self.logical_name} (v1: '{self.physical_name_v1}', v2: '{self.physical_name_v2}')"
    
    def has_version_changes(self) -> bool:
        """Check if tab has version-related changes (name or version number)"""
        return (self.physical_name_v1 != self.physical_name_v2 or 
                self.version_v1 != self.version_v2)


@dataclass
class STTMDocument:
    """Represents the complete STTM difference document"""
    
    # Tabs categorized by change status
    changed_tabs: List[STTMTab] = field(default_factory=list)
    unchanged_tabs: List[STTMTab] = field(default_factory=list)
    
    # Metadata
    total_tabs: int = 0
    total_mappings: int = 0
    total_changes: int = 0
    
    def get_all_tabs(self) -> List[STTMTab]:
        """Get all tabs (changed and unchanged)"""
        return self.changed_tabs + self.unchanged_tabs
    
    def get_tab_by_name(self, tab_name: str) -> Optional[STTMTab]:
        """Find a tab by name (case-insensitive)"""
        for tab in self.get_all_tabs():
            if tab.name.lower() == tab_name.lower():
                return tab
        return None
    
    def get_tabs_with_changes(self) -> List[STTMTab]:
        """Get only tabs that have changes"""
        return [tab for tab in self.changed_tabs if tab.has_changes()]
    
    def get_all_changed_mappings(self) -> List[STTMMapping]:
        """Get all mappings that have changes across all tabs"""
        changed_mappings = []
        for tab in self.changed_tabs:
            changed_mappings.extend(tab.added_mappings)
            changed_mappings.extend(tab.deleted_mappings)
            changed_mappings.extend(tab.modified_mappings)
        return changed_mappings
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the STTM document"""
        return {
            "total_tabs": len(self.get_all_tabs()),
            "changed_tabs": len(self.changed_tabs),
            "unchanged_tabs": len(self.unchanged_tabs),
            "total_changes": sum(tab.get_total_changes() for tab in self.changed_tabs),
            "tabs_by_change_type": {
                "additions_only": len([t for t in self.changed_tabs if t.change_category == TabChangeCategory.ADDITIONS_ONLY]),
                "deletions_only": len([t for t in self.changed_tabs if t.change_category == TabChangeCategory.DELETIONS_ONLY]),
                "modifications_only": len([t for t in self.changed_tabs if t.change_category == TabChangeCategory.MODIFICATIONS_ONLY]),
                "mixed": len([t for t in self.changed_tabs if t.change_category == TabChangeCategory.MIXED])
            }
        }
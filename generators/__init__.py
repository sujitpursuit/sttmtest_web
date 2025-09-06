"""
Test Step Generation Package

This package contains components for generating new test steps and modifications
based on STTM changes, following the confirmed approach:

- ADD: New verification steps for deleted fields and validation steps for added fields
- MODIFY: Update existing steps that reference modified fields
- DELETE: Flag existing steps that reference deleted fields for removal

Components:
- test_step_generator.py: Core step generation logic
- test_modification_exporter.py: Excel export functionality
- step_templates.py: Templates for different step types
- step_reference_finder.py: Find existing steps referencing specific fields
"""

from .test_step_generator import TestStepGenerator
from .step_reference_finder import StepReferenceFinder
from .test_modification_exporter import TestModificationExporter

__all__ = ['TestStepGenerator', 'StepReferenceFinder', 'TestModificationExporter']
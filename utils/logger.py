"""
Logging system for the STTM impact analysis tool.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class STTMLogger:
    """Enhanced logger for STTM analysis with structured output"""
    
    def __init__(self, name: str = "sttm_analyzer", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers with appropriate formatting"""
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Console formatter - clean for user-facing messages
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
        
        # File handler for detailed logging (optional)
        try:
            log_file = Path("sttm_analysis.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # File formatter - detailed for debugging
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            
            self.logger.addHandler(file_handler)
            
        except Exception:
            # If file logging fails, continue with console only
            pass
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        return self.logger
    
    def set_level(self, level: str):
        """Set the logging level"""
        self.logger.setLevel(getattr(logging, level.upper()))
    
    def log_parsing_start(self, file_type: str, file_path: str):
        """Log the start of file parsing"""
        self.logger.info(f"Parsing {file_type} file: {Path(file_path).name}")
    
    def log_parsing_complete(self, file_type: str, items_count: int, details: str = ""):
        """Log successful parsing completion"""
        self.logger.info(f"[SUCCESS] {file_type} parsing complete: {items_count} items processed")
        if details:
            self.logger.info(f"   {details}")
    
    def log_parsing_error(self, file_type: str, error: str):
        """Log parsing errors"""
        self.logger.error(f"[ERROR] {file_type} parsing failed: {error}")
    
    def log_pattern_detection(self, pattern_description: str, confidence: float):
        """Log ID pattern detection results"""
        confidence_level = "HIGH" if confidence > 0.8 else "MEDIUM" if confidence > 0.6 else "LOW"
        self.logger.info(f"[{confidence_level}] ID Pattern detected: {pattern_description} "
                        f"(confidence: {confidence:.1%})")
    
    def log_matching_summary(self, matches_found: int, total_items: int, match_type: str):
        """Log matching/analysis summary"""
        percentage = (matches_found / total_items * 100) if total_items > 0 else 0
        self.logger.info(f"[MATCH] {match_type} matching: {matches_found}/{total_items} matches ({percentage:.1f}%)")
    
    def log_impact_summary(self, high: int, medium: int, low: int):
        """Log impact analysis summary"""
        total = high + medium + low
        self.logger.info(f"[SUMMARY] Impact Analysis Complete:")
        self.logger.info(f"   HIGH impact: {high} test cases")
        self.logger.info(f"   MEDIUM impact: {medium} test cases")
        self.logger.info(f"   LOW impact: {low} test cases")
        self.logger.info(f"   Total analyzed: {total} test cases")
    
    def log_report_generation(self, report_type: str, output_path: str):
        """Log report generation"""
        self.logger.info(f"[REPORT] Generated {report_type} report: {Path(output_path).name}")
    
    def log_phase_start(self, phase_name: str):
        """Log the start of a processing phase"""
        self.logger.info(f"\n[START] Starting {phase_name}...")
    
    def log_phase_complete(self, phase_name: str):
        """Log the completion of a processing phase"""
        self.logger.info(f"[COMPLETE] {phase_name} completed successfully\n")


def get_logger(name: str = "sttm_analyzer", level: str = "INFO") -> logging.Logger:
    """Convenience function to get a configured logger"""
    sttm_logger = STTMLogger(name, level)
    return sttm_logger.get_logger()


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration for the application"""
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Optional file handler
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
    
    return root_logger
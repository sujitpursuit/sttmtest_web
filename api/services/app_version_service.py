"""
Application Version Service
Provides version information for the STTM QTest Impact Analysis Tool
"""

from datetime import datetime
import hashlib
from pathlib import Path

class AppVersionService:
    def __init__(self):
        self.version = "1.0.4"  # FIXED: Azure Blob ContentSettings error
        self.build_date = "2025-09-08"
        self.build_time = datetime.now().strftime("%H:%M:%S")
        
    def get_version_info(self):
        """Get complete version information"""
        # Generate a simple hash based on key files for build verification
        key_files = [
            "api/main.py",
            "frontend/js/app.js", 
            "frontend/index.html"
        ]
        
        build_hash = self._generate_build_hash(key_files)
        
        return {
            "version": self.version,
            "build_date": self.build_date,
            "build_time": self.build_time,
            "build_hash": build_hash[:8],  # Short hash for display
            "full_version": f"{self.version}-{self.build_date}-{build_hash[:8]}"
        }
    
    def _generate_build_hash(self, file_paths):
        """Generate a hash based on key application files"""
        hasher = hashlib.md5()
        base_path = Path(__file__).parent.parent.parent
        
        for file_path in file_paths:
            full_path = base_path / file_path
            if full_path.exists():
                with open(full_path, 'rb') as f:
                    hasher.update(f.read())
        
        return hasher.hexdigest()

# Global app version service instance
app_version_service = AppVersionService()
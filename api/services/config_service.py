"""
Configuration Service for FastAPI

Handles saving, loading, and managing custom analysis configurations.
Configurations are stored as JSON files in the output_files/configs directory.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from api.models.api_models import AnalysisConfig, ConfigSaveRequest, SavedConfigInfo
from api.utils.exceptions import ConfigurationError


class ConfigService:
    """Service for managing analysis configuration persistence"""
    
    def __init__(self, config_dir: str = "output_files/configs", logger: Optional[logging.Logger] = None):
        self.config_dir = config_dir
        self.logger = logger or logging.getLogger(__name__)
        self._ensure_config_directory()
    
    def _ensure_config_directory(self):
        """Ensure config directory exists"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            self.logger.debug(f"Config directory ensured: {self.config_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create config directory: {str(e)}")
            raise ConfigurationError(f"Failed to create config directory: {str(e)}")
    
    def save_config(self, request: ConfigSaveRequest) -> str:
        """
        Save a custom configuration
        
        Args:
            request: Configuration save request
            
        Returns:
            Configuration ID (filename without extension)
        """
        try:
            # Generate config ID (sanitize name for filename)
            config_id = self._sanitize_filename(request.name)
            
            # Check if config already exists
            config_path = os.path.join(self.config_dir, f"{config_id}.json")
            if os.path.exists(config_path):
                raise ConfigurationError(f"Configuration '{request.name}' already exists")
            
            # Prepare config data
            config_data = {
                "name": request.name,
                "description": request.description,
                "created_timestamp": datetime.now().isoformat(),
                "recommended_for": request.recommended_for,
                "config": request.config.dict()
            }
            
            # Save to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved configuration: {request.name} -> {config_id}")
            return config_id
            
        except ConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to save config '{request.name}': {str(e)}", exc_info=True)
            raise ConfigurationError(f"Failed to save configuration: {str(e)}")
    
    def get_config(self, config_id: str) -> Dict[str, Any]:
        """
        Load a saved configuration
        
        Args:
            config_id: Configuration identifier
            
        Returns:
            Configuration data
        """
        try:
            config_path = os.path.join(self.config_dir, f"{config_id}.json")
            
            if not os.path.exists(config_path):
                raise ConfigurationError(f"Configuration not found: {config_id}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.logger.debug(f"Retrieved configuration: {config_id}")
            return config_data
            
        except ConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to load config {config_id}: {str(e)}")
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")
    
    def get_config_settings_only(self, config_id: str) -> AnalysisConfig:
        """Get only the configuration settings as AnalysisConfig object"""
        config_data = self.get_config(config_id)
        config_settings = config_data.get("config", {})
        return AnalysisConfig(**config_settings)
    
    def list_configs(self) -> List[SavedConfigInfo]:
        """
        List all saved configurations
        
        Returns:
            List of configuration summaries
        """
        try:
            configs = []
            
            if not os.path.exists(self.config_dir):
                return configs
            
            for filename in os.listdir(self.config_dir):
                if filename.endswith('.json'):
                    config_id = filename[:-5]  # Remove .json extension
                    
                    try:
                        config_path = os.path.join(self.config_dir, filename)
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                        
                        config_info = SavedConfigInfo(
                            name=config_data.get("name", config_id),
                            description=config_data.get("description", ""),
                            created_timestamp=config_data.get("created_timestamp", ""),
                            recommended_for=config_data.get("recommended_for", [])
                        )
                        
                        configs.append(config_info)
                        
                    except Exception as e:
                        self.logger.warning(f"Could not read config {filename}: {str(e)}")
                        continue
            
            # Sort by creation time (newest first)
            configs.sort(key=lambda x: x.created_timestamp, reverse=True)
            
            self.logger.debug(f"Found {len(configs)} saved configurations")
            return configs
            
        except Exception as e:
            self.logger.error(f"Failed to list configs: {str(e)}")
            raise ConfigurationError(f"Failed to list configurations: {str(e)}")
    
    def delete_config(self, config_id: str) -> bool:
        """
        Delete a saved configuration
        
        Args:
            config_id: Configuration identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            config_path = os.path.join(self.config_dir, f"{config_id}.json")
            
            if not os.path.exists(config_path):
                raise ConfigurationError(f"Configuration not found: {config_id}")
            
            os.remove(config_path)
            self.logger.info(f"Deleted configuration: {config_id}")
            return True
            
        except ConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete config {config_id}: {str(e)}")
            raise ConfigurationError(f"Failed to delete configuration: {str(e)}")
    
    def update_config(self, config_id: str, request: ConfigSaveRequest) -> str:
        """
        Update an existing configuration
        
        Args:
            config_id: Configuration identifier to update
            request: New configuration data
            
        Returns:
            Configuration ID
        """
        try:
            # Check if config exists
            if not self._config_exists(config_id):
                raise ConfigurationError(f"Configuration not found: {config_id}")
            
            # Load existing config to preserve creation timestamp
            existing_config = self.get_config(config_id)
            
            # Prepare updated config data
            config_data = {
                "name": request.name,
                "description": request.description,
                "created_timestamp": existing_config.get("created_timestamp"),
                "updated_timestamp": datetime.now().isoformat(),
                "recommended_for": request.recommended_for,
                "config": request.config.dict()
            }
            
            # Save updated config
            config_path = os.path.join(self.config_dir, f"{config_id}.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Updated configuration: {config_id}")
            return config_id
            
        except ConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update config {config_id}: {str(e)}")
            raise ConfigurationError(f"Failed to update configuration: {str(e)}")
    
    def _config_exists(self, config_id: str) -> bool:
        """Check if a configuration exists"""
        config_path = os.path.join(self.config_dir, f"{config_id}.json")
        return os.path.exists(config_path)
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize config name for use as filename"""
        import re
        
        # Replace spaces and special chars with underscores
        sanitized = re.sub(r'[^\w\-_]', '_', name.lower())
        
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure not empty
        if not sanitized:
            sanitized = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return sanitized
    
    def get_default_config(self) -> AnalysisConfig:
        """Get default analysis configuration"""
        return AnalysisConfig()
    
    def export_config(self, config_id: str, export_path: str) -> str:
        """
        Export a configuration to a specific file path
        
        Args:
            config_id: Configuration to export
            export_path: Path to export to
            
        Returns:
            Path to exported file
        """
        try:
            config_data = self.get_config(config_id)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Exported configuration {config_id} to {export_path}")
            return export_path
            
        except Exception as e:
            self.logger.error(f"Failed to export config {config_id}: {str(e)}")
            raise ConfigurationError(f"Failed to export configuration: {str(e)}")
    
    def import_config(self, import_path: str, new_name: Optional[str] = None) -> str:
        """
        Import a configuration from a file
        
        Args:
            import_path: Path to import from
            new_name: Optional new name for imported config
            
        Returns:
            Configuration ID of imported config
        """
        try:
            if not os.path.exists(import_path):
                raise ConfigurationError(f"Import file not found: {import_path}")
            
            with open(import_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Create save request from imported data
            config_settings = AnalysisConfig(**config_data.get("config", {}))
            
            request = ConfigSaveRequest(
                name=new_name or config_data.get("name", "Imported Configuration"),
                description=config_data.get("description", "Imported configuration"),
                config=config_settings,
                recommended_for=config_data.get("recommended_for", [])
            )
            
            # Save imported config
            config_id = self.save_config(request)
            
            self.logger.info(f"Imported configuration from {import_path} -> {config_id}")
            return config_id
            
        except ConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to import config from {import_path}: {str(e)}")
            raise ConfigurationError(f"Failed to import configuration: {str(e)}")
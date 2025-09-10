"""
Configuration manager for Devix.

This module provides the ConfigManager class that handles loading configuration
from multiple sources (files, environment variables, defaults) and provides
a unified interface for accessing and modifying Devix settings.
"""

import json
import logging
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .settings import DevixSettings


class ConfigManager:
    """
    Manages configuration loading, saving, and validation for Devix.
    
    Supports loading configuration from:
    - YAML files (.devix.yml, devix.yaml)
    - JSON files (.devix.json)
    - Environment variables (DEVIX_*)
    - Default values from DevixSettings
    """
    
    def __init__(self, project_path: str = "../", config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            project_path: Path to the project being analyzed
            config_file: Optional specific config file path
        """
        self.project_path = Path(project_path).resolve()
        self.config_file = config_file
        self.logger = self._setup_logger()
        self._settings: Optional[DevixSettings] = None
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for the config manager."""
        logger = logging.getLogger("devix.config.ConfigManager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def load_config(self) -> DevixSettings:
        """
        Load configuration from available sources in priority order:
        1. Specified config file
        2. Project-level config files
        3. Environment variables
        4. Default settings
        
        Returns:
            DevixSettings instance with loaded configuration
        """
        try:
            # Start with default settings
            config_data = {}
            
            # Load from file if available
            file_config = self._load_from_file()
            if file_config:
                config_data.update(file_config)
                self.logger.info(f"Loaded configuration from file")
            
            # Override with environment variables
            env_config = self._load_from_environment()
            if env_config:
                self._merge_config(config_data, env_config)
                self.logger.info(f"Applied {len(env_config)} environment overrides")
            
            # Create settings from merged config
            if config_data:
                self._settings = DevixSettings.from_dict(config_data)
            else:
                self._settings = DevixSettings(project_path=str(self.project_path))
            
            self.logger.info(f"Configuration loaded successfully")
            return self._settings
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Fall back to default settings
            self._settings = DevixSettings(project_path=str(self.project_path))
            return self._settings
    
    def save_config(self, settings: Optional[DevixSettings] = None, output_file: Optional[str] = None) -> Path:
        """
        Save current configuration to file.
        
        Args:
            settings: Optional settings to save (uses current if not provided)
            output_file: Optional output file path
            
        Returns:
            Path to saved configuration file
        """
        if settings is None:
            settings = self._settings or DevixSettings(project_path=str(self.project_path))
        
        if output_file is None:
            output_file = str(self.project_path / ".devix.yml")
        
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = settings.to_dict()
            
            # Save as YAML for better readability
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2, sort_keys=True)
            
            self.logger.info(f"Configuration saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def get_settings(self) -> DevixSettings:
        """Get current settings, loading if necessary."""
        if self._settings is None:
            return self.load_config()
        return self._settings
    
    def update_settings(self, **kwargs) -> None:
        """Update specific settings values."""
        if self._settings is None:
            self._settings = self.load_config()
        
        # Update settings attributes
        for key, value in kwargs.items():
            if hasattr(self._settings, key):
                setattr(self._settings, key, value)
                self.logger.debug(f"Updated setting {key} = {value}")
            else:
                self.logger.warning(f"Unknown setting: {key}")
    
    def _load_from_file(self) -> Optional[Dict[str, Any]]:
        """Load configuration from file sources."""
        config_files = self._find_config_files()
        
        for config_file in config_files:
            try:
                if config_file.suffix.lower() in ['.yml', '.yaml']:
                    return self._load_yaml_file(config_file)
                elif config_file.suffix.lower() == '.json':
                    return self._load_json_file(config_file)
            except Exception as e:
                self.logger.warning(f"Failed to load config from {config_file}: {e}")
                continue
        
        return None
    
    def _find_config_files(self) -> List[Path]:
        """Find potential configuration files in order of priority."""
        config_files = []
        
        # Specific config file takes priority
        if self.config_file:
            specific_file = Path(self.config_file)
            if specific_file.exists():
                config_files.append(specific_file)
        
        # Project-level config files
        project_configs = [
            '.devix.yml',
            '.devix.yaml', 
            'devix.yml',
            'devix.yaml',
            '.devix.json',
            'devix.json'
        ]
        
        for config_name in project_configs:
            config_path = self.project_path / config_name
            if config_path.exists():
                config_files.append(config_path)
        
        return config_files
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables."""
        env_config = {}
        
        # Map environment variables to config paths
        env_mappings = {
            'DEVIX_PROJECT_PATH': ['project_path'],
            'DEVIX_LOG_LEVEL': ['system', 'log_level'],
            'DEVIX_LOG_FILE': ['system', 'log_file'],
            'DEVIX_PARALLEL_EXECUTION': ['system', 'parallel_execution'],
            'DEVIX_MAX_WORKERS': ['system', 'max_workers'],
            'DEVIX_CACHE_ENABLED': ['system', 'cache_enabled'],
            'DEVIX_CACHE_DIR': ['system', 'cache_dir'],
            'DEVIX_OUTPUT_FORMATS': ['reporting', 'output_formats'],
            'DEVIX_OUTPUT_DIR': ['reporting', 'output_dir'],
            'DEVIX_ENABLED_ANALYZERS': ['enabled_analyzers'],
            'DEVIX_SECURITY_ENABLED': ['security', 'enabled'],
            'DEVIX_SECURITY_TIMEOUT': ['security', 'timeout'],
            'DEVIX_QUALITY_ENABLED': ['quality', 'enabled'],
            'DEVIX_QUALITY_TIMEOUT': ['quality', 'timeout'],
            'DEVIX_TEST_ENABLED': ['test', 'enabled'],
            'DEVIX_TEST_COVERAGE_THRESHOLD': ['test', 'coverage_threshold'],
            'DEVIX_PERFORMANCE_ENABLED': ['performance', 'enabled'],
            'DEVIX_PERFORMANCE_CPU_THRESHOLD': ['performance', 'cpu_threshold']
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert value to appropriate type
                converted_value = self._convert_env_value(value)
                self._set_nested_value(env_config, config_path, converted_value)
        
        return env_config
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False
        
        # Number conversion
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # List conversion (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # Return as string
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: List[str], value: Any) -> None:
        """Set a nested value in the configuration dictionary."""
        current = config
        
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[path[-1]] = value
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Merge override configuration into base configuration."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def validate_config(self, settings: Optional[DevixSettings] = None) -> List[str]:
        """
        Validate configuration and return list of issues found.
        
        Args:
            settings: Settings to validate (uses current if not provided)
            
        Returns:
            List of validation error messages
        """
        if settings is None:
            settings = self.get_settings()
        
        issues = []
        
        try:
            # Validate project path
            if not Path(settings.project_path).exists():
                issues.append(f"Project path does not exist: {settings.project_path}")
            
            # Validate enabled analyzers
            valid_analyzers = {"project_scanner", "security", "quality", "test", "performance"}
            invalid_analyzers = set(settings.enabled_analyzers) - valid_analyzers
            if invalid_analyzers:
                issues.append(f"Invalid analyzers enabled: {', '.join(invalid_analyzers)}")
            
            # Validate log level
            valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            if settings.system.log_level.upper() not in valid_log_levels:
                issues.append(f"Invalid log level: {settings.system.log_level}")
            
            # Validate thresholds
            if settings.test.coverage_threshold < 0 or settings.test.coverage_threshold > 100:
                issues.append(f"Invalid coverage threshold: {settings.test.coverage_threshold}")
            
            if settings.performance.cpu_threshold < 0 or settings.performance.cpu_threshold > 100:
                issues.append(f"Invalid CPU threshold: {settings.performance.cpu_threshold}")
            
            # Validate output formats
            valid_formats = {"markdown", "text", "json", "html"}
            invalid_formats = set(settings.reporting.output_formats) - valid_formats
            if invalid_formats:
                issues.append(f"Invalid output formats: {', '.join(invalid_formats)}")
            
            # Validate cache directory
            if settings.system.cache_enabled and settings.system.cache_dir:
                cache_dir = Path(settings.system.cache_dir)
                if not cache_dir.parent.exists():
                    issues.append(f"Cache directory parent does not exist: {cache_dir.parent}")
            
        except Exception as e:
            issues.append(f"Validation error: {e}")
        
        return issues
    
    def create_sample_config(self, output_file: Optional[str] = None) -> Path:
        """
        Create a sample configuration file with documentation.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to created sample config file
        """
        if output_file is None:
            output_file = str(self.project_path / "devix.sample.yml")
        
        sample_config = {
            "# Devix Configuration File": None,
            "# This file configures all aspects of Devix analysis": None,
            "": None,
            "project_path": str(self.project_path),
            "": None,
            "# File patterns to ignore during analysis": None,
            "ignore_patterns": [
                "__pycache__",
                "*.pyc",
                ".git",
                "node_modules",
                ".pytest_cache",
                "*.log"
            ],
            "": None,
            "# Analyzers to run": None,
            "enabled_analyzers": [
                "project_scanner",
                "security", 
                "quality",
                "test",
                "performance"
            ],
            "": None,
            "# Security analyzer configuration": None,
            "security": {
                "enabled": True,
                "timeout": 300,
                "skip_tests": True,
                "confidence_level": "medium",
                "severity_level": "medium"
            },
            "": None,
            "# Quality analyzer configuration": None,
            "quality": {
                "enabled": True,
                "timeout": 300,
                "max_line_length": 120,
                "max_complexity": 10,
                "enable_docstring_checks": True
            },
            "": None,
            "# Test analyzer configuration": None,
            "test": {
                "enabled": True,
                "coverage_threshold": 70.0,
                "run_tests": True,
                "test_timeout": 600
            },
            "": None,
            "# Performance analyzer configuration": None,
            "performance": {
                "enabled": True,
                "cpu_threshold": 80.0,
                "memory_threshold": 500.0,
                "monitoring_duration": 30
            },
            "": None,
            "# Reporting configuration": None,
            "reporting": {
                "output_formats": ["markdown", "text"],
                "filename_prefix": "devix_report",
                "include_metadata": True
            },
            "": None,
            "# System configuration": None,
            "system": {
                "log_level": "INFO",
                "parallel_execution": True,
                "max_workers": 4,
                "cache_enabled": True
            }
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write with comments preserved
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Devix Configuration File\n")
            f.write("# This file configures all aspects of Devix analysis\n\n")
            
            yaml.dump(
                {k: v for k, v in sample_config.items() if not k.startswith('#') and k != ''},
                f,
                default_flow_style=False,
                indent=2,
                sort_keys=False
            )
        
        self.logger.info(f"Sample configuration created: {output_path}")
        return output_path

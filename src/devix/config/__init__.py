"""
Configuration management for Devix.

This package provides comprehensive configuration management capabilities
including loading settings from files, environment variables, and providing
defaults for all analyzers and system components.
"""

from .config_manager import ConfigManager
from .settings import DevixSettings

__all__ = [
    "ConfigManager",
    "DevixSettings",
]

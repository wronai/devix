"""
Devix - Automated Development and Code Analysis System

A comprehensive system for automated code analysis, testing, and repair
with enhanced reporting capabilities and modular architecture.
"""

__version__ = "2.1.8"
__author__ = "Tom Sapletta"
__email__ = "devix@info@softreck.dev"

# Core components
from .core.orchestrator import DevixOrchestrator
from .config.config_manager import ConfigManager
from .config.settings import DevixSettings

# Analysis components
from .analysis.project_scanner import ProjectScanner
from .analysis.security_analyzer import SecurityAnalyzer
from .analysis.quality_analyzer import QualityAnalyzer
from .analysis.test_analyzer import TestAnalyzer
from .analysis.performance_analyzer import PerformanceAnalyzer

# Reporting components
from .reporting.enhanced_generator import EnhancedReportGenerator
from .reporting.markdown_formatter import MarkdownFormatter
from .reporting.text_formatter import TextFormatter

# CLI
from .cli.main import main

__all__ = [
    # Core
    "DevixOrchestrator",
    "ConfigManager",
    "DevixSettings",
    # Analysis
    "ProjectScanner",
    "SecurityAnalyzer",
    "QualityAnalyzer", 
    "TestAnalyzer",
    "PerformanceAnalyzer",
    # Reporting
    "EnhancedReportGenerator",
    "MarkdownFormatter",
    "TextFormatter",
    # CLI
    "main",
]

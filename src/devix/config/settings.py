"""
Settings and configuration data classes for Devix.

This module defines the configuration structure and default values
for all Devix components including analyzers, formatters, and system settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class AnalyzerConfig:
    """Configuration for individual analyzers."""
    enabled: bool = True
    timeout: int = 300  # 5 minutes default
    max_issues: int = 100
    severity_threshold: str = "low"  # low, medium, high, critical
    custom_args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityConfig(AnalyzerConfig):
    """Security analyzer specific configuration."""
    bandit_config: Optional[str] = None
    skip_tests: bool = True
    confidence_level: str = "medium"  # low, medium, high
    severity_level: str = "medium"  # low, medium, high
    exclude_dirs: Set[str] = field(default_factory=lambda: {"tests", "test", "__pycache__"})


@dataclass
class QualityConfig(AnalyzerConfig):
    """Quality analyzer specific configuration."""
    pylint_rcfile: Optional[str] = None
    flake8_config: Optional[str] = None
    max_line_length: int = 120
    max_complexity: int = 10
    enable_docstring_checks: bool = True
    enable_type_checks: bool = True


@dataclass
class TestConfig(AnalyzerConfig):
    """Test analyzer specific configuration."""
    test_frameworks: List[str] = field(default_factory=lambda: ["pytest", "unittest", "jest"])
    coverage_threshold: float = 70.0
    run_tests: bool = True
    test_timeout: int = 600  # 10 minutes
    coverage_formats: List[str] = field(default_factory=lambda: ["term", "html"])


@dataclass
class PerformanceConfig(AnalyzerConfig):
    """Performance analyzer specific configuration."""
    cpu_threshold: float = 80.0
    memory_threshold: float = 500.0  # MB
    performance_threshold: float = 1000.0  # ms
    monitoring_duration: int = 30  # seconds
    enable_profiling: bool = False


@dataclass
class ProjectScannerConfig(AnalyzerConfig):
    """Project scanner specific configuration."""
    max_depth: int = 10
    include_hidden: bool = False
    extract_fragments: bool = True
    fragment_size: int = 50  # lines


@dataclass
class ReportingConfig:
    """Reporting system configuration."""
    output_formats: List[str] = field(default_factory=lambda: ["markdown", "text"])
    output_dir: Optional[str] = None
    filename_prefix: str = "devix_report"
    include_metadata: bool = True
    include_file_paths: bool = True
    max_issues_per_category: int = 50


@dataclass
class SystemConfig:
    """System-wide configuration."""
    log_level: str = "INFO"
    log_file: Optional[str] = None
    parallel_execution: bool = True
    max_workers: int = 4
    cache_enabled: bool = True
    cache_dir: Optional[str] = None


@dataclass
class DevixSettings:
    """Main Devix configuration settings."""
    
    # Project settings
    project_path: str = "../"
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".git", ".svn", ".hg",
        "node_modules", ".pytest_cache", ".coverage", "*.log", ".DS_Store",
        "*.egg-info", "dist", "build", ".venv", "venv", ".env"
    ])
    
    # Analyzer configurations
    security: SecurityConfig = field(default_factory=SecurityConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    test: TestConfig = field(default_factory=TestConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    project_scanner: ProjectScannerConfig = field(default_factory=ProjectScannerConfig)
    
    # System configurations
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    
    # Runtime settings
    enabled_analyzers: List[str] = field(default_factory=lambda: [
        "project_scanner", "security", "quality", "test", "performance"
    ])
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Ensure project_path is absolute
        self.project_path = str(Path(self.project_path).resolve())
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.system.log_level.upper() not in valid_log_levels:
            self.system.log_level = "INFO"
        
        # Validate enabled analyzers
        valid_analyzers = {"project_scanner", "security", "quality", "test", "performance"}
        self.enabled_analyzers = [
            analyzer for analyzer in self.enabled_analyzers 
            if analyzer in valid_analyzers
        ]
        
        # Set up cache directory if not specified
        if self.system.cache_enabled and not self.system.cache_dir:
            self.system.cache_dir = str(Path(self.project_path) / ".devix_cache")
    
    def get_analyzer_config(self, analyzer_name: str) -> Optional[AnalyzerConfig]:
        """Get configuration for a specific analyzer."""
        config_map = {
            "security": self.security,
            "quality": self.quality,
            "test": self.test,
            "performance": self.performance,
            "project_scanner": self.project_scanner
        }
        return config_map.get(analyzer_name)
    
    def is_analyzer_enabled(self, analyzer_name: str) -> bool:
        """Check if an analyzer is enabled."""
        if analyzer_name not in self.enabled_analyzers:
            return False
        
        config = self.get_analyzer_config(analyzer_name)
        return config.enabled if config else False
    
    def get_ignore_patterns(self) -> List[str]:
        """Get all ignore patterns including default and custom ones."""
        return self.ignore_patterns.copy()
    
    def add_ignore_pattern(self, pattern: str) -> None:
        """Add a new ignore pattern."""
        if pattern not in self.ignore_patterns:
            self.ignore_patterns.append(pattern)
    
    def remove_ignore_pattern(self, pattern: str) -> bool:
        """Remove an ignore pattern. Returns True if removed, False if not found."""
        try:
            self.ignore_patterns.remove(pattern)
            return True
        except ValueError:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        return {
            "project_path": self.project_path,
            "ignore_patterns": self.ignore_patterns,
            "enabled_analyzers": self.enabled_analyzers,
            "security": {
                "enabled": self.security.enabled,
                "timeout": self.security.timeout,
                "max_issues": self.security.max_issues,
                "severity_threshold": self.security.severity_threshold,
                "bandit_config": self.security.bandit_config,
                "skip_tests": self.security.skip_tests,
                "confidence_level": self.security.confidence_level,
                "severity_level": self.security.severity_level,
                "exclude_dirs": list(self.security.exclude_dirs),
                "custom_args": self.security.custom_args
            },
            "quality": {
                "enabled": self.quality.enabled,
                "timeout": self.quality.timeout,
                "max_issues": self.quality.max_issues,
                "severity_threshold": self.quality.severity_threshold,
                "pylint_rcfile": self.quality.pylint_rcfile,
                "flake8_config": self.quality.flake8_config,
                "max_line_length": self.quality.max_line_length,
                "max_complexity": self.quality.max_complexity,
                "enable_docstring_checks": self.quality.enable_docstring_checks,
                "enable_type_checks": self.quality.enable_type_checks,
                "custom_args": self.quality.custom_args
            },
            "test": {
                "enabled": self.test.enabled,
                "timeout": self.test.timeout,
                "max_issues": self.test.max_issues,
                "severity_threshold": self.test.severity_threshold,
                "test_frameworks": self.test.test_frameworks,
                "coverage_threshold": self.test.coverage_threshold,
                "run_tests": self.test.run_tests,
                "test_timeout": self.test.test_timeout,
                "coverage_formats": self.test.coverage_formats,
                "custom_args": self.test.custom_args
            },
            "performance": {
                "enabled": self.performance.enabled,
                "timeout": self.performance.timeout,
                "max_issues": self.performance.max_issues,
                "severity_threshold": self.performance.severity_threshold,
                "cpu_threshold": self.performance.cpu_threshold,
                "memory_threshold": self.performance.memory_threshold,
                "performance_threshold": self.performance.performance_threshold,
                "monitoring_duration": self.performance.monitoring_duration,
                "enable_profiling": self.performance.enable_profiling,
                "custom_args": self.performance.custom_args
            },
            "project_scanner": {
                "enabled": self.project_scanner.enabled,
                "timeout": self.project_scanner.timeout,
                "max_issues": self.project_scanner.max_issues,
                "severity_threshold": self.project_scanner.severity_threshold,
                "max_depth": self.project_scanner.max_depth,
                "include_hidden": self.project_scanner.include_hidden,
                "extract_fragments": self.project_scanner.extract_fragments,
                "fragment_size": self.project_scanner.fragment_size,
                "custom_args": self.project_scanner.custom_args
            },
            "reporting": {
                "output_formats": self.reporting.output_formats,
                "output_dir": self.reporting.output_dir,
                "filename_prefix": self.reporting.filename_prefix,
                "include_metadata": self.reporting.include_metadata,
                "include_file_paths": self.reporting.include_file_paths,
                "max_issues_per_category": self.reporting.max_issues_per_category
            },
            "system": {
                "log_level": self.system.log_level,
                "log_file": self.system.log_file,
                "parallel_execution": self.system.parallel_execution,
                "max_workers": self.system.max_workers,
                "cache_enabled": self.system.cache_enabled,
                "cache_dir": self.system.cache_dir
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DevixSettings':
        """Create settings from dictionary."""
        # Extract main settings
        settings = cls(
            project_path=data.get("project_path", "../"),
            ignore_patterns=data.get("ignore_patterns", []),
            enabled_analyzers=data.get("enabled_analyzers", [])
        )
        
        # Load analyzer configurations
        if "security" in data:
            sec_data = data["security"]
            settings.security = SecurityConfig(
                enabled=sec_data.get("enabled", True),
                timeout=sec_data.get("timeout", 300),
                max_issues=sec_data.get("max_issues", 100),
                severity_threshold=sec_data.get("severity_threshold", "low"),
                bandit_config=sec_data.get("bandit_config"),
                skip_tests=sec_data.get("skip_tests", True),
                confidence_level=sec_data.get("confidence_level", "medium"),
                severity_level=sec_data.get("severity_level", "medium"),
                exclude_dirs=set(sec_data.get("exclude_dirs", [])),
                custom_args=sec_data.get("custom_args", {})
            )
        
        if "quality" in data:
            qual_data = data["quality"]
            settings.quality = QualityConfig(
                enabled=qual_data.get("enabled", True),
                timeout=qual_data.get("timeout", 300),
                max_issues=qual_data.get("max_issues", 100),
                severity_threshold=qual_data.get("severity_threshold", "low"),
                pylint_rcfile=qual_data.get("pylint_rcfile"),
                flake8_config=qual_data.get("flake8_config"),
                max_line_length=qual_data.get("max_line_length", 120),
                max_complexity=qual_data.get("max_complexity", 10),
                enable_docstring_checks=qual_data.get("enable_docstring_checks", True),
                enable_type_checks=qual_data.get("enable_type_checks", True),
                custom_args=qual_data.get("custom_args", {})
            )
        
        # Load other configurations similarly...
        if "reporting" in data:
            rep_data = data["reporting"]
            settings.reporting = ReportingConfig(
                output_formats=rep_data.get("output_formats", ["markdown", "text"]),
                output_dir=rep_data.get("output_dir"),
                filename_prefix=rep_data.get("filename_prefix", "devix_report"),
                include_metadata=rep_data.get("include_metadata", True),
                include_file_paths=rep_data.get("include_file_paths", True),
                max_issues_per_category=rep_data.get("max_issues_per_category", 50)
            )
        
        if "system" in data:
            sys_data = data["system"]
            settings.system = SystemConfig(
                log_level=sys_data.get("log_level", "INFO"),
                log_file=sys_data.get("log_file"),
                parallel_execution=sys_data.get("parallel_execution", True),
                max_workers=sys_data.get("max_workers", 4),
                cache_enabled=sys_data.get("cache_enabled", True),
                cache_dir=sys_data.get("cache_dir")
            )
        
        return settings

"""
Main orchestrator for Devix analysis workflow.

This module provides the DevixOrchestrator class that coordinates all analyzers,
manages the analysis pipeline, handles configuration, and orchestrates report generation.
It serves as the central coordinator for the entire Devix analysis system.
"""

import asyncio
import concurrent.futures
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from ..analysis.base_analyzer import BaseAnalyzer
from ..analysis.project_scanner import ProjectScanner
from ..analysis.security_analyzer import SecurityAnalyzer
from ..analysis.quality_analyzer import QualityAnalyzer
from ..analysis.test_analyzer import TestAnalyzer
from ..analysis.performance_analyzer import PerformanceAnalyzer
from ..config.config_manager import ConfigManager
from ..config.settings import DevixSettings
from ..reporting.enhanced_generator import EnhancedReportGenerator


class DevixOrchestrator:
    """
    Main orchestrator that coordinates all Devix analysis components.
    
    The orchestrator manages:
    - Configuration loading and validation
    - Analyzer initialization and execution
    - Parallel/sequential execution coordination
    - Report generation and output
    - Error handling and recovery
    - Progress tracking and logging
    """
    
    def __init__(self, 
                 project_path: str = "../",
                 config_file: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the Devix orchestrator.
        
        Args:
            project_path: Path to the project being analyzed
            config_file: Optional config file path
            logger: Optional logger instance
        """
        self.project_path = Path(project_path).resolve()
        self.config_manager = ConfigManager(str(self.project_path), config_file)
        self.settings = self.config_manager.load_config()
        self.logger = logger or self._setup_logger()
        
        # Analysis state
        self.analyzers: Dict[str, BaseAnalyzer] = {}
        self.analysis_results: Dict[str, Any] = {}
        self.execution_stats: Dict[str, Any] = {}
        
        # Report generator
        self.report_generator = EnhancedReportGenerator(
            str(self.project_path), 
            self.logger
        )
        
        # Initialize analyzers
        self._initialize_analyzers()
        
        self.logger.info(f"DevixOrchestrator initialized for project: {self.project_path.name}")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for the orchestrator."""
        logger = logging.getLogger("devix.core.DevixOrchestrator")
        
        if not logger.handlers:
            # Create handler
            handler = logging.StreamHandler()
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(handler)
            
            # Set log level from settings
            log_level = getattr(logging, self.settings.system.log_level.upper(), logging.INFO)
            logger.setLevel(log_level)
            
            # Add file handler if specified
            if self.settings.system.log_file:
                file_handler = logging.FileHandler(self.settings.system.log_file)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        
        return logger
    
    def _initialize_analyzers(self) -> None:
        """Initialize all enabled analyzers."""
        analyzer_classes = {
            'project_scanner': ProjectScanner,
            'security': SecurityAnalyzer,
            'quality': QualityAnalyzer,
            'test': TestAnalyzer,
            'performance': PerformanceAnalyzer
        }
        
        for analyzer_name in self.settings.enabled_analyzers:
            if analyzer_name in analyzer_classes and self.settings.is_analyzer_enabled(analyzer_name):
                try:
                    analyzer_class = analyzer_classes[analyzer_name]
                    analyzer = analyzer_class(str(self.project_path), self.logger)
                    
                    # Configure analyzer with settings
                    self._configure_analyzer(analyzer, analyzer_name)
                    
                    self.analyzers[analyzer_name] = analyzer
                    self.logger.info(f"Initialized {analyzer_name} analyzer")
                    
                except Exception as e:
                    self.logger.error(f"Failed to initialize {analyzer_name} analyzer: {e}")
        
        self.logger.info(f"Initialized {len(self.analyzers)} analyzers")
    
    def _configure_analyzer(self, analyzer: BaseAnalyzer, analyzer_name: str) -> None:
        """Configure an analyzer with settings from configuration."""
        config = self.settings.get_analyzer_config(analyzer_name)
        if not config:
            return
        
        # Set common configuration attributes if they exist on the analyzer
        common_attrs = {
            'timeout': config.timeout,
            'max_issues': config.max_issues,
            'severity_threshold': config.severity_threshold
        }
        
        for attr_name, attr_value in common_attrs.items():
            if hasattr(analyzer, attr_name):
                setattr(analyzer, attr_name, attr_value)
        
        # Set analyzer-specific configuration
        if analyzer_name == 'security' and hasattr(config, 'skip_tests'):
            if hasattr(analyzer, 'skip_tests'):
                analyzer.skip_tests = config.skip_tests
        
        elif analyzer_name == 'quality' and hasattr(config, 'max_line_length'):
            if hasattr(analyzer, 'max_line_length'):
                analyzer.max_line_length = config.max_line_length
        
        elif analyzer_name == 'test' and hasattr(config, 'coverage_threshold'):
            if hasattr(analyzer, 'coverage_threshold'):
                analyzer.coverage_threshold = config.coverage_threshold
        
        elif analyzer_name == 'performance' and hasattr(config, 'cpu_threshold'):
            if hasattr(analyzer, 'cpu_threshold'):
                analyzer.cpu_threshold = config.cpu_threshold
    
    def run_analysis(self, 
                    analyzers: Optional[List[str]] = None,
                    parallel: Optional[bool] = None) -> Dict[str, Any]:
        """
        Run the complete analysis workflow.
        
        Args:
            analyzers: Optional list of specific analyzers to run
            parallel: Optional override for parallel execution
            
        Returns:
            Dictionary containing all analysis results
        """
        start_time = time.time()
        self.logger.info("Starting Devix analysis workflow")
        
        try:
            # Determine which analyzers to run
            if analyzers is None:
                analyzers_to_run = list(self.analyzers.keys())
            else:
                analyzers_to_run = [name for name in analyzers if name in self.analyzers]
            
            # Determine execution mode
            use_parallel = parallel if parallel is not None else self.settings.system.parallel_execution
            
            self.logger.info(f"Running {len(analyzers_to_run)} analyzers: {', '.join(analyzers_to_run)}")
            
            # Execute analyzers
            if use_parallel and len(analyzers_to_run) > 1:
                self.analysis_results = self._run_analyzers_parallel(analyzers_to_run)
            else:
                self.analysis_results = self._run_analyzers_sequential(analyzers_to_run)
            
            # Calculate execution statistics
            execution_time = time.time() - start_time
            self.execution_stats = {
                'total_execution_time': execution_time,
                'analyzers_run': len(analyzers_to_run),
                'analyzers_successful': len([r for r in self.analysis_results.values() if r.get('status') == 'success']),
                'analyzers_failed': len([r for r in self.analysis_results.values() if r.get('status') == 'error']),
                'timestamp': datetime.now().isoformat(),
                'parallel_execution': use_parallel
            }
            
            self.logger.info(f"Analysis completed in {execution_time:.2f} seconds")
            return self.analysis_results
            
        except Exception as e:
            self.logger.error(f"Analysis workflow failed: {e}")
            raise
    
    def _run_analyzers_sequential(self, analyzer_names: List[str]) -> Dict[str, Any]:
        """Run analyzers sequentially."""
        results = {}
        
        for analyzer_name in analyzer_names:
            self.logger.info(f"Running {analyzer_name} analyzer...")
            
            try:
                analyzer = self.analyzers[analyzer_name]
                start_time = time.time()
                
                result = analyzer.analyze()
                execution_time = time.time() - start_time
                
                result['status'] = 'success'
                result['execution_time'] = execution_time
                results[analyzer_name] = result
                
                issues_count = len(result.get('issues', []))
                self.logger.info(f"{analyzer_name} completed: {issues_count} issues found in {execution_time:.2f}s")
                
            except Exception as e:
                self.logger.error(f"{analyzer_name} analyzer failed: {e}")
                results[analyzer_name] = {
                    'status': 'error',
                    'error': str(e),
                    'issues': [],
                    'metrics': {},
                    'recommendations': []
                }
        
        return results
    
    def _run_analyzers_parallel(self, analyzer_names: List[str]) -> Dict[str, Any]:
        """Run analyzers in parallel using ThreadPoolExecutor."""
        results = {}
        max_workers = min(self.settings.system.max_workers, len(analyzer_names))
        
        self.logger.info(f"Running analyzers in parallel with {max_workers} workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all analyzer tasks
            future_to_analyzer = {
                executor.submit(self._run_single_analyzer, name): name
                for name in analyzer_names
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_analyzer):
                analyzer_name = future_to_analyzer[future]
                
                try:
                    result = future.result()
                    results[analyzer_name] = result
                    
                    issues_count = len(result.get('issues', []))
                    execution_time = result.get('execution_time', 0)
                    self.logger.info(f"{analyzer_name} completed: {issues_count} issues found in {execution_time:.2f}s")
                    
                except Exception as e:
                    self.logger.error(f"{analyzer_name} analyzer failed: {e}")
                    results[analyzer_name] = {
                        'status': 'error',
                        'error': str(e),
                        'issues': [],
                        'metrics': {},
                        'recommendations': []
                    }
        
        return results
    
    def _run_single_analyzer(self, analyzer_name: str) -> Dict[str, Any]:
        """Run a single analyzer and return its results."""
        analyzer = self.analyzers[analyzer_name]
        start_time = time.time()
        
        try:
            result = analyzer.analyze()
            execution_time = time.time() - start_time
            
            result['status'] = 'success'
            result['execution_time'] = execution_time
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'status': 'error',
                'error': str(e),
                'execution_time': execution_time,
                'issues': [],
                'metrics': {},
                'recommendations': []
            }
    
    def generate_reports(self, 
                        output_dir: Optional[str] = None,
                        formats: Optional[List[str]] = None) -> Dict[str, Path]:
        """
        Generate analysis reports in specified formats.
        
        Args:
            output_dir: Optional output directory
            formats: Optional list of formats to generate
            
        Returns:
            Dictionary mapping format names to output file paths
        """
        if not self.analysis_results:
            raise ValueError("No analysis results available. Run analysis first.")
        
        # Use settings defaults if not specified
        if output_dir is None:
            output_dir = self.settings.reporting.output_dir or str(self.project_path)
        
        if formats is None:
            formats = self.settings.reporting.output_formats
        
        self.logger.info(f"Generating reports in formats: {', '.join(formats)}")
        
        try:
            # Add execution stats to results for reporting
            enriched_results = self.analysis_results.copy()
            enriched_results['_execution_stats'] = self.execution_stats
            
            # Generate reports
            report_files = self.report_generator.save_reports(
                enriched_results,
                Path(output_dir),
                self.settings.reporting.filename_prefix
            )
            
            self.logger.info(f"Reports generated successfully")
            return report_files
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of the analysis results."""
        if not self.analysis_results:
            return {"status": "no_analysis_run"}
        
        total_issues = 0
        successful_analyzers = 0
        failed_analyzers = 0
        
        analyzer_summaries = {}
        
        for analyzer_name, results in self.analysis_results.items():
            if analyzer_name.startswith('_'):  # Skip metadata
                continue
                
            if results.get('status') == 'success':
                successful_analyzers += 1
                issues_count = len(results.get('issues', []))
                total_issues += issues_count
                
                analyzer_summaries[analyzer_name] = {
                    'status': 'success',
                    'issues_count': issues_count,
                    'execution_time': results.get('execution_time', 0)
                }
            else:
                failed_analyzers += 1
                analyzer_summaries[analyzer_name] = {
                    'status': 'failed',
                    'error': results.get('error', 'Unknown error')
                }
        
        return {
            'total_issues': total_issues,
            'successful_analyzers': successful_analyzers,
            'failed_analyzers': failed_analyzers,
            'total_analyzers': len(self.analyzers),
            'execution_stats': self.execution_stats,
            'analyzer_summaries': analyzer_summaries,
            'project_path': str(self.project_path),
            'timestamp': datetime.now().isoformat()
        }
    
    def save_configuration(self, output_file: Optional[str] = None) -> Path:
        """Save current configuration to file."""
        return self.config_manager.save_config(self.settings, output_file)
    
    def reload_configuration(self, config_file: Optional[str] = None) -> None:
        """Reload configuration and reinitialize analyzers."""
        self.logger.info("Reloading configuration...")
        
        if config_file:
            self.config_manager.config_file = config_file
        
        # Reload settings
        self.settings = self.config_manager.load_config()
        
        # Reinitialize analyzers
        self.analyzers.clear()
        self._initialize_analyzers()
        
        # Update logger level
        log_level = getattr(logging, self.settings.system.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        self.logger.info("Configuration reloaded successfully")
    
    def validate_setup(self) -> List[str]:
        """
        Validate the current setup and return any issues found.
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        try:
            # Validate configuration
            config_issues = self.config_manager.validate_config(self.settings)
            issues.extend(config_issues)
            
            # Validate project path
            if not self.project_path.exists():
                issues.append(f"Project path does not exist: {self.project_path}")
            
            # Validate analyzers
            if not self.analyzers:
                issues.append("No analyzers initialized")
            
            for analyzer_name, analyzer in self.analyzers.items():
                try:
                    # Basic analyzer validation
                    if not hasattr(analyzer, 'analyze'):
                        issues.append(f"Analyzer {analyzer_name} missing analyze method")
                except Exception as e:
                    issues.append(f"Analyzer {analyzer_name} validation failed: {e}")
            
            # Validate report generator
            if not self.report_generator:
                issues.append("Report generator not initialized")
            
        except Exception as e:
            issues.append(f"Setup validation failed: {e}")
        
        return issues
    
    def get_available_analyzers(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available analyzers."""
        analyzer_info = {}
        
        for analyzer_name, analyzer in self.analyzers.items():
            config = self.settings.get_analyzer_config(analyzer_name)
            
            analyzer_info[analyzer_name] = {
                'enabled': config.enabled if config else False,
                'timeout': config.timeout if config else 300,
                'class_name': analyzer.__class__.__name__,
                'status': 'initialized'
            }
        
        return analyzer_info
    
    def run_quick_analysis(self) -> Dict[str, Any]:
        """
        Run a quick analysis with reduced scope for faster feedback.
        
        Returns:
            Dictionary containing quick analysis results
        """
        self.logger.info("Running quick analysis...")
        
        # Configure for quick analysis
        original_settings = {}
        quick_analyzers = ['project_scanner', 'security']  # Run only essential analyzers
        
        try:
            # Temporarily reduce timeouts and limits
            for analyzer_name in quick_analyzers:
                if analyzer_name in self.analyzers:
                    analyzer = self.analyzers[analyzer_name]
                    if hasattr(analyzer, 'timeout'):
                        original_settings[f'{analyzer_name}_timeout'] = analyzer.timeout
                        analyzer.timeout = 60  # 1 minute max
                    if hasattr(analyzer, 'max_issues'):
                        original_settings[f'{analyzer_name}_max_issues'] = analyzer.max_issues
                        analyzer.max_issues = 20  # Limit issues for quick feedback
            
            # Run quick analysis
            results = self.run_analysis(analyzers=quick_analyzers, parallel=False)
            
            return results
            
        finally:
            # Restore original settings
            for analyzer_name in quick_analyzers:
                if analyzer_name in self.analyzers:
                    analyzer = self.analyzers[analyzer_name]
                    if f'{analyzer_name}_timeout' in original_settings:
                        analyzer.timeout = original_settings[f'{analyzer_name}_timeout']
                    if f'{analyzer_name}_max_issues' in original_settings:
                        analyzer.max_issues = original_settings[f'{analyzer_name}_max_issues']

"""
Main CLI interface for Devix.

This module provides a comprehensive command-line interface for running
Devix analysis with various options, configurations, and output formats.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional

from ..core.orchestrator import DevixOrchestrator
from ..config.config_manager import ConfigManager


class DevixCLI:
    """Command-line interface for Devix analysis."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.parser = self._create_parser()
        self.orchestrator: Optional[DevixOrchestrator] = None
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser with subcommands."""
        parser = argparse.ArgumentParser(
            prog='devix',
            description='Devix - Modular Code Analysis Tool',
            epilog='For more information, visit the project documentation.',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Create subparsers for commands
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )
        
        # Analyze command (main command)
        analyze_parser = subparsers.add_parser(
            'analyze',
            help='Analyze a project',
            description='Run comprehensive code analysis on a project'
        )
        analyze_parser.add_argument(
            'project_path',
            nargs='?',
            default='.',
            help='Path to the project to analyze (default: current directory)'
        )
        
        # Configuration options for analyze command
        config_group = analyze_parser.add_argument_group('Configuration')
        config_group.add_argument(
            '-c', '--config',
            dest='config_file',
            help='Path to configuration file (.devix.yml, .devix.json)'
        )
        
        # Analyzer selection for analyze command
        analyzer_group = analyze_parser.add_argument_group('Analyzer Selection')
        analyzer_group.add_argument(
            '-a', '--analyzers',
            nargs='+',
            choices=['project_scanner', 'security', 'quality', 'test', 'performance', 'all'],
            default=['all'],
            help='Analyzers to run (default: all)'
        )
        analyzer_group.add_argument(
            '--exclude',
            nargs='+',
            choices=['project_scanner', 'security', 'quality', 'test', 'performance'],
            help='Analyzers to exclude from analysis'
        )
        analyzer_group.add_argument(
            '--quick',
            action='store_true',
            help='Run quick analysis with reduced scope'
        )
        
        # Configuration management commands
        config_parser = subparsers.add_parser(
            'config',
            help='Configuration management',
            description='Create, validate, or manage Devix configuration'
        )
        config_subparsers = config_parser.add_subparsers(
            dest='config_action',
            help='Configuration actions'
        )
        
        # Create config subcommand
        config_subparsers.add_parser(
            'create',
            help='Create a sample configuration file'
        )
        
        # Validate config subcommand
        validate_parser = config_subparsers.add_parser(
            'validate',
            help='Validate configuration file'
        )
        validate_parser.add_argument(
            'config_file',
            nargs='?',
            help='Configuration file to validate'
        )
        
        # Execution options for analyze command
        execution_group = analyze_parser.add_argument_group('Execution Options')
        execution_group.add_argument(
            '--parallel',
            action='store_true',
            help='Run analyzers in parallel (default: from config)'
        )
        execution_group.add_argument(
            '--sequential',
            action='store_true',
            help='Run analyzers sequentially'
        )
        execution_group.add_argument(
            '--timeout',
            type=int,
            help='Timeout for each analyzer in seconds'
        )
        execution_group.add_argument(
            '--max-workers',
            type=int,
            help='Maximum number of parallel workers'
        )
        
        # Output options for analyze command
        output_group = analyze_parser.add_argument_group('Output Options')
        output_group.add_argument(
            '-o', '--output',
            dest='output_dir',
            help='Output directory for reports'
        )
        output_group.add_argument(
            '-f', '--formats',
            nargs='+',
            choices=['markdown', 'text', 'json'],
            default=['markdown', 'text'],
            help='Output formats for reports (default: markdown text)'
        )
        output_group.add_argument(
            '--prefix',
            dest='filename_prefix',
            default='devix_report',
            help='Prefix for report filenames (default: devix_report)'
        )
        output_group.add_argument(
            '--no-reports',
            action='store_true',
            help='Skip report generation (analysis only)'
        )
        
        # Logging options for analyze command
        logging_group = analyze_parser.add_argument_group('Logging Options')
        logging_group.add_argument(
            '-v', '--verbose',
            action='count',
            default=0,
            help='Increase verbosity (-v for INFO, -vv for DEBUG)'
        )
        logging_group.add_argument(
            '-q', '--quiet',
            action='store_true',
            help='Suppress all output except errors'
        )
        logging_group.add_argument(
            '--log-file',
            help='Log to file instead of console'
        )
        
        # Info command
        info_parser = subparsers.add_parser(
            'info',
            help='Show information about Devix',
            description='Display version, available analyzers, and setup validation'
        )
        info_group = info_parser.add_mutually_exclusive_group()
        info_group.add_argument(
            '--version',
            action='store_true',
            help='Show version information'
        )
        info_group.add_argument(
            '--list-analyzers',
            action='store_true',
            help='List available analyzers'
        )
        info_group.add_argument(
            '--validate-setup',
            action='store_true',
            help='Validate setup and configuration'
        )
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI with the given arguments.
        
        Args:
            args: Optional list of arguments (uses sys.argv if None)
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Parse arguments
            parsed_args = self.parser.parse_args(args)
            
            # Handle different commands
            if not hasattr(parsed_args, 'command') or parsed_args.command is None:
                # No command provided, show help
                self.parser.print_help()
                return 1
                
            # Set up logging for analyze command
            if parsed_args.command == 'analyze':
                self._setup_logging(parsed_args)
                
            # Route to appropriate handler
            if parsed_args.command == 'analyze':
                return self._handle_analyze(parsed_args)
            elif parsed_args.command == 'config':
                return self._handle_config(parsed_args)
            elif parsed_args.command == 'info':
                return self._handle_info(parsed_args)
            else:
                print(f"Unknown command: {parsed_args.command}")
                return 1
            
        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user.", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _setup_logging(self, args: argparse.Namespace) -> None:
        """Set up logging based on CLI arguments."""
        if args.quiet:
            log_level = logging.ERROR
        elif args.verbose >= 2:
            log_level = logging.DEBUG
        elif args.verbose >= 1:
            log_level = logging.INFO
        else:
            log_level = logging.WARNING
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if args.verbose else '%(levelname)s: %(message)s',
            filename=args.log_file if hasattr(args, 'log_file') and args.log_file else None
        )

    def _handle_analyze(self, args: argparse.Namespace) -> int:
        """Handle the analyze command."""
        try:
            # Initialize orchestrator
            self.orchestrator = DevixOrchestrator(
                project_path=args.project_path,
                config_file=getattr(args, 'config_file', None)
            )
            
            # Apply CLI overrides to configuration
            self._apply_cli_overrides(args)
            
            # Run analysis
            return self._run_analysis(args)
            
        except Exception as e:
            print(f"Analysis failed: {e}", file=sys.stderr)
            return 1
    
    def _handle_config(self, args: argparse.Namespace) -> int:
        """Handle configuration commands."""
        try:
            if args.config_action == 'create':
                return self._handle_create_config(args)
            elif args.config_action == 'validate':
                return self._handle_validate_config(args)
            else:
                print("No configuration action specified. Use 'create' or 'validate'.")
                return 1
        except Exception as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            return 1
    
    def _handle_info(self, args: argparse.Namespace) -> int:
        """Handle info commands."""
        try:
            if args.version:
                print("Devix 1.0.0 - Modular Code Analysis Tool")
                return 0
            elif args.list_analyzers:
                return self._handle_list_analyzers(args)
            elif args.validate_setup:
                return self._handle_validate_setup(args)
            else:
                # Default info output
                print("Devix 1.0.0 - Modular Code Analysis Tool")
                print("Use 'devix info --help' for more options.")
                return 0
        except Exception as e:
            print(f"Info error: {e}", file=sys.stderr)
            return 1
    
    def _apply_cli_overrides(self, args: argparse.Namespace) -> None:
        """Apply CLI argument overrides to the orchestrator configuration."""
        if not self.orchestrator:
            return
        
        settings = self.orchestrator.settings
        
        # Override parallel execution
        if args.parallel:
            settings.system.parallel_execution = True
        elif args.sequential:
            settings.system.parallel_execution = False
        
        # Override max workers
        if args.max_workers:
            settings.system.max_workers = args.max_workers
        
        # Override timeout for analyzers
        if args.timeout:
            for analyzer_name in settings.enabled_analyzers:
                config = settings.get_analyzer_config(analyzer_name)
                if config:
                    config.timeout = args.timeout
        
        # Override output settings
        if args.output_dir:
            settings.reporting.output_dir = args.output_dir
        
        if args.formats:
            settings.reporting.output_formats = args.formats
        
        if args.filename_prefix:
            settings.reporting.filename_prefix = args.filename_prefix
    
    def _handle_create_config(self, args: argparse.Namespace) -> int:
        """Handle creating a sample configuration file."""
        try:
            config_manager = ConfigManager(args.project_path, args.config_file)
            output_file = args.config_file or str(Path(args.project_path) / "devix.sample.yml")
            
            config_path = config_manager.create_sample_config(output_file)
            print(f"Sample configuration created: {config_path}")
            return 0
            
        except Exception as e:
            print(f"Failed to create configuration: {e}", file=sys.stderr)
            return 1
    
    def _handle_list_analyzers(self, args: argparse.Namespace) -> int:
        """Handle listing available analyzers."""
        analyzers = {
            'project_scanner': 'Scans project structure and extracts code fragments',
            'security': 'Analyzes code for security vulnerabilities using Bandit and other tools',
            'quality': 'Checks code quality using pylint, flake8, and complexity analysis',
            'test': 'Discovers and runs tests, analyzes coverage',
            'performance': 'Monitors system resources and analyzes performance patterns'
        }
        
        print("Available Analyzers:")
        print("-" * 50)
        for name, description in analyzers.items():
            print(f"{name:15} - {description}")
        
        return 0
    
    def _handle_validate_config(self, args: argparse.Namespace) -> int:
        """Handle configuration validation."""
        try:
            issues = self.orchestrator.config_manager.validate_config()
            
            if not issues:
                print("✅ Configuration is valid!")
                return 0
            else:
                print("❌ Configuration issues found:")
                for issue in issues:
                    print(f"  - {issue}")
                return 1
                
        except Exception as e:
            print(f"Configuration validation failed: {e}", file=sys.stderr)
            return 1
    
    def _handle_validate_setup(self, args: argparse.Namespace) -> int:
        """Handle setup validation."""
        try:
            issues = self.orchestrator.validate_setup()
            
            if not issues:
                print("✅ Setup is valid!")
                
                # Show analyzer information
                analyzers = self.orchestrator.get_available_analyzers()
                print(f"\nAvailable analyzers: {len(analyzers)}")
                for name, info in analyzers.items():
                    status = "✅" if info['enabled'] else "❌"
                    print(f"  {status} {name} ({info['class_name']})")
                
                return 0
            else:
                print("❌ Setup issues found:")
                for issue in issues:
                    print(f"  - {issue}")
                return 1
                
        except Exception as e:
            print(f"Setup validation failed: {e}", file=sys.stderr)
            return 1
    
    def _run_analysis(self, args: argparse.Namespace) -> int:
        """Run the main analysis workflow."""
        try:
            # Determine which analyzers to run
            if 'all' in args.analyzers:
                analyzers_to_run = None  # Run all enabled analyzers
            else:
                analyzers_to_run = args.analyzers
            
            # Apply exclusions
            if args.exclude and analyzers_to_run:
                analyzers_to_run = [a for a in analyzers_to_run if a not in args.exclude]
            
            # Determine parallel execution
            parallel = None
            if args.parallel:
                parallel = True
            elif args.sequential:
                parallel = False
            
            print(f"🔍 Starting Devix analysis of: {Path(args.project_path).resolve().name}")
            start_time = time.time()
            
            # Run analysis
            if args.quick:
                results = self.orchestrator.run_quick_analysis()
            else:
                results = self.orchestrator.run_analysis(analyzers_to_run, parallel)
            
            execution_time = time.time() - start_time
            
            # Display summary
            summary = self.orchestrator.get_analysis_summary()
            self._display_summary(summary, execution_time)
            
            # Generate reports if requested
            if not args.no_reports:
                print("\n📊 Generating reports...")
                report_files = self.orchestrator.generate_reports(
                    args.output_dir,
                    args.formats
                )
                
                print("Reports generated:")
                for format_name, file_path in report_files.items():
                    if isinstance(file_path, Path):
                        print(f"  📄 {format_name}: {file_path.name}")
            
            # Return appropriate exit code
            if summary['failed_analyzers'] > 0:
                return 2  # Analysis had failures
            elif summary['total_issues'] > 0:
                return 1  # Issues found
            else:
                return 0  # Success, no issues
                
        except Exception as e:
            print(f"Analysis failed: {e}", file=sys.stderr)
            return 1
    
    def _display_summary(self, summary: dict, execution_time: float) -> None:
        """Display analysis summary."""
        print(f"\n📋 Analysis Summary")
        print("=" * 50)
        print(f"⏱️  Execution Time: {execution_time:.2f} seconds")
        print(f"🔧 Analyzers Run: {summary['successful_analyzers']}/{summary['total_analyzers']}")
        
        if summary['failed_analyzers'] > 0:
            print(f"❌ Failed Analyzers: {summary['failed_analyzers']}")
        
        print(f"🐛 Total Issues: {summary['total_issues']}")
        
        # Show analyzer breakdown
        if summary.get('analyzer_summaries'):
            print(f"\n📊 Analyzer Results:")
            for analyzer_name, analyzer_summary in summary['analyzer_summaries'].items():
                if analyzer_summary['status'] == 'success':
                    issues_count = analyzer_summary['issues_count']
                    exec_time = analyzer_summary['execution_time']
                    status_icon = "✅" if issues_count == 0 else "⚠️"
                    print(f"  {status_icon} {analyzer_name:15} {issues_count:3d} issues ({exec_time:.1f}s)")
                else:
                    print(f"  ❌ {analyzer_name:15} FAILED - {analyzer_summary.get('error', 'Unknown error')}")
        
        # Overall status
        if summary['total_issues'] == 0 and summary['failed_analyzers'] == 0:
            print(f"\n🎉 Analysis completed successfully! No issues found.")
        elif summary['failed_analyzers'] > 0:
            print(f"\n⚠️  Analysis completed with errors. Check analyzer failures.")
        else:
            print(f"\n⚠️  Analysis completed. {summary['total_issues']} issues found.")


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    cli = DevixCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())

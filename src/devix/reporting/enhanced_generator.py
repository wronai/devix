"""
Enhanced report generator for Devix.

This module provides a comprehensive report generator that orchestrates multiple
formatters to create rich, detailed reports from analysis results. It combines
data from all analyzers and produces both markdown and text outputs with
enhanced project repair analysis capabilities.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .base_formatter import BaseFormatter
from .markdown_formatter import MarkdownFormatter
from .text_formatter import TextFormatter


class EnhancedReportGenerator:
    """Enhanced report generator that creates comprehensive analysis reports."""
    
    def __init__(self, project_path: str = "../", logger: Optional[logging.Logger] = None):
        """
        Initialize the enhanced report generator.
        
        Args:
            project_path: Path to the project being analyzed
            logger: Optional logger instance
        """
        self.project_path = Path(project_path).resolve()
        self.project_name = self.project_path.name
        self.logger = logger or self._setup_logger()
        
        # Initialize formatters
        self.markdown_formatter = MarkdownFormatter(project_path, logger)
        self.text_formatter = TextFormatter(project_path, logger)
        
        # Report generation metadata
        self.generation_time = datetime.now()
        self.report_metadata = {
            'version': '1.0.0',
            'generator': 'Devix Enhanced Report Generator',
            'project_path': str(self.project_path),
            'project_name': self.project_name
        }
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for the report generator."""
        logger = logging.getLogger("devix.reporting.EnhancedReportGenerator")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def generate_reports(self, analysis_results: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate both markdown and text reports from analysis results.
        
        Args:
            analysis_results: Dictionary containing all analysis data from analyzers
            
        Returns:
            Tuple of (text_content, markdown_content)
        """
        try:
            self.logger.info("Generating enhanced reports...")
            
            # Enrich analysis results with additional metadata
            enriched_results = self._enrich_analysis_results(analysis_results)
            
            # Generate reports in both formats
            text_content = self.text_formatter.format_report(enriched_results)
            markdown_content = self.markdown_formatter.format_report(enriched_results)
            
            # Add metadata to both reports
            text_content = self._add_metadata_to_text(text_content)
            markdown_content = self._add_metadata_to_markdown(markdown_content)
            
            self.logger.info(f"Generated reports: TXT ({len(text_content)} chars), MD ({len(markdown_content)} chars)")
            
            return text_content, markdown_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate reports: {e}")
            error_text = f"ERROR: Failed to generate report - {e}"
            error_markdown = f"# Error\n\nFailed to generate report: {e}"
            return error_text, error_markdown
    
    def save_reports(self, 
                    analysis_results: Dict[str, Any], 
                    output_dir: Optional[Path] = None,
                    filename_prefix: str = "devix_report") -> Dict[str, Path]:
        """
        Generate and save both text and markdown reports.
        
        Args:
            analysis_results: Dictionary containing all analysis data
            output_dir: Optional directory to save reports (defaults to project root)
            filename_prefix: Prefix for the report filenames
            
        Returns:
            Dictionary with paths to saved files {'text': path, 'markdown': path}
        """
        try:
            # Generate reports
            text_content, markdown_content = self.generate_reports(analysis_results)
            
            # Determine output directory
            if output_dir is None:
                output_dir = self.project_path
            
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filenames with timestamp
            timestamp = self.generation_time.strftime("%Y%m%d_%H%M%S")
            
            text_file = output_dir / f"{filename_prefix}_{timestamp}.txt"
            markdown_file = output_dir / f"{filename_prefix}_{timestamp}.md"
            
            # Save files
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"Reports saved: {text_file.name}, {markdown_file.name}")
            
            return {
                'text': text_file,
                'markdown': markdown_file,
                'text_size': len(text_content),
                'markdown_size': len(markdown_content)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save reports: {e}")
            raise
    
    def _enrich_analysis_results(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich analysis results with additional metadata and cross-analyzer insights.
        
        Args:
            analysis_results: Raw analysis results from analyzers
            
        Returns:
            Enriched analysis results with additional metadata
        """
        enriched = analysis_results.copy()
        
        try:
            # Add project structure overview
            enriched['project_structure'] = self._analyze_project_structure()
            
            # Add cross-analyzer insights
            enriched['cross_analysis'] = self._perform_cross_analysis(analysis_results)
            
            # Add priority recommendations
            enriched['priority_actions'] = self._generate_priority_actions(analysis_results)
            
            # Add enhanced metadata for each analyzer
            for analyzer_name, results in analysis_results.items():
                if isinstance(results, dict):
                    enriched[analyzer_name] = self._enrich_analyzer_results(analyzer_name, results)
                    
                    # Transform ProjectScanner file statistics to format expected by formatters
                    if analyzer_name == 'project_scanner' and 'file_stats' in results:
                        file_stats = results['file_stats']
                        enriched[analyzer_name]['analyzed_files'] = file_stats.get('analyzed_paths', [])
                        enriched[analyzer_name]['skipped_files'] = file_stats.get('skipped_paths', [])
                        enriched[analyzer_name]['total_files'] = (
                            file_stats.get('analyzed_paths', []) + file_stats.get('skipped_paths', [])
                        )
                        enriched[analyzer_name]['file_types'] = file_stats.get('file_types', {})
            
            # Add generation metadata
            enriched['_metadata'] = self.report_metadata.copy()
            enriched['_metadata']['generation_time'] = self.generation_time.isoformat()
            
        except Exception as e:
            self.logger.error(f"Error enriching analysis results: {e}")
        
        return enriched
    
    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze and summarize project structure using ProjectScanner data."""
        structure = {
            'directories': [],
            'key_files': [],
            'project_type': 'unknown',
            'technologies': [],
            'file_statistics': {
                'total_files': 0,
                'analyzed_files': 0,
                'skipped_files': 0,
                'file_types': {}
            }
        }
        
        try:
            # Try to get data from ProjectScanner first
            from ..analysis.project_scanner import ProjectScanner
            scanner = ProjectScanner(str(self.project_path))
            scanner_results = scanner.analyze()
            
            # Extract file statistics from ProjectScanner
            file_stats = scanner_results.get('file_stats', {})
            if file_stats:
                structure['file_statistics'] = {
                    'total_files': len(file_stats.get('analyzed_paths', [])) + len(file_stats.get('skipped_paths', [])),
                    'analyzed_files': len(file_stats.get('analyzed_paths', [])),
                    'skipped_files': len(file_stats.get('skipped_paths', [])),
                    'file_types': file_stats.get('file_types', {})
                }
            
            # Extract directories from ProjectScanner
            if 'directories' in file_stats:
                structure['directories'] = [
                    dir_path.split('/')[-1] for dir_path in file_stats['directories']
                    if '/' in dir_path  # Only get directory names, not full paths
                ]
                # Remove duplicates and keep unique directory names
                structure['directories'] = list(set(structure['directories']))
            
            # Fallback to basic analysis if ProjectScanner fails
            if structure['file_statistics']['total_files'] == 0:
                # Identify key directories
                key_dirs = ['src', 'lib', 'app', 'backend', 'frontend', 'tests', 'docs']
                for dir_name in key_dirs:
                    dir_path = self.project_path / dir_name
                    if dir_path.exists() and dir_path.is_dir():
                        structure['directories'].append(dir_name)
            
            # Identify key files and project type
            key_files = {
                'package.json': 'Node.js',
                'requirements.txt': 'Python',
                'pyproject.toml': 'Python',
                'Cargo.toml': 'Rust',
                'go.mod': 'Go',
                'pom.xml': 'Java',
                'Gemfile': 'Ruby',
                'composer.json': 'PHP'
            }
            
            for file_name, tech in key_files.items():
                file_path = self.project_path / file_name
                if file_path.exists():
                    structure['key_files'].append(file_name)
                    if tech not in structure['technologies']:
                        structure['technologies'].append(tech)
            
            # Determine primary project type
            if 'package.json' in structure['key_files']:
                structure['project_type'] = 'Node.js/JavaScript'
            elif any(f in structure['key_files'] for f in ['requirements.txt', 'pyproject.toml']):
                structure['project_type'] = 'Python'
            elif 'Cargo.toml' in structure['key_files']:
                structure['project_type'] = 'Rust'
            
        except Exception as e:
            self.logger.debug(f"Error analyzing project structure: {e}")
        
        return structure
    
    def _perform_cross_analysis(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cross-analyzer insights and correlations."""
        cross_analysis = {
            'correlations': [],
            'conflicts': [],
            'recommendations': []
        }
        
        try:
            # Find correlations between security and quality issues
            security_issues = analysis_results.get('security', {}).get('issues', [])
            quality_issues = analysis_results.get('quality', {}).get('issues', [])
            
            if security_issues and quality_issues:
                cross_analysis['correlations'].append(
                    "Both security and quality issues detected - consider comprehensive code review"
                )
            
            # Check for performance vs quality trade-offs
            performance_issues = analysis_results.get('performance', {}).get('issues', [])
            if performance_issues and quality_issues:
                cross_analysis['correlations'].append(
                    "Performance and quality issues may be related - optimize carefully"
                )
            
            # Test coverage vs issue density correlation
            test_results = analysis_results.get('test', {})
            if test_results:
                test_coverage = test_results.get('metrics', {}).get('coverage_percentage', 0)
                total_issues = sum(len(results.get('issues', [])) for results in analysis_results.values() if isinstance(results, dict))
                
                if test_coverage < 50 and total_issues > 10:
                    cross_analysis['correlations'].append(
                        "Low test coverage correlates with high issue count - increase testing"
                    )
            
            # Generate cross-analyzer recommendations
            if len([r for r in analysis_results.values() if isinstance(r, dict) and r.get('issues')]) >= 3:
                cross_analysis['recommendations'].append(
                    "Multiple analyzers found issues - consider systematic refactoring approach"
                )
            
        except Exception as e:
            self.logger.debug(f"Error in cross-analysis: {e}")
        
        return cross_analysis
    
    def _generate_priority_actions(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized action items from all analysis results."""
        actions = []
        
        try:
            # Security actions (highest priority)
            security_issues = analysis_results.get('security', {}).get('issues', [])
            for issue in security_issues[:3]:  # Top 3 security issues
                actions.append({
                    'priority': 'critical',
                    'category': 'security',
                    'action': f"Address security issue: {issue}",
                    'urgency': 'immediate'
                })
            
            # Quality actions (high priority)
            quality_issues = analysis_results.get('quality', {}).get('issues', [])
            for issue in quality_issues[:2]:  # Top 2 quality issues
                actions.append({
                    'priority': 'high',
                    'category': 'quality',
                    'action': f"Fix quality issue: {issue}",
                    'urgency': 'soon'
                })
            
            # Test actions (medium priority)
            test_results = analysis_results.get('test', {})
            if test_results:
                test_coverage = test_results.get('metrics', {}).get('coverage_percentage', 0)
                if test_coverage < 70:
                    actions.append({
                        'priority': 'medium',
                        'category': 'testing',
                        'action': f"Improve test coverage from {test_coverage}% to 80%+",
                        'urgency': 'planned'
                    })
            
            # Performance actions (medium priority)
            performance_issues = analysis_results.get('performance', {}).get('issues', [])
            for issue in performance_issues[:1]:  # Top performance issue
                actions.append({
                    'priority': 'medium',
                    'category': 'performance',
                    'action': f"Optimize performance: {issue}",
                    'urgency': 'planned'
                })
            
        except Exception as e:
            self.logger.debug(f"Error generating priority actions: {e}")
        
        return actions
    
    def _enrich_analyzer_results(self, analyzer_name: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich individual analyzer results with additional context."""
        enriched = results.copy()
        
        try:
            # Add issue categorization
            issues = enriched.get('issues', [])
            if issues:
                enriched['issue_categories'] = self._categorize_issues(analyzer_name, issues)
                enriched['severity_breakdown'] = self._analyze_issue_severity(analyzer_name, issues)
            
            # Add enhanced recommendations based on analyzer type
            existing_recommendations = enriched.get('recommendations', [])
            enhanced_recommendations = self._generate_enhanced_recommendations(
                analyzer_name, results, existing_recommendations
            )
            enriched['recommendations'] = enhanced_recommendations
            
            # Add success metrics where applicable
            enriched['success_indicators'] = self._calculate_success_indicators(analyzer_name, results)
            
        except Exception as e:
            self.logger.debug(f"Error enriching {analyzer_name} results: {e}")
        
        return enriched
    
    def _categorize_issues(self, analyzer_name: str, issues: List[str]) -> Dict[str, List[str]]:
        """Categorize issues by type for better organization."""
        categories = {
            'critical': [],
            'fixable': [],
            'style': [],
            'informational': []
        }
        
        for issue in issues:
            issue_lower = issue.lower()
            
            # Categorize based on keywords and analyzer type
            if any(word in issue_lower for word in ['critical', 'error', 'failed', 'broken']):
                categories['critical'].append(issue)
            elif any(word in issue_lower for word in ['warning', 'deprecated', 'unused']):
                categories['fixable'].append(issue)
            elif any(word in issue_lower for word in ['style', 'format', 'convention']):
                categories['style'].append(issue)
            else:
                categories['informational'].append(issue)
        
        return {k: v for k, v in categories.items() if v}  # Return only non-empty categories
    
    def _analyze_issue_severity(self, analyzer_name: str, issues: List[str]) -> Dict[str, int]:
        """Analyze severity distribution of issues."""
        severity_count = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for issue in issues:
            severity = self._determine_issue_severity(issue, analyzer_name)
            if severity in severity_count:
                severity_count[severity] += 1
        
        return severity_count
    
    def _determine_issue_severity(self, issue: str, analyzer_name: str) -> str:
        """Determine issue severity (reused from base formatter)."""
        issue_lower = issue.lower()
        
        if analyzer_name == 'security':
            if any(word in issue_lower for word in ['critical', 'high', 'severe']):
                return 'critical'
            elif any(word in issue_lower for word in ['medium', 'moderate']):
                return 'medium'
            return 'high'
        elif analyzer_name == 'performance':
            if any(word in issue_lower for word in ['critical', 'severe', 'blocking']):
                return 'high'
            elif any(word in issue_lower for word in ['slow', 'inefficient']):
                return 'medium'
            return 'low'
        elif analyzer_name == 'quality':
            if any(word in issue_lower for word in ['error', 'critical', 'fatal']):
                return 'high'
            elif any(word in issue_lower for word in ['warning', 'style']):
                return 'low'
            return 'medium'
        elif analyzer_name == 'test':
            if any(word in issue_lower for word in ['failed', 'error', 'broken']):
                return 'high'
            elif any(word in issue_lower for word in ['missing', 'coverage']):
                return 'medium'
            return 'low'
        
        return 'medium'
    
    def _generate_enhanced_recommendations(self, 
                                         analyzer_name: str, 
                                         results: Dict[str, Any], 
                                         existing_recommendations: List[str]) -> List[str]:
        """Generate enhanced recommendations based on analysis results."""
        recommendations = existing_recommendations.copy()
        
        try:
            issues_count = len(results.get('issues', []))
            
            # Add specific recommendations based on analyzer and issue count
            if analyzer_name == 'security' and issues_count > 0:
                recommendations.append("Consider implementing automated security scanning in CI/CD pipeline")
                if issues_count > 5:
                    recommendations.append("Conduct thorough security audit with manual code review")
            
            elif analyzer_name == 'quality' and issues_count > 10:
                recommendations.append("Implement code quality gates in development workflow")
                recommendations.append("Consider refactoring modules with highest issue density")
            
            elif analyzer_name == 'test':
                coverage = results.get('metrics', {}).get('coverage_percentage', 0)
                if coverage < 50:
                    recommendations.append("Prioritize writing tests for critical business logic")
                elif coverage < 80:
                    recommendations.append("Add tests for edge cases and error handling")
            
            elif analyzer_name == 'performance' and issues_count > 0:
                recommendations.append("Profile application under realistic load conditions")
                recommendations.append("Consider performance monitoring and alerting setup")
        
        except Exception as e:
            self.logger.debug(f"Error generating enhanced recommendations: {e}")
        
        return recommendations
    
    def _calculate_success_indicators(self, analyzer_name: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate success indicators for each analyzer."""
        indicators = {}
        
        try:
            issues_count = len(results.get('issues', []))
            metrics = results.get('metrics', {})
            
            # Base success score
            if issues_count == 0:
                indicators['score'] = 100
                indicators['status'] = 'excellent'
            elif issues_count <= 3:
                indicators['score'] = 85 - (issues_count * 5)
                indicators['status'] = 'good'
            elif issues_count <= 10:
                indicators['score'] = 70 - ((issues_count - 3) * 3)
                indicators['status'] = 'fair'
            else:
                indicators['score'] = max(30, 50 - (issues_count - 10))
                indicators['status'] = 'needs_improvement'
            
            # Analyzer-specific indicators
            if analyzer_name == 'test':
                coverage = metrics.get('coverage_percentage', 0)
                indicators['coverage_status'] = 'good' if coverage >= 80 else 'needs_improvement'
            
            elif analyzer_name == 'security':
                indicators['risk_level'] = 'low' if issues_count == 0 else 'medium' if issues_count <= 2 else 'high'
            
        except Exception as e:
            self.logger.debug(f"Error calculating success indicators: {e}")
        
        return indicators
    
    def _add_metadata_to_text(self, text_content: str) -> str:
        """Add metadata section to text report."""
        metadata_section = f"""

REPORT METADATA
{'-' * 60}
Generator Version: {self.report_metadata['version']}
Generation Time:   {self.generation_time.strftime('%Y-%m-%d %H:%M:%S')}
Project Path:      {self.report_metadata['project_path']}
Report Format:     Plain Text
"""
        return text_content + metadata_section
    
    def _add_metadata_to_markdown(self, markdown_content: str) -> str:
        """Add metadata section to markdown report."""
        metadata_section = f"""

## 📋 Report Metadata

| Field | Value |
|-------|-------|
| Generator Version | {self.report_metadata['version']} |
| Generation Time | {self.generation_time.strftime('%Y-%m-%d %H:%M:%S')} |
| Project Path | `{self.report_metadata['project_path']}` |
| Report Format | Markdown |
"""
        return markdown_content + metadata_section

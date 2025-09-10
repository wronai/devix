"""
Text formatter for Devix reports.

This module provides a plain text formatter that generates clean, readable reports
suitable for terminals, logs, and simple text outputs. It focuses on clarity
and readability without markup formatting.
"""

from typing import Any, Dict, List, Optional
from .base_formatter import BaseFormatter


class TextFormatter(BaseFormatter):
    """Plain text formatter for generating clean, readable reports."""
    
    def __init__(self, project_path: str = "../", logger: Optional[Any] = None):
        """Initialize the text formatter."""
        super().__init__(project_path, logger)
        self.separator_line = "=" * 80
        self.section_separator = "-" * 60
        self.subsection_separator = "-" * 40
    
    def get_file_extension(self) -> str:
        """Return the text file extension."""
        return '.txt'
    
    def format_report(self, analysis_results: Dict[str, Any]) -> str:
        """
        Format the analysis results into a clean text report.
        
        Args:
            analysis_results: Dictionary containing all analysis data
            
        Returns:
            Formatted text report as string
        """
        try:
            sections = []
            
            # Header
            sections.append(self._format_text_header())
            
            # Executive Summary
            sections.append(self._format_text_summary(analysis_results))
            
            # Health Score and Metrics
            sections.append(self._format_health_metrics(analysis_results))
            
            # Issues by Severity
            sections.append(self._format_text_issues_by_severity(analysis_results))
            
            # Detailed Analysis Results
            sections.append(self._format_text_detailed_analysis(analysis_results))
            
            # File Statistics
            sections.append(self._format_text_file_statistics(analysis_results))
            
            # Recommendations
            sections.append(self._format_text_recommendations(analysis_results))
            
            # Footer
            sections.append(self._format_text_footer())
            
            return '\n\n'.join(filter(None, sections))
            
        except Exception as e:
            self.logger.error(f"Error formatting text report: {e}")
            return f"ERROR GENERATING REPORT\n\nAn error occurred while generating the report: {e}"
    
    def _format_text_header(self) -> str:
        """Format the text header with project information."""
        timestamp = self.generation_time.strftime("%Y-%m-%d %H:%M:%S")
        
        header = f"""{self.separator_line}
                        DEVIX ANALYSIS REPORT
{self.separator_line}

Project Name: {self.project_name}
Generated On: {timestamp}
Analysis Tool: Devix - Modular Code Analysis Platform

{self.separator_line}"""
        
        return header
    
    def _format_text_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Format executive summary in plain text."""
        total_issues = 0
        critical_issues = 0
        analyzers_run = []
        
        # Collect statistics
        for analyzer_name, results in analysis_results.items():
            if isinstance(results, dict) and 'issues' in results:
                issues = results.get('issues', [])
                issues_count = len(issues)
                total_issues += issues_count
                
                # Count critical issues
                for issue in issues:
                    if self._determine_issue_severity(issue, analyzer_name) in ['critical', 'high']:
                        critical_issues += 1
                
                analyzers_run.append({
                    'name': analyzer_name,
                    'issues': issues_count
                })
        
        health_score = self._calculate_project_health_score(analysis_results)
        coverage = self._calculate_coverage_percentage(analysis_results)
        
        summary = f"""EXECUTIVE SUMMARY
{self.section_separator}

Project Health Score: {health_score}/100 {self._get_health_indicator(health_score)}
Analysis Coverage:    {coverage}%

QUICK STATS:
  Total Issues Found:     {total_issues}
  Critical/High Priority: {critical_issues}
  Analyzers Executed:     {len(analyzers_run)}

ANALYZER BREAKDOWN:"""
        
        # Add analyzer breakdown
        if analyzers_run:
            for analyzer in analyzers_run:
                status = "CLEAN" if analyzer['issues'] == 0 else f"{analyzer['issues']} ISSUES"
                summary += f"\n  {analyzer['name'].upper():<12} {status}"
        
        return summary
    
    def _format_health_metrics(self, analysis_results: Dict[str, Any]) -> str:
        """Format health metrics and scores."""
        health_score = self._calculate_project_health_score(analysis_results)
        
        metrics_section = f"""HEALTH DASHBOARD
{self.section_separator}

Overall Project Health: {health_score}/100 {self._create_text_progress_bar(health_score, 100)}

Individual Analyzer Scores:"""
        
        # Individual analyzer scores
        for analyzer_name, results in analysis_results.items():
            if isinstance(results, dict) and 'issues' in results:
                issues_count = len(results.get('issues', []))
                
                # Calculate individual score
                if issues_count == 0:
                    score = 100
                elif issues_count <= 3:
                    score = 90 - (issues_count * 10)
                elif issues_count <= 10:
                    score = 60 - ((issues_count - 3) * 5)
                else:
                    score = max(0, 25 - (issues_count - 10))
                
                progress_bar = self._create_text_progress_bar(score, 100)
                metrics_section += f"\n  {analyzer_name.upper():<12} {score:>3}/100 {progress_bar}"
        
        return metrics_section
    
    def _format_text_issues_by_severity(self, analysis_results: Dict[str, Any]) -> str:
        """Format issues categorized by severity level in text."""
        severity_issues = self._extract_issues_by_severity(analysis_results)
        
        if not any(issues for issues in severity_issues.values()):
            return f"""ISSUES BY SEVERITY
{self.section_separator}

*** NO ISSUES FOUND! ***
Your project analysis completed without any issues. Great job!"""
        
        issues_section = f"""ISSUES BY SEVERITY
{self.section_separator}"""
        
        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        severity_labels = {
            'critical': 'CRITICAL',
            'high': 'HIGH',
            'medium': 'MEDIUM',
            'low': 'LOW',
            'info': 'INFO'
        }
        
        for severity in severity_order:
            issues = severity_issues.get(severity, [])
            if issues:
                label = severity_labels.get(severity, severity.upper())
                issues_section += f"\n\n{label} PRIORITY ({len(issues)} issues):"
                issues_section += f"\n{self.subsection_separator}"
                
                for i, issue in enumerate(issues, 1):
                    # Clean up issue text for better readability
                    clean_issue = issue.replace('[', '').replace(']', ' -')
                    issues_section += f"\n{i:2d}. {clean_issue}"
                    
                    if i >= 20:  # Limit to 20 issues per severity
                        remaining = len(issues) - 20
                        if remaining > 0:
                            issues_section += f"\n    ... and {remaining} more {severity} priority issues"
                        break
        
        return issues_section
    
    def _format_text_detailed_analysis(self, analysis_results: Dict[str, Any]) -> str:
        """Format detailed analysis results for each analyzer in text."""
        detailed_section = f"""DETAILED ANALYSIS RESULTS
{self.section_separator}"""
        
        for analyzer_name, results in analysis_results.items():
            if isinstance(results, dict):
                detailed_section += f"\n\n{analyzer_name.upper()} ANALYSIS:"
                detailed_section += f"\n{self.subsection_separator}"
                
                # Issues
                issues = results.get('issues', [])
                if issues:
                    detailed_section += f"\nIssues Found: {len(issues)}"
                    
                    for i, issue in enumerate(issues[:10], 1):  # Limit to 10 issues
                        clean_issue = issue.replace('[', '').replace(']', ' -')
                        detailed_section += f"\n  {i}. {clean_issue}"
                    
                    if len(issues) > 10:
                        detailed_section += f"\n  ... and {len(issues) - 10} more issues"
                else:
                    detailed_section += "\nIssues Found: 0 (CLEAN)"
                
                # Metrics
                metrics = results.get('metrics', {})
                if metrics:
                    detailed_section += "\n\nMetrics:"
                    for key, value in metrics.items():
                        formatted_key = key.replace('_', ' ').title()
                        if isinstance(value, float):
                            formatted_value = f"{value:.2f}"
                        else:
                            formatted_value = str(value)
                        detailed_section += f"\n  {formatted_key:<25} {formatted_value}"
                
                # Recommendations
                recommendations = results.get('recommendations', [])
                if recommendations:
                    detailed_section += "\n\nRecommendations:"
                    for i, rec in enumerate(recommendations, 1):
                        detailed_section += f"\n  {i}. {rec}"
        
        return detailed_section
    
    def _format_text_file_statistics(self, analysis_results: Dict[str, Any]) -> str:
        """Format file statistics in text format."""
        stats_section = f"""FILE STATISTICS
{self.section_separator}"""
        
        # Collect file statistics
        total_files = set()
        analyzed_files = set()
        skipped_files = set()
        
        for analyzer_name, results in analysis_results.items():
            if isinstance(results, dict):
                if 'analyzed_files' in results:
                    analyzed_files.update(results['analyzed_files'])
                if 'total_files' in results:
                    total_files.update(results['total_files'])
                if 'skipped_files' in results:
                    skipped_files.update(results['skipped_files'])
        
        # File type breakdown
        file_types = {}
        for file_path in analyzed_files:
            try:
                extension = file_path.split('.')[-1].lower() if '.' in file_path else 'no_extension'
                file_types[extension] = file_types.get(extension, 0) + 1
            except:
                continue
        
        stats_section += f"""

File Analysis Summary:
  Total Files in Project:  {len(total_files):>6}
  Files Analyzed:          {len(analyzed_files):>6}
  Files Skipped:           {len(skipped_files):>6}

File Type Breakdown:"""
        
        if file_types:
            # Sort by count (descending) and show top 15
            sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
            for file_type, count in sorted_types[:15]:
                extension = f".{file_type}" if file_type != 'no_extension' else '(no ext)'
                stats_section += f"\n  {extension:<12} {count:>6} files"
        
        # Add project tree visualization if available
        project_scanner_results = analysis_results.get('project_scanner', {})
        tree_visualization = project_scanner_results.get('tree_visualization', '')
        if tree_visualization:
            stats_section += f"\n\nPROJECT STRUCTURE TREE:\n{self.section_separator}\n\n{tree_visualization}"
        
        return stats_section
    
    def _format_text_recommendations(self, analysis_results: Dict[str, Any]) -> str:
        """Format consolidated recommendations from all analyzers."""
        all_recommendations = []
        
        for analyzer_name, results in analysis_results.items():
            if isinstance(results, dict) and 'recommendations' in results:
                recommendations = results.get('recommendations', [])
                for rec in recommendations:
                    all_recommendations.append(f"{analyzer_name.upper()}: {rec}")
        
        if not all_recommendations:
            return f"""RECOMMENDATIONS & NEXT STEPS
{self.section_separator}

*** EXCELLENT WORK! ***
No specific recommendations at this time. Your project is in great shape!"""
        
        recommendations_section = f"""RECOMMENDATIONS & NEXT STEPS
{self.section_separator}"""
        
        # Prioritize recommendations
        high_priority = [rec for rec in all_recommendations if any(word in rec.lower() for word in ['critical', 'security', 'fix', 'urgent'])]
        medium_priority = [rec for rec in all_recommendations if rec not in high_priority and any(word in rec.lower() for word in ['improve', 'consider', 'update'])]
        low_priority = [rec for rec in all_recommendations if rec not in high_priority and rec not in medium_priority]
        
        if high_priority:
            recommendations_section += f"\n\nHIGH PRIORITY ACTIONS:"
            recommendations_section += f"\n{self.subsection_separator}"
            for i, rec in enumerate(high_priority, 1):
                recommendations_section += f"\n{i:2d}. {rec}"
        
        if medium_priority:
            recommendations_section += f"\n\nMEDIUM PRIORITY IMPROVEMENTS:"
            recommendations_section += f"\n{self.subsection_separator}"
            for i, rec in enumerate(medium_priority, 1):
                recommendations_section += f"\n{i:2d}. {rec}"
        
        if low_priority:
            recommendations_section += f"\n\nLOW PRIORITY SUGGESTIONS:"
            recommendations_section += f"\n{self.subsection_separator}"
            for i, rec in enumerate(low_priority, 1):
                recommendations_section += f"\n{i:2d}. {rec}"
        
        return recommendations_section
    
    def _format_text_footer(self) -> str:
        """Format the text footer."""
        return f"""{self.separator_line}

Report generated by DEVIX - Modular Code Analysis Platform
For more information, visit the project documentation

NOTE: This report provides automated analysis. Manual code review
      is always recommended for critical applications.

{self.separator_line}"""
    
    def _create_text_progress_bar(self, value: float, max_value: float, length: int = 20) -> str:
        """Create a text-based progress bar."""
        percentage = min(100, max(0, (value / max_value) * 100))
        filled_length = int(length * percentage / 100)
        
        # Create bar with different characters based on percentage
        if percentage >= 80:
            fill_char = '█'
        elif percentage >= 50:
            fill_char = '▓'
        else:
            fill_char = '░'
        
        empty_char = '·'
        
        bar = fill_char * filled_length + empty_char * (length - filled_length)
        return f"[{bar}] {percentage:5.1f}%"
    
    def _get_health_indicator(self, score: float) -> str:
        """Get text indicator for health score."""
        if score >= 90:
            return "(EXCELLENT)"
        elif score >= 70:
            return "(GOOD)"
        elif score >= 50:
            return "(FAIR)"
        elif score >= 30:
            return "(NEEDS WORK)"
        else:
            return "(CRITICAL)"
    
    def _calculate_coverage_percentage(self, analysis_results: Dict[str, Any]) -> int:
        """Calculate analysis coverage percentage."""
        try:
            total_files = set()
            analyzed_files = set()
            
            for results in analysis_results.values():
                if isinstance(results, dict):
                    if 'total_files' in results:
                        total_files.update(results['total_files'])
                    if 'analyzed_files' in results:
                        analyzed_files.update(results['analyzed_files'])
            
            if len(total_files) > 0:
                return int((len(analyzed_files) / len(total_files)) * 100)
            return 0
            
        except Exception:
            return 0

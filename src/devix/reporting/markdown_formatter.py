"""
Markdown formatter for Devix reports.

This module provides a specialized formatter that generates rich markdown reports
with tables, collapsible sections, progress bars, and enhanced visual formatting
for better readability and presentation.
"""

import re
from typing import Any, Dict, List, Optional
from .base_formatter import BaseFormatter


class MarkdownFormatter(BaseFormatter):
    """Markdown formatter for generating rich, structured reports."""
    
    def __init__(self, project_path: str = "../", logger: Optional[Any] = None):
        """Initialize the markdown formatter."""
        super().__init__(project_path, logger)
        self.emoji_map = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'info': 'ℹ️',
            'critical': '🚨',
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢',
            'security': '🔒',
            'performance': '⚡',
            'quality': '🎯',
            'test': '🧪',
            'files': '📁',
            'code': '💻',
            'metrics': '📊',
            'recommendation': '💡'
        }
    
    def get_file_extension(self) -> str:
        """Return the markdown file extension."""
        return '.md'
    
    def format_report(self, analysis_results: Dict[str, Any]) -> str:
        """
        Format the analysis results into a comprehensive markdown report.
        
        Args:
            analysis_results: Dictionary containing all analysis data
            
        Returns:
            Formatted markdown report as string
        """
        try:
            sections = []
            
            # Header
            sections.append(self._format_markdown_header())
            
            # Executive Summary
            sections.append(self._format_executive_summary(analysis_results))
            
            # Health Score and Key Metrics
            sections.append(self._format_health_dashboard(analysis_results))
            
            # Issues by Severity
            sections.append(self._format_issues_by_severity(analysis_results))
            
            # Detailed Analysis Results
            sections.append(self._format_detailed_analysis(analysis_results))
            
            # File Statistics
            sections.append(self._format_file_statistics_markdown(analysis_results))
            
            # Recommendations
            sections.append(self._format_recommendations(analysis_results))
            
            # Footer
            sections.append(self._format_markdown_footer())
            
            return '\n\n'.join(filter(None, sections))
            
        except Exception as e:
            self.logger.error(f"Error formatting markdown report: {e}")
            return f"# Error Generating Report\n\nAn error occurred while generating the report: {e}"
    
    def _format_markdown_header(self) -> str:
        """Format the markdown header with project information."""
        timestamp = self.generation_time.strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""# {self.emoji_map['code']} Devix Analysis Report

**Project:** `{self.project_name}`  
**Generated:** {timestamp}  
**Analysis Tool:** Devix - Modular Code Analysis Platform

---"""
    
    def _format_executive_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Format an executive summary with key findings."""
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
        health_emoji = self._get_health_emoji(health_score)
        
        summary = f"""## {self.emoji_map['metrics']} Executive Summary

{health_emoji} **Project Health Score:** {health_score}/100

| Metric | Value |
|--------|-------|
| Total Issues Found | {total_issues} |
| Critical/High Priority | {critical_issues} |
| Analyzers Executed | {len(analyzers_run)} |
| Analysis Coverage | {self._calculate_coverage_percentage(analysis_results)}% |

### {self.emoji_map['info']} Quick Overview"""
        
        # Add analyzer breakdown
        if analyzers_run:
            for analyzer in analyzers_run:
                emoji = self.emoji_map.get(analyzer['name'], self.emoji_map['info'])
                status_emoji = self.emoji_map['success'] if analyzer['issues'] == 0 else self.emoji_map['warning']
                summary += f"\n- {emoji} **{analyzer['name'].title()}:** {analyzer['issues']} issues {status_emoji}"
        
        return summary
    
    def _format_health_dashboard(self, analysis_results: Dict[str, Any]) -> str:
        """Format a visual health dashboard with progress bars."""
        health_score = self._calculate_project_health_score(analysis_results)
        
        dashboard = f"""## {self.emoji_map['metrics']} Health Dashboard

### Overall Project Health
{self._create_progress_bar(health_score, 100, '🟢', '🟡', '🔴')} **{health_score}/100**

### Analysis Breakdown"""
        
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
                
                emoji = self.emoji_map.get(analyzer_name, self.emoji_map['info'])
                progress_bar = self._create_progress_bar(score, 100, '🟢', '🟡', '🔴')
                
                dashboard += f"\n**{emoji} {analyzer_name.title()}:** {progress_bar} {score}/100"
        
        return dashboard
    
    def _format_issues_by_severity(self, analysis_results: Dict[str, Any]) -> str:
        """Format issues categorized by severity level."""
        severity_issues = self._extract_issues_by_severity(analysis_results)
        
        if not any(issues for issues in severity_issues.values()):
            return f"## {self.emoji_map['success']} Issues by Severity\n\n{self.emoji_map['success']} **No issues found!** Your project looks great!"
        
        issues_section = f"## {self.emoji_map['warning']} Issues by Severity"
        
        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        severity_emojis = {
            'critical': self.emoji_map['critical'],
            'high': self.emoji_map['high'],
            'medium': self.emoji_map['medium'],
            'low': self.emoji_map['low'],
            'info': self.emoji_map['info']
        }
        
        for severity in severity_order:
            issues = severity_issues.get(severity, [])
            if issues:
                emoji = severity_emojis.get(severity, self.emoji_map['info'])
                issues_section += f"\n\n### {emoji} {severity.title()} Priority ({len(issues)} issues)\n"
                
                if len(issues) <= 10:
                    # Show all issues for small lists
                    for issue in issues:
                        issues_section += f"- {issue}\n"
                else:
                    # Show first 10 and create collapsible section for the rest
                    for issue in issues[:10]:
                        issues_section += f"- {issue}\n"
                    
                    issues_section += f"\n<details>\n<summary>Show {len(issues) - 10} more {severity} priority issues...</summary>\n\n"
                    for issue in issues[10:]:
                        issues_section += f"- {issue}\n"
                    issues_section += "\n</details>"
        
        return issues_section
    
    def _format_detailed_analysis(self, analysis_results: Dict[str, Any]) -> str:
        """Format detailed analysis results for each analyzer."""
        detailed_section = f"## {self.emoji_map['code']} Detailed Analysis Results"
        
        for analyzer_name, results in analysis_results.items():
            if isinstance(results, dict):
                emoji = self.emoji_map.get(analyzer_name, self.emoji_map['info'])
                detailed_section += f"\n\n### {emoji} {analyzer_name.title()} Analysis"
                
                # Issues
                issues = results.get('issues', [])
                if issues:
                    detailed_section += f"\n\n**Issues Found:** {len(issues)}"
                    
                    if len(issues) <= 5:
                        detailed_section += "\n"
                        for issue in issues:
                            detailed_section += f"- {issue}\n"
                    else:
                        detailed_section += "\n"
                        for issue in issues[:5]:
                            detailed_section += f"- {issue}\n"
                        
                        detailed_section += f"\n<details>\n<summary>Show {len(issues) - 5} more issues...</summary>\n\n"
                        for issue in issues[5:]:
                            detailed_section += f"- {issue}\n"
                        detailed_section += "\n</details>"
                else:
                    detailed_section += f"\n\n{self.emoji_map['success']} **No issues found!**"
                
                # Metrics
                metrics = results.get('metrics', {})
                if metrics:
                    detailed_section += "\n\n**Metrics:**\n"
                    detailed_section += "| Metric | Value |\n|--------|-------|\n"
                    
                    for key, value in metrics.items():
                        formatted_key = key.replace('_', ' ').title()
                        if isinstance(value, float):
                            formatted_value = f"{value:.2f}"
                        else:
                            formatted_value = str(value)
                        detailed_section += f"| {formatted_key} | {formatted_value} |\n"
                
                # Recommendations
                recommendations = results.get('recommendations', [])
                if recommendations:
                    detailed_section += f"\n\n**{self.emoji_map['recommendation']} Recommendations:**\n"
                    for rec in recommendations:
                        detailed_section += f"- {rec}\n"
        
        return detailed_section
    
    def _format_file_statistics_markdown(self, analysis_results: Dict[str, Any]) -> str:
        """Format file statistics in markdown format."""
        stats_section = f"## {self.emoji_map['files']} File Statistics"
        
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

| Statistic | Count |
|-----------|-------|
| Total Files in Project | {len(total_files)} |
| Files Analyzed | {len(analyzed_files)} |
| Files Skipped | {len(skipped_files)} |

### File Type Breakdown"""
        
        if file_types:
            stats_section += "\n\n| File Type | Count |\n|-----------|-------|\n"
            
            # Sort by count (descending)
            sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
            for file_type, count in sorted_types[:10]:  # Top 10 file types
                stats_section += f"| .{file_type} | {count} |\n"
        
        # Add project tree visualization if available
        project_scanner_results = analysis_results.get('project_scanner', {})
        tree_visualization = project_scanner_results.get('tree_visualization', '')
        if tree_visualization:
            stats_section += f"\n\n### Project Structure Tree\n\n```\n{tree_visualization}\n```"
        
        return stats_section
    
    def _format_recommendations(self, analysis_results: Dict[str, Any]) -> str:
        """Format consolidated recommendations from all analyzers."""
        all_recommendations = []
        
        for analyzer_name, results in analysis_results.items():
            if isinstance(results, dict) and 'recommendations' in results:
                recommendations = results.get('recommendations', [])
                for rec in recommendations:
                    emoji = self.emoji_map.get(analyzer_name, self.emoji_map['recommendation'])
                    all_recommendations.append(f"{emoji} **{analyzer_name.title()}:** {rec}")
        
        if not all_recommendations:
            return f"## {self.emoji_map['success']} Recommendations\n\n{self.emoji_map['success']} Great job! No specific recommendations at this time."
        
        recommendations_section = f"## {self.emoji_map['recommendation']} Recommendations & Next Steps"
        
        # Prioritize recommendations
        high_priority = [rec for rec in all_recommendations if any(word in rec.lower() for word in ['critical', 'security', 'fix', 'urgent'])]
        medium_priority = [rec for rec in all_recommendations if rec not in high_priority and any(word in rec.lower() for word in ['improve', 'consider', 'update'])]
        low_priority = [rec for rec in all_recommendations if rec not in high_priority and rec not in medium_priority]
        
        if high_priority:
            recommendations_section += f"\n\n### {self.emoji_map['critical']} High Priority\n"
            for rec in high_priority:
                recommendations_section += f"- {rec}\n"
        
        if medium_priority:
            recommendations_section += f"\n\n### {self.emoji_map['medium']} Medium Priority\n"
            for rec in medium_priority:
                recommendations_section += f"- {rec}\n"
        
        if low_priority:
            recommendations_section += f"\n\n### {self.emoji_map['low']} Low Priority\n"
            for rec in low_priority:
                recommendations_section += f"- {rec}\n"
        
        return recommendations_section
    
    def _format_markdown_footer(self) -> str:
        """Format the markdown footer."""
        return f"""---

*Report generated by **Devix** - Modular Code Analysis Platform*  
*For more information, visit the project documentation*

{self.emoji_map['info']} **Note:** This report provides automated analysis. Manual code review is always recommended for critical applications."""
    
    def _create_progress_bar(self, value: float, max_value: float, good_emoji: str = '🟢', medium_emoji: str = '🟡', bad_emoji: str = '🔴', length: int = 20) -> str:
        """Create a visual progress bar using emojis."""
        percentage = min(100, max(0, (value / max_value) * 100))
        filled_length = int(length * percentage / 100)
        
        # Choose emoji based on percentage
        if percentage >= 80:
            emoji = good_emoji
        elif percentage >= 50:
            emoji = medium_emoji
        else:
            emoji = bad_emoji
        
        # Create bar
        bar = emoji * filled_length + '⚪' * (length - filled_length)
        return f"`{bar}` {percentage:.0f}%"
    
    def _get_health_emoji(self, score: float) -> str:
        """Get appropriate emoji for health score."""
        if score >= 90:
            return '🟢'
        elif score >= 70:
            return '🟡'
        elif score >= 40:
            return '🟠'
        else:
            return '🔴'
    
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

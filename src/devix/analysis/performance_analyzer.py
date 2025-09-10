#!/usr/bin/env python3
"""
Performance Analyzer for Devix - Application performance monitoring and analysis

This module provides comprehensive performance analysis including:
- System resource monitoring (CPU, memory, disk)
- Code performance profiling
- Application response time analysis
- Resource usage optimization recommendations
"""

import json
import logging
import os
import psutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_analyzer import BaseAnalyzer


class PerformanceAnalyzer(BaseAnalyzer):
    """Performance analyzer for monitoring application performance and resource usage"""
    
    def __init__(self, project_path: str = "../", logger: Optional[logging.Logger] = None):
        super().__init__(project_path, logger)
        self.performance_threshold = 100  # ms
        self.memory_threshold = 512  # MB
        self.cpu_threshold = 80  # %
        self.monitoring_duration = 30  # seconds
    
    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive performance analysis"""
        self.logger.info("Starting performance analysis")
        
        results = {
            "system_resources": self._check_system_resources(),
            "code_performance": self._analyze_code_performance(),
            "optimization_suggestions": self._generate_optimization_suggestions(),
            "summary": self._generate_performance_summary()
        }
        
        self.logger.info("Performance analysis completed")
        return results
        
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check current system resource usage"""
        results = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "issues": [],
            "available": True
        }
        
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            results["cpu_usage"] = cpu_percent
            
            if cpu_percent > self.cpu_threshold:
                results["issues"].append({
                    "type": "high_cpu_usage",
                    "value": cpu_percent,
                    "threshold": self.cpu_threshold,
                    "severity": "medium"
                })
                
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            results["memory_usage"] = memory_mb
            
            if memory_mb > self.memory_threshold:
                results["issues"].append({
                    "type": "high_memory_usage",
                    "value": memory_mb,
                    "threshold": self.memory_threshold,
                    "severity": "medium"
                })
                
            # Get disk usage for project directory
            disk_usage = psutil.disk_usage(self.project_path)
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            results["disk_usage"] = disk_percent
            
            if disk_percent > 90:
                results["issues"].append({
                    "type": "high_disk_usage",
                    "value": disk_percent,
                    "threshold": 90,
                    "severity": "high"
                })
                
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
            results["available"] = False
            
        return results
        
    def _analyze_code_performance(self) -> Dict[str, Any]:
        """Analyze code performance characteristics"""
        results = {
            "large_files": [],
            "complex_imports": [],
            "performance_patterns": [],
            "recommendations": []
        }
        
        # Check for large files that might impact performance
        large_files = self._find_large_files()
        results["large_files"] = large_files
        
        # Check for complex import patterns
        complex_imports = self._check_import_complexity()
        results["complex_imports"] = complex_imports
        
        # Check for common performance anti-patterns
        performance_patterns = self._check_performance_patterns()
        results["performance_patterns"] = performance_patterns
        
        return results
        
    def _find_large_files(self) -> List[Dict[str, Any]]:
        """Find files that are unusually large"""
        large_files = []
        size_threshold = 1024 * 1024  # 1MB
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if not self._should_ignore_file(file_path):
                    try:
                        size = file_path.stat().st_size
                        if size > size_threshold:
                            large_files.append({
                                "file": file_path.name,
                                "size_mb": round(size / 1024 / 1024, 2),
                                "extension": file_path.suffix
                            })
                    except Exception as e:
                        self.logger.debug(f"Error checking file size {file_path}: {e}")
                        
        return sorted(large_files, key=lambda x: x["size_mb"], reverse=True)[:10]
        
    def _check_import_complexity(self) -> List[Dict[str, Any]]:
        """Check for complex import patterns that might slow startup"""
        complex_imports = []
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if (file_path.suffix == '.py' and 
                    not self._should_ignore_file(file_path)):
                    
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        lines = content.split('\n')
                        
                        import_count = 0
                        heavy_imports = []
                        
                        for line in lines[:50]:  # Check first 50 lines
                            line = line.strip()
                            if line.startswith('import ') or line.startswith('from '):
                                import_count += 1
                                
                                # Check for potentially heavy imports
                                heavy_modules = ['pandas', 'numpy', 'torch', 'tensorflow', 'matplotlib']
                                if any(module in line for module in heavy_modules):
                                    heavy_imports.append(line)
                                    
                        if import_count > 20 or heavy_imports:
                            complex_imports.append({
                                "file": file_path.name,
                                "import_count": import_count,
                                "heavy_imports": heavy_imports[:3]  # Limit to 3
                            })
                            
                    except Exception as e:
                        self.logger.debug(f"Error analyzing imports in {file_path}: {e}")
                        
                if len(complex_imports) >= 5:  # Limit results
                    break
                    
        return complex_imports
        
    def _check_performance_patterns(self) -> List[Dict[str, Any]]:
        """Check for common performance anti-patterns"""
        patterns = []
        
        # Performance anti-patterns to look for
        anti_patterns = [
            (r'for\s+\w+\s+in\s+range\(len\(', 'Use enumerate() instead of range(len())'),
            (r'\.append\(\)\s*$', 'Consider list comprehension for better performance'),
            (r'global\s+\w+', 'Global variables can impact performance'),
            (r'exec\(|eval\(', 'exec() and eval() are slow and insecure'),
        ]
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if (file_path.suffix == '.py' and 
                    not self._should_ignore_file(file_path)):
                    
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        
                        for pattern, suggestion in anti_patterns:
                            import re
                            matches = re.findall(pattern, content)
                            if matches:
                                patterns.append({
                                    "file": file_path.name,
                                    "pattern": pattern,
                                    "suggestion": suggestion,
                                    "occurrences": len(matches)
                                })
                                
                    except Exception as e:
                        self.logger.debug(f"Error checking patterns in {file_path}: {e}")
                        
                if len(patterns) >= 10:  # Limit results
                    break
                    
        return patterns
        
    def _generate_optimization_suggestions(self) -> List[str]:
        """Generate performance optimization suggestions"""
        suggestions = []
        
        # Check if profiling tools are available
        if not self._tool_available("py-spy"):
            suggestions.append("Install py-spy for Python performance profiling")
            
        if not self._tool_available("memory_profiler"):
            suggestions.append("Install memory_profiler for memory usage analysis")
            
        # General performance suggestions
        suggestions.extend([
            "Use list comprehensions instead of loops where possible",
            "Cache expensive function calls with @lru_cache decorator",
            "Use generators for large datasets to save memory",
            "Profile critical code paths to identify bottlenecks",
            "Consider using numpy for numerical computations",
            "Minimize global variable usage",
            "Use efficient data structures (sets for membership tests, deque for queues)",
            "Lazy load heavy modules when needed"
        ])
        
        return suggestions
        
    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate performance analysis summary"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                "current_cpu": cpu_usage,
                "current_memory_mb": round(memory.used / 1024 / 1024, 2),
                "memory_percent": memory.percent,
                "cpu_threshold": self.cpu_threshold,
                "memory_threshold": self.memory_threshold,
                "monitoring_available": True,
                "profiling_tools": [
                    tool for tool in ["py-spy", "memory_profiler", "cProfile"]
                    if self._tool_available(tool)
                ]
            }
        except Exception as e:
            self.logger.error(f"Error generating performance summary: {e}")
            return {
                "monitoring_available": False,
                "error": str(e)
            }
            
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get high-level performance summary"""
        try:
            return {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage_mb": round(psutil.virtual_memory().used / 1024 / 1024, 2),
                "profiling_tools_available": len([
                    tool for tool in ["py-spy", "memory_profiler", "cProfile"]
                    if self._tool_available(tool)
                ]),
                "optimization_suggestions_count": 8,  # Base suggestions
            }
        except Exception:
            return {
                "cpu_usage": 0,
                "memory_usage_mb": 0,
                "profiling_tools_available": 0,
                "optimization_suggestions_count": 8,
            }

    def _tool_available(self, tool_name: str) -> bool:
        """Check if a performance analysis tool is available"""
        import shutil
        return shutil.which(tool_name) is not None

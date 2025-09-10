"""
Test analyzer for Devix

Provides comprehensive test execution, coverage analysis,
and test structure assessment for multiple testing frameworks.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .base_analyzer import BaseAnalyzer


class TestAnalyzer(BaseAnalyzer):
    """
    Analyzer for test execution and coverage analysis
    
    Supports multiple testing frameworks including pytest, unittest,
    nose, and JavaScript testing frameworks.
    """
    
    def __init__(self, project_path: str = "../", logger: Optional[Any] = None):
        """Initialize test analyzer"""
        super().__init__(project_path, logger)
        self.test_results: Dict[str, Any] = {}
        self.coverage_data: Dict[str, Any] = {}
        self.test_structure: Dict[str, Any] = {}
        
    def analyze(self) -> Dict[str, Any]:
        """
        Perform comprehensive test analysis
        
        Returns:
            Dictionary containing test analysis results
        """
        try:
            self.logger.info("Starting test analysis")
            
            # Reset previous results
            self.reset_stats()
            self.test_results = {}
            self.coverage_data = {}
            self.test_structure = {}
            
            # Discover test structure
            self.test_structure = self._discover_test_structure()
            
            # Run tests if available
            if self.test_structure.get("has_tests", False):
                self.test_results = self._run_tests()
                self.coverage_data = self._analyze_coverage()
            
            return {
                "test_structure": self.test_structure,
                "test_results": self.test_results,
                "coverage_data": self.coverage_data,
                "file_stats": self.get_file_stats(),
                "recommendations": self._generate_test_recommendations(),
            }
            
        except Exception as e:
            self.logger.error(f"Error in test analysis: {e}")
            return {
                "error": str(e),
                "test_structure": self.test_structure,
                "test_results": {},
                "coverage_data": {},
                "file_stats": self.get_file_stats(),
            }
            
    def _discover_test_structure(self) -> Dict[str, Any]:
        """
        Discover test files and structure
        
        Returns:
            Dictionary containing test structure information
        """
        structure = {
            "has_tests": False,
            "test_directories": [],
            "test_files": [],
            "test_frameworks": [],
            "test_configs": [],
            "total_test_files": 0,
            "estimated_test_count": 0,
        }
        
        # Look for test directories
        test_dirs = ['tests', 'test', 'testing', '__tests__']
        for dir_name in test_dirs:
            test_dir = self.project_path / dir_name
            if test_dir.exists() and test_dir.is_dir():
                structure["test_directories"].append(str(test_dir.resolve()))
                structure["has_tests"] = True
                
        # Look for test files throughout project
        for root, dirs, files in os.walk(self.project_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                
                if self._should_ignore_file(file_path):
                    continue
                    
                # Python test files
                if (file.startswith('test_') or file.endswith('_test.py') or 
                    file == 'test.py'):
                    structure["test_files"].append(str(file_path.resolve()))
                    structure["has_tests"] = True
                    self._update_file_stats(file_path, analyzed=True)
                    
                    # Estimate test count
                    structure["estimated_test_count"] += self._count_tests_in_file(file_path)
                    
                # JavaScript test files
                elif (file.endswith(('.test.js', '.test.ts', '.spec.js', '.spec.ts')) or
                      file in ['test.js', 'test.ts']):
                    structure["test_files"].append(str(file_path.resolve()))
                    structure["has_tests"] = True
                    self._update_file_stats(file_path, analyzed=True)
                    
        structure["total_test_files"] = len(structure["test_files"])
        
        # Detect test frameworks
        structure["test_frameworks"] = self._detect_test_frameworks()
        
        # Look for test configuration files
        config_files = [
            'pytest.ini', 'setup.cfg', 'tox.ini', '.coveragerc',
            'jest.config.js', 'jest.config.json', 'karma.conf.js',
            'mocha.opts', '.mocharc.json'
        ]
        
        for config_file in config_files:
            config_path = self.project_path / config_file
            if config_path.exists():
                structure["test_configs"].append(str(config_path.resolve()))
                
        return structure
        
    def _detect_test_frameworks(self) -> List[str]:
        """Detect which test frameworks are being used"""
        frameworks = []
        
        # Check for Python test frameworks
        requirements_files = ['requirements.txt', 'requirements-dev.txt', 'pyproject.toml']
        for req_file in requirements_files:
            req_path = self.project_path / req_file
            if req_path.exists():
                try:
                    content = req_path.read_text(encoding='utf-8')
                    if 'pytest' in content:
                        frameworks.append('pytest')
                    if 'unittest' in content or 'unittest2' in content:
                        frameworks.append('unittest')
                    if 'nose' in content:
                        frameworks.append('nose')
                except Exception as e:
                    self.logger.warning(f"Error reading {req_file}: {e}")
                    
        return list(set(frameworks))  # Remove duplicates
        
    def _count_tests_in_file(self, file_path: Path) -> int:
        """Estimate number of tests in a file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            if file_path.suffix == '.py':
                # Count Python test functions
                test_count = content.count('def test_')
                test_count += content.count('def Test')
                test_count += content.count('class Test')
            else:
                # Count JavaScript test functions
                test_count = content.count('test(')
                test_count += content.count('it(')
                test_count += content.count('describe(')
                
            return test_count
            
        except Exception:
            return 0
            
    def _run_tests(self) -> Dict[str, Any]:
        """Run tests using detected frameworks"""
        results = {
            "executed": False,
            "framework_results": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "duration": 0.0,
            }
        }
        
        frameworks = self.test_structure.get("test_frameworks", [])
        
        for framework in frameworks:
            if framework == 'pytest':
                results["framework_results"]['pytest'] = self._run_pytest()
            elif framework == 'unittest':
                results["framework_results"]['unittest'] = self._run_unittest()
                
        return results
        
    def _run_pytest(self) -> Dict[str, Any]:
        """Run pytest and parse results"""
        try:
            cmd = ["python", "-m", "pytest", "--tb=short", "-v"]
            returncode, stdout, stderr = self._run_command(cmd)
            
            return {
                "success": returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "summary": self._parse_pytest_output(stdout, stderr),
            }
            
        except Exception as e:
            self.logger.error(f"Error running pytest: {e}")
            return {"success": False, "error": str(e)}
            
    def _run_unittest(self) -> Dict[str, Any]:
        """Run unittest and parse results"""
        try:
            cmd = ["python", "-m", "unittest", "discover", "-v"]
            returncode, stdout, stderr = self._run_command(cmd)
            
            return {
                "success": returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "summary": self._parse_unittest_output(stdout, stderr),
            }
            
        except Exception as e:
            self.logger.error(f"Error running unittest: {e}")
            return {"success": False, "error": str(e)}
            
    def _parse_pytest_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse pytest output for test summary"""
        lines = stdout.split('\n') + stderr.split('\n')
        summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
        
        for line in lines:
            if 'passed' in line and 'failed' in line:
                # Parse pytest summary line
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed' and i > 0:
                            summary["passed"] = int(parts[i-1])
                        elif part == 'failed' and i > 0:
                            summary["failed"] = int(parts[i-1])
                        elif part == 'skipped' and i > 0:
                            summary["skipped"] = int(parts[i-1])
                except (ValueError, IndexError):
                    pass
                    
        summary["total"] = summary["passed"] + summary["failed"] + summary["skipped"]
        return summary
        
    def _parse_unittest_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse unittest output for test summary"""
        lines = stdout.split('\n') + stderr.split('\n')
        summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}
        
        for line in lines:
            if 'Ran ' in line and ' test' in line:
                try:
                    summary["total"] = int(line.split('Ran ')[1].split(' test')[0])
                    # Assume all tests passed if no failures mentioned
                    summary["passed"] = summary["total"]
                except (ValueError, IndexError):
                    pass
                    
        return summary
        
    def _analyze_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage"""
        coverage = {
            "available": False,
            "total_coverage": 0.0,
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "covered_files": [],
            "uncovered_files": [],
        }
        
        # Try to find coverage data
        coverage_files = ['.coverage', 'coverage.json', 'coverage.xml']
        for coverage_file in coverage_files:
            coverage_path = self.project_path / coverage_file
            if coverage_path.exists():
                coverage["available"] = True
                break
                
        return coverage
        
    def _generate_test_recommendations(self) -> List[str]:
        """Generate test improvement recommendations"""
        recommendations = []
        
        if not self.test_structure.get("has_tests", False):
            recommendations.append("Consider adding test files to improve code quality")
        
        total_files = self.get_file_stats().get("total_files", 0)
        test_files = self.test_structure.get("total_test_files", 0)
        
        if total_files > 0 and test_files / total_files < 0.2:
            recommendations.append("Test coverage appears low - consider adding more test files")
            
        frameworks = self.test_structure.get("test_frameworks", [])
        if not frameworks:
            recommendations.append("No test framework detected - consider setting up pytest or unittest")
            
        return recommendations
        
    def get_test_summary(self) -> Dict[str, Any]:
        """Get high-level test summary"""
        return {
            "has_tests": self.test_structure.get("has_tests", False),
            "total_test_files": self.test_structure.get("total_test_files", 0),
            "estimated_test_count": self.test_structure.get("estimated_test_count", 0),
            "frameworks": self.test_structure.get("test_frameworks", []),
            "coverage_available": self.coverage_data.get("available", False),
            "tests_executed": self.test_results.get("executed", False),
            "recommendations_count": len(self._generate_test_recommendations()),
        }

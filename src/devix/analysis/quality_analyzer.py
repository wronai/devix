"""
Code quality analyzer for Devix

Provides comprehensive code quality analysis including static analysis,
complexity metrics, code smells detection, and style checking.
"""

import os
import json
import subprocess
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .base_analyzer import BaseAnalyzer


class QualityAnalyzer(BaseAnalyzer):
    """
    Analyzer for code quality assessment
    
    Performs static analysis using tools like pylint, flake8, radon,
    and detects code smells, complexity issues, and style violations.
    """
    
    def __init__(self, project_path: str = "../", logger: Optional[Any] = None):
        """Initialize quality analyzer"""
        super().__init__(project_path, logger)
        self.quality_results: Dict[str, Any] = {}
        self.complexity_threshold = 10
        self.quality_threshold = 7.0
    
    def get_analyzer_name(self) -> str:
        return "Code Quality Analyzer"
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform comprehensive code quality analysis
        
        Returns:
            Dictionary containing quality analysis results
        """
        try:
            self.logger.info("Starting code quality analysis")
            
            # Reset previous results
            self.reset_stats()
            self.quality_results = {}
            
            # Run static analysis
            static_results = self._run_static_analysis()
            
            # Check code complexity
            complexity_results = self._check_complexity()
            
            # Detect code smells
            smell_results = self._detect_code_smells()
            
            # Check documentation
            doc_results = self._check_documentation()
            
            # Check code style
            style_results = self._check_style()
            
            # Aggregate results
            self.quality_results = {
                "static_analysis": static_results,
                "complexity": complexity_results,
                "code_smells": smell_results,
                "documentation": doc_results,
                "style": style_results,
            }
            
            return {
                "quality_results": self.quality_results,
                "file_stats": self.get_file_stats(),
                "recommendations": self._generate_quality_recommendations(),
                "tools_available": self._get_available_tools(),
            }
            
        except Exception as e:
            self.logger.error(f"Error in quality analysis: {e}")
            return {
                "error": str(e),
                "quality_results": self.quality_results,
                "file_stats": self.get_file_stats(),
            }
            
    def _run_static_analysis(self) -> Dict[str, Any]:
        """Run static analysis tools like pylint and flake8"""
        results = {
            "pylint": {"available": False, "issues": [], "score": None},
            "flake8": {"available": False, "issues": []},
            "mypy": {"available": False, "issues": []},
        }
        
        # Get Python files to analyze
        python_files = []
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if (file_path.suffix == '.py' and 
                    not self._should_ignore_file(file_path)):
                    python_files.append(str(file_path))
                    self._update_file_stats(file_path, analyzed=True)
        
        # Run pylint if available
        if self._tool_available("pylint") and python_files:
            results["pylint"] = self._run_pylint(python_files[:5])
            
        # Run flake8 if available
        if self._tool_available("flake8") and python_files:
            results["flake8"] = self._run_flake8(python_files[:5])
            
        return results
        
    def _tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available"""
        try:
            result = subprocess.run([tool_name, "--version"], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
            
    def _run_pylint(self, python_files: List[str]) -> Dict[str, Any]:
        """Run pylint analysis"""
        result = {
            "available": True,
            "issues": [],
            "score": None
        }
        
        try:
            cmd = ["pylint", "--output-format=json", "--score=y"] + python_files
            proc_result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Parse JSON output
            if proc_result.stdout:
                try:
                    pylint_data = json.loads(proc_result.stdout)
                    for item in pylint_data:
                        if item.get('type') in ['error', 'warning']:
                            file_name = Path(item['path']).name
                            message = item['message']
                            line = item.get('line', 0)
                            result["issues"].append({
                                "file": file_name,
                                "line": line,
                                "message": message,
                                "type": item['type']
                            })
                except json.JSONDecodeError:
                    pass
                    
            # Extract score from stderr
            import re
            score_match = re.search(r'Your code has been rated at ([\d.]+)/10', proc_result.stderr)
            if score_match:
                result["score"] = float(score_match.group(1))
                
        except Exception as e:
            self.logger.warning(f"Pylint analysis failed: {e}")
            result["available"] = False
            
        return result
        
    def _run_flake8(self, python_files: List[str]) -> Dict[str, Any]:
        """Run flake8 analysis"""
        result = {
            "available": True,
            "issues": []
        }
        
        try:
            cmd = ["flake8", "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s"] + python_files
            proc_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if proc_result.stdout:
                for line in proc_result.stdout.strip().split('\n'):
                    if ':' in line and line.strip():
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            file_path, line_no, col, message = parts
                            result["issues"].append({
                                "file": Path(file_path).name,
                                "line": int(line_no) if line_no.isdigit() else 0,
                                "column": int(col) if col.isdigit() else 0,
                                "message": message.strip()
                            })
                            
        except Exception as e:
            self.logger.warning(f"Flake8 analysis failed: {e}")
            result["available"] = False
            
        return result
        
    def _check_complexity(self) -> Dict[str, Any]:
        """Check code complexity using radon or manual analysis"""
        results = {
            "radon_available": False,
            "complex_functions": [],
            "average_complexity": 0.0,
        }
        
        # Get Python files
        python_files = []
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if (file_path.suffix == '.py' and 
                    not self._should_ignore_file(file_path)):
                    python_files.append(file_path)
                    
        if not python_files:
            return results
            
        # Try radon first
        if self._tool_available("radon"):
            results.update(self._run_radon_analysis(python_files[:5]))
        else:
            # Manual complexity check
            results.update(self._manual_complexity_check(python_files[:5]))
            
        return results
        
    def _run_radon_analysis(self, python_files: List[Path]) -> Dict[str, Any]:
        """Run radon complexity analysis"""
        results = {
            "radon_available": True,
            "complex_functions": [],
            "average_complexity": 0.0,
        }
        
        try:
            cmd = ["radon", "cc", "--json"] + [str(f) for f in python_files]
            proc_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if proc_result.stdout:
                try:
                    radon_data = json.loads(proc_result.stdout)
                    complexities = []
                    
                    for file_path, functions in radon_data.items():
                        for func in functions:
                            complexity = func.get('complexity', 0)
                            complexities.append(complexity)
                            
                            if complexity > self.complexity_threshold:
                                results["complex_functions"].append({
                                    "file": Path(file_path).name,
                                    "function": func.get('name', 'unknown'),
                                    "line": func.get('lineno', 0),
                                    "complexity": complexity
                                })
                                
                    if complexities:
                        results["average_complexity"] = sum(complexities) / len(complexities)
                        
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Radon analysis failed: {e}")
            results["radon_available"] = False
            
        return results
        
    def _manual_complexity_check(self, python_files: List[Path]) -> Dict[str, Any]:
        """Manual complexity check using AST analysis"""
        results = {
            "radon_available": False,
            "complex_functions": [],
            "average_complexity": 0.0,
        }
        
        try:
            complexities = []
            
            for file_path in python_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            # Simple complexity estimation based on control flow
                            complexity = 1  # Base complexity
                            
                            for child in ast.walk(node):
                                if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                                    complexity += 1
                                elif isinstance(child, ast.ExceptHandler):
                                    complexity += 1
                                    
                            complexities.append(complexity)
                            
                            if complexity > self.complexity_threshold:
                                results["complex_functions"].append({
                                    "file": file_path.name,
                                    "function": node.name,
                                    "line": node.lineno,
                                    "complexity": complexity
                                })
                                
                except Exception as e:
                    self.logger.debug(f"Error analyzing {file_path}: {e}")
                    
            if complexities:
                results["average_complexity"] = sum(complexities) / len(complexities)
                
        except Exception as e:
            self.logger.error(f"Manual complexity analysis failed: {e}")
            
        return results
        
    def _detect_code_smells(self) -> Dict[str, Any]:
        """Detect common code smells"""
        results = {
            "long_functions": [],
            "large_classes": [],
            "long_lines": [],
            "duplicate_code": [],
        }
        
        # Get Python files
        python_files = []
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if (file_path.suffix == '.py' and 
                    not self._should_ignore_file(file_path)):
                    python_files.append(file_path)
                    
        for file_path in python_files[:5]:  # Limit to 5 files
            try:
                file_smells = self._analyze_file_smells(file_path)
                for category, smells in file_smells.items():
                    results[category].extend(smells)
            except Exception as e:
                self.logger.debug(f"Error analyzing smells in {file_path}: {e}")
                
        return results
        
    def _analyze_file_smells(self, file_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze code smells in a single file"""
        smells = {
            "long_functions": [],
            "large_classes": [],
            "long_lines": [],
            "duplicate_code": [],
        }
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Check for long lines
            for i, line in enumerate(lines, 1):
                if len(line) > 100:
                    smells["long_lines"].append({
                        "file": file_path.name,
                        "line": i,
                        "length": len(line)
                    })
                    
            # Parse AST for function and class analysis
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_lines = (node.end_lineno - node.lineno 
                                    if hasattr(node, 'end_lineno') else 0)
                        if func_lines > 50:
                            smells["long_functions"].append({
                                "file": file_path.name,
                                "function": node.name,
                                "line": node.lineno,
                                "lines": func_lines
                            })
                            
                    elif isinstance(node, ast.ClassDef):
                        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                        if len(methods) > 15:
                            smells["large_classes"].append({
                                "file": file_path.name,
                                "class": node.name,
                                "line": node.lineno,
                                "methods": len(methods)
                            })
                            
            except SyntaxError:
                pass  # Skip files with syntax errors
                
        except Exception as e:
            self.logger.debug(f"Error analyzing file smells in {file_path}: {e}")
            
        return smells
        
    def _check_documentation(self) -> Dict[str, Any]:
        """Check code documentation quality"""
        results = {
            "missing_docstrings": [],
            "docstring_coverage": 0.0,
            "total_items": 0,
            "documented_items": 0,
        }
        
        # Get Python files
        python_files = []
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if (file_path.suffix == '.py' and 
                    not self._should_ignore_file(file_path)):
                    python_files.append(file_path)
                    
        for file_path in python_files[:5]:  # Limit to 5 files
            try:
                doc_info = self._check_file_documentation(file_path)
                results["missing_docstrings"].extend(doc_info["missing"])
                results["total_items"] += doc_info["total"]
                results["documented_items"] += doc_info["documented"]
            except Exception as e:
                self.logger.debug(f"Error checking docs in {file_path}: {e}")
                
        if results["total_items"] > 0:
            results["docstring_coverage"] = (results["documented_items"] / 
                                           results["total_items"]) * 100
                                           
        return results
        
    def _check_file_documentation(self, file_path: Path) -> Dict[str, Any]:
        """Check documentation in a single file"""
        doc_info = {
            "missing": [],
            "total": 0,
            "documented": 0
        }
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            # Check module docstring
            doc_info["total"] += 1
            if ast.get_docstring(tree):
                doc_info["documented"] += 1
            else:
                doc_info["missing"].append({
                    "file": file_path.name,
                    "item": "module",
                    "line": 1
                })
                
            # Check functions and classes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    doc_info["total"] += 1
                    if ast.get_docstring(node):
                        doc_info["documented"] += 1
                    else:
                        item_type = "function" if isinstance(node, ast.FunctionDef) else "class"
                        doc_info["missing"].append({
                            "file": file_path.name,
                            "item": f"{item_type} {node.name}",
                            "line": node.lineno
                        })
                        
        except Exception as e:
            self.logger.debug(f"Error checking documentation in {file_path}: {e}")
            
        return doc_info
        
    def _check_style(self) -> Dict[str, Any]:
        """Check code style using black and isort"""
        results = {
            "black": {"available": False, "issues": []},
            "isort": {"available": False, "issues": []},
        }
        
        # Get Python files
        python_files = []
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if (file_path.suffix == '.py' and 
                    not self._should_ignore_file(file_path)):
                    python_files.append(str(file_path))
                    
        if not python_files:
            return results
            
        # Check black formatting
        if self._tool_available("black"):
            results["black"] = self._check_black_formatting(python_files[:5])
            
        # Check import sorting
        if self._tool_available("isort"):
            results["isort"] = self._check_import_sorting(python_files[:5])
            
        return results
        
    def _check_black_formatting(self, python_files: List[str]) -> Dict[str, Any]:
        """Check black code formatting"""
        result = {
            "available": True,
            "issues": []
        }
        
        try:
            cmd = ["black", "--check", "--diff"] + python_files
            proc_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if proc_result.returncode != 0:
                for line in proc_result.stderr.split('\n'):
                    if 'would reformat' in line:
                        file_path = line.split()[-1] if line.split() else "unknown"
                        result["issues"].append({
                            "file": Path(file_path).name,
                            "type": "formatting",
                            "message": "Code formatting needed"
                        })
                        
        except Exception as e:
            self.logger.warning(f"Black formatting check failed: {e}")
            result["available"] = False
            
        return result
        
    def _check_import_sorting(self, python_files: List[str]) -> Dict[str, Any]:
        """Check import sorting with isort"""
        result = {
            "available": True,
            "issues": []
        }
        
        try:
            cmd = ["isort", "--check-only", "--diff"] + python_files
            proc_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if proc_result.returncode != 0:
                result["issues"].append({
                    "type": "import_sorting",
                    "message": "Import sorting needed"
                })
                
        except Exception as e:
            self.logger.warning(f"Import sorting check failed: {e}")
            result["available"] = False
            
        return result
        
    def _get_available_tools(self) -> List[str]:
        """Get list of available quality analysis tools"""
        tools = []
        for tool in ["pylint", "flake8", "black", "isort", "mypy", "radon", "bandit"]:
            if self._tool_available(tool):
                tools.append(tool)
        return tools
        
    def _generate_quality_recommendations(self) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        available_tools = self._get_available_tools()
        
        if not available_tools:
            recommendations.append("Consider installing quality analysis tools like pylint, flake8, black")
            
        if "pylint" not in available_tools:
            recommendations.append("Install pylint for comprehensive static analysis")
            
        if "black" not in available_tools:
            recommendations.append("Install black for automatic code formatting")
            
        # Check if we have quality results
        if hasattr(self, 'quality_results') and self.quality_results:
            static_results = self.quality_results.get("static_analysis", {})
            
            # Check pylint score
            pylint_score = static_results.get("pylint", {}).get("score")
            if pylint_score is not None and pylint_score < self.quality_threshold:
                recommendations.append(f"Improve code quality - pylint score {pylint_score:.1f} below threshold {self.quality_threshold}")
                
            # Check complexity
            complexity_results = self.quality_results.get("complexity", {})
            complex_functions = complexity_results.get("complex_functions", [])
            if complex_functions:
                recommendations.append(f"Refactor {len(complex_functions)} complex functions to reduce complexity")
                
            # Check documentation
            doc_results = self.quality_results.get("documentation", {})
            coverage = doc_results.get("docstring_coverage", 0)
            if coverage < 80:
                recommendations.append(f"Improve documentation coverage - currently {coverage:.1f}%")
                
        return recommendations
        
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get high-level quality summary"""
        return {
            "tools_available": len(self._get_available_tools()),
            "quality_score": self.quality_results.get("static_analysis", {}).get("pylint", {}).get("score"),
            "complex_functions": len(self.quality_results.get("complexity", {}).get("complex_functions", [])),
            "documentation_coverage": self.quality_results.get("documentation", {}).get("docstring_coverage", 0),
            "recommendations_count": len(self._generate_quality_recommendations()),
        }

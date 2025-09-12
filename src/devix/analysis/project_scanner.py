"""
Project structure scanner for Devix

Provides project structure analysis, directory tree generation,
code fragment extraction, and project organization assessment.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import ast
import subprocess

from .base_analyzer import BaseAnalyzer


class ProjectScanner(BaseAnalyzer):
    """
    Analyzer for project structure and organization
    
    Scans project directories, generates visual trees,
    extracts code fragments, and identifies structural issues.
    """
    
    def __init__(self, project_path: str = "../", logger: Optional[Any] = None):
        """Initialize project scanner"""
        super().__init__(project_path, logger)
        self.project_tree: Dict[str, Any] = {}
        self.code_fragments: List[Dict[str, Any]] = []
        self.structure_issues: List[Dict[str, Any]] = []
        
    def analyze(self) -> Dict[str, Any]:
        """
        Perform comprehensive project structure analysis
        
        Returns:
            Dictionary containing project structure analysis results
        """
        try:
            self.logger.info("Starting project structure analysis")
            
            # Reset previous results
            self.reset_stats()
            self.project_tree = {}
            self.code_fragments = []
            self.structure_issues = []
            
            # Scan project structure
            self.project_tree = self._scan_directory_tree()
            
            # Extract important code fragments
            self.code_fragments = self._extract_code_fragments()
            
            # Check for structural issues
            self.structure_issues = self._check_structure_issues()
            
            return {
                "project_tree": self.project_tree,
                "code_fragments": self.code_fragments,
                "structure_issues": self.structure_issues,
                "file_stats": self.get_file_stats(),
                "tree_visualization": self._generate_tree_visualization(),
            }
            
        except Exception as e:
            self.logger.error(f"Error in project structure analysis: {e}")
            return {
                "error": str(e),
                "project_tree": {},
                "code_fragments": [],
                "structure_issues": [],
                "file_stats": self.get_file_stats(),
            }
            
    def _scan_directory_tree(self) -> Dict[str, Any]:
        """
        Scan project directory and build tree structure
        First builds complete structure, then creates filtered version
        
        Returns:
            Dictionary with full and filtered project trees
        """
        def scan_directory_full(path: Path, level: int = 0) -> Dict[str, Any]:
            """Scan directory without filtering - get complete structure"""
            if level > 10:  # Prevent infinite recursion
                return {"error": "Max depth reached"}
                
            items = {}
            
            try:
                for item in sorted(path.iterdir()):
                    if item.is_dir():
                        items[item.name] = {
                            "type": "directory",
                            "path": str(item.resolve()),
                            "items": scan_directory_full(item, level + 1),
                            "ignored": self._should_ignore_file(item)
                        }
                    else:
                        items[item.name] = {
                            "type": "file",
                            "path": str(item.resolve()),
                            "size": item.stat().st_size if item.exists() else 0,
                            "extension": item.suffix.lower(),
                            "ignored": self._should_ignore_file(item)
                        }
                        
            except PermissionError:
                return {"error": "Permission denied"}
            except Exception as e:
                return {"error": f"Error scanning directory: {e}"}
                
            return items
        
        def scan_directory_filtered(path: Path, level: int = 0) -> Dict[str, Any]:
            """Scan directory with filtering - only non-ignored items"""
            if level > 10:  # Prevent infinite recursion
                return {"error": "Max depth reached"}
                
            items = {}
            
            try:
                for item in sorted(path.iterdir()):
                    if self._should_ignore_file(item):
                        self._update_file_stats(item, analyzed=False)
                        continue
                        
                    if item.is_dir():
                        items[item.name] = {
                            "type": "directory",
                            "path": str(item.resolve()),
                            "items": scan_directory_filtered(item, level + 1)
                        }
                    else:
                        self._update_file_stats(item, analyzed=True)
                        items[item.name] = {
                            "type": "file",
                            "path": str(item.resolve()),
                            "size": item.stat().st_size if item.exists() else 0,
                            "extension": item.suffix.lower()
                        }
                        
            except PermissionError:
                self.logger.warning(f"Permission denied accessing {path}")
            except Exception as e:
                self.logger.error(f"Error scanning {path}: {e}")
                
            return items
            
        # Build both full and filtered structures
        full_structure = scan_directory_full(self.project_path)
        filtered_structure = scan_directory_filtered(self.project_path)
        
        return {
            "root": str(self.project_path.resolve()),
            "full_structure": full_structure,
            "filtered_structure": filtered_structure,
            # Keep backward compatibility
            "structure": filtered_structure
        }
        
    def _generate_tree_visualization(self) -> str:
        """
        Generate ASCII tree visualization showing both full and filtered structures
        
        Returns:
            String containing ASCII tree representation with ignore indicators
        """
        def build_tree_lines(items: Dict[str, Any], prefix: str = "", show_ignored: bool = True) -> List[str]:
            lines = []
            item_list = list(items.items())
            
            def _all_contents_ignored(directory_items: Dict[str, Any]) -> bool:
                """Check if all contents of a directory are ignored."""
                if not directory_items:
                    return True
                    
                for item_name, item_info in directory_items.items():
                    if isinstance(item_info, dict):
                        if not item_info.get("ignored", False):
                            return False
                        if item_info.get("type") == "directory" and "items" in item_info:
                            if not _all_contents_ignored(item_info["items"]):
                                return False
                    # If item_info is not a dict, consider it not ignored
                    else:
                        return False
                return True
            
            for i, (name, info) in enumerate(item_list):
                is_last = (i == len(item_list) - 1)
                current_prefix = "└── " if is_last else "├── "
                
                # Add ignore indicator
                if isinstance(info, dict):
                    ignored = info.get("ignored", False)
                    ignore_marker = " 🚫" if ignored and show_ignored else ""
                    
                    if info.get("type") == "directory":
                        # Check if all contents are ignored
                        all_ignored = ignored and "items" in info and _all_contents_ignored(info["items"])
                        
                        if all_ignored and show_ignored:
                            # Collapse directory - show only the top-level folder with 🚫
                            lines.append(f"{prefix}{current_prefix}{name}/ 🚫 (all contents ignored)")
                        else:
                            # Show directory normally
                            lines.append(f"{prefix}{current_prefix}{name}/{ignore_marker}")
                            next_prefix = prefix + ("    " if is_last else "│   ")
                            if "items" in info:
                                lines.extend(build_tree_lines(info["items"], next_prefix, show_ignored))
                    else:
                        size_info = ""
                        if "size" in info:
                            size = info["size"]
                            if size > 1024 * 1024:
                                size_info = f" ({size // (1024*1024)}MB)"
                            elif size > 1024:
                                size_info = f" ({size // 1024}KB)"
                        lines.append(f"{prefix}{current_prefix}{name}{size_info}{ignore_marker}")
                else:
                    # Handle case where info is not a dictionary (e.g., error message)
                    lines.append(f"{prefix}{current_prefix}{name} (error: {info})")
                    
            return lines
            
        if not self.project_tree:
            return "No project structure available"
            
        # Generate both visualizations
        result = []
        
        # Full structure with ignore markers
        if "full_structure" in self.project_tree:
            result.append("📁 FULL PROJECT STRUCTURE (🚫 = ignored by .devixignore)")
            result.append("=" * 60)
            result.append(f"{self.project_path.name}/")
            result.extend(build_tree_lines(self.project_tree["full_structure"], "", True))
            result.append("")
            
        # Filtered structure (analyzed files only)  
        if "filtered_structure" in self.project_tree:
            result.append("🔍 ANALYZED STRUCTURE (filtered)")
            result.append("=" * 60)
            result.append(f"{self.project_path.name}/")
            result.extend(build_tree_lines(self.project_tree["filtered_structure"], "", False))
        elif "structure" in self.project_tree:
            # Fallback for backward compatibility
            result.append("🔍 PROJECT STRUCTURE")
            result.append("=" * 60)
            result.append(f"{self.project_path.name}/")
            result.extend(build_tree_lines(self.project_tree["structure"], "", False))
            
        return "\n".join(result) if result else "No project structure available"
        
    def _extract_code_fragments(self) -> List[Dict[str, Any]]:
        """
        Extract important code fragments from Python files
        
        Returns:
            List of code fragments with metadata
        """
        fragments = []
        
        for root, dirs, files in os.walk(self.project_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                
                if self._should_ignore_file(file_path):
                    continue
                    
                if file.endswith('.py'):
                    fragments.extend(self._extract_python_fragments(file_path))
                elif file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                    fragments.extend(self._extract_javascript_fragments(file_path))
                elif file.endswith(('.yml', '.yaml')):
                    fragments.extend(self._extract_yaml_fragments(file_path))
                    
        return fragments[:50]  # Limit to first 50 fragments
        
    def _extract_python_fragments(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract important fragments from Python files"""
        fragments = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return fragments
                
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract function definitions
                    lines = content.split('\n')
                    start_line = node.lineno - 1
                    end_line = min(start_line + 10, len(lines))  # Max 10 lines
                    
                    fragments.append({
                        "type": "function",
                        "name": node.name,
                        "file": str(file_path.resolve()),
                        "line": node.lineno,
                        "code": '\n'.join(lines[start_line:end_line]),
                        "docstring": ast.get_docstring(node) or ""
                    })
                    
                elif isinstance(node, ast.ClassDef):
                    # Extract class definitions
                    lines = content.split('\n')
                    start_line = node.lineno - 1
                    end_line = min(start_line + 15, len(lines))  # Max 15 lines
                    
                    fragments.append({
                        "type": "class",
                        "name": node.name,
                        "file": str(file_path.resolve()),
                        "line": node.lineno,
                        "code": '\n'.join(lines[start_line:end_line]),
                        "docstring": ast.get_docstring(node) or "",
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    })
                    
        except Exception as e:
            self.logger.error(f"Error extracting Python fragments from {file_path}: {e}")
            
        return fragments
        
    def _extract_javascript_fragments(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract important fragments from JavaScript/TypeScript files"""
        fragments = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Function declarations
                if line.startswith('function ') or 'function(' in line:
                    end_line = min(i + 10, len(lines))
                    fragments.append({
                        "type": "function",
                        "name": line.split('function')[1].split('(')[0].strip(),
                        "file": str(file_path.resolve()),
                        "line": i + 1,
                        "code": ''.join(lines[i:end_line])
                    })
                    
                # Class declarations
                elif line.startswith('class '):
                    end_line = min(i + 15, len(lines))
                    fragments.append({
                        "type": "class",
                        "name": line.split('class')[1].split('{')[0].strip(),
                        "file": str(file_path.resolve()),
                        "line": i + 1,
                        "code": ''.join(lines[i:end_line])
                    })
                    
        except Exception as e:
            self.logger.error(f"Error extracting JS fragments from {file_path}: {e}")
            
        return fragments
        
    def _extract_yaml_fragments(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract important fragments from YAML files"""
        fragments = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            fragments.append({
                "type": "config",
                "name": file_path.name,
                "file": str(file_path.resolve()),
                "line": 1,
                "code": content[:500] + "..." if len(content) > 500 else content
            })
            
        except Exception as e:
            self.logger.error(f"Error extracting YAML fragments from {file_path}: {e}")
            
        return fragments
        
    def _check_structure_issues(self) -> List[Dict[str, Any]]:
        """
        Check for common project structure issues
        
        Returns:
            List of detected structural issues
        """
        issues = []
        
        # Check for common structure patterns
        common_files = ['README.md', 'requirements.txt', 'setup.py', 'pyproject.toml', '.gitignore']
        missing_files = []
        
        for file_name in common_files:
            if not (self.project_path / file_name).exists():
                missing_files.append(file_name)
                
        if missing_files:
            issues.append({
                "type": "missing_files",
                "severity": "medium",
                "description": f"Missing common project files: {', '.join(missing_files)}"
            })
            
        # Check directory structure
        common_dirs = ['tests', 'test', 'docs', 'src']
        has_tests = any((self.project_path / d).exists() for d in ['tests', 'test'])
        
        if not has_tests:
            issues.append({
                "type": "missing_tests",
                "severity": "high", 
                "description": "No test directory found"
            })
            
        # Check for large files
        stats = self.get_file_stats()
        for file_type, count in stats.get("file_types", {}).items():
            if count > 100:
                issues.append({
                    "type": "too_many_files",
                    "severity": "low",
                    "description": f"Many {file_type} files ({count}), consider organization"
                })
                
        return issues
        
    def get_project_summary(self) -> Dict[str, Any]:
        """
        Get high-level project summary
        
        Returns:
            Summary of project structure and statistics
        """
        stats = self.get_file_stats()
        
        return {
            "total_files": stats.get("total_files", 0),
            "analyzed_files": stats.get("analyzed_files", 0),
            "file_types": stats.get("file_types", {}),
            "total_directories": len(stats.get("directories", [])),
            "code_fragments": len(self.code_fragments),
            "structure_issues": len(self.structure_issues),
            "project_root": str(self.project_path.resolve())
        }

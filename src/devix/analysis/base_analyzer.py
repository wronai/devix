"""
Base analyzer class for Devix analysis modules

Provides common functionality for all specialized analyzers including
file ignore patterns, statistics tracking, and logging.
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import fnmatch
import subprocess


class BaseAnalyzer(ABC):
    """
    Abstract base class for all Devix analyzers
    
    Provides common functionality including:
    - File ignore pattern handling
    - File statistics tracking  
    - Logging configuration
    - Common utility methods
    """
    
    def __init__(self, project_path: str = "../", logger: Optional[logging.Logger] = None):
        """
        Initialize base analyzer
        
        Args:
            project_path: Path to project directory to analyze
            logger: Optional logger instance
        """
        self.project_path = Path(project_path).resolve()
        self.logger = logger or self._setup_logger()
        self.ignore_patterns: Set[str] = set()
        self.file_stats: Dict[str, Any] = {
            "total_files": 0,
            "analyzed_files": 0,
            "skipped_files": 0,
            "analyzed_paths": [],
            "skipped_paths": [],
            "file_types": {},
            "directories": set(),
        }
        
        self._load_ignore_patterns()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the analyzer"""
        logger = logging.getLogger(f"devix.{self.__class__.__name__}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
        
    def _load_ignore_patterns(self) -> None:
        """Load ignore patterns from .devixignore file"""
        ignore_file = self.project_path / ".devixignore"
        
        # Default ignore patterns
        default_patterns = {
            "*.pyc", "*.pyo", "*.pyd", "__pycache__/", "*.so",
            ".git/", ".svn/", ".hg/", ".bzr/",
            "node_modules/", ".npm/", "bower_components/",
            ".venv/", "venv/", "env/", ".env",
            "*.log", "logs/", "*.tmp", "temp/",
            ".DS_Store", "Thumbs.db",
            "*.egg-info/", "dist/", "build/",
            ".pytest_cache/", ".coverage", "htmlcov/",
            ".mypy_cache/", ".tox/",
            ".idea/", ".vscode/settings.json",
            "*.min.js", "*.min.css",
        }
        
        self.ignore_patterns.update(default_patterns)
        
        if ignore_file.exists():
            try:
                with open(ignore_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.ignore_patterns.add(line)
                self.logger.info(f"Loaded {len(self.ignore_patterns)} ignore patterns")
            except Exception as e:
                self.logger.warning(f"Error loading ignore patterns: {e}")
                
    def _should_ignore_file(self, file_path: Path) -> bool:
        """
        Check if file should be ignored based on patterns
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be ignored
        """
        # Convert to relative path for pattern matching
        try:
            rel_path = file_path.relative_to(self.project_path)
            path_str = str(rel_path)
            
            for pattern in self.ignore_patterns:
                # Directory patterns
                if pattern.endswith('/'):
                    if any(part.startswith(pattern[:-1]) for part in rel_path.parts):
                        return True
                # File patterns
                elif fnmatch.fnmatch(path_str, pattern):
                    return True
                elif fnmatch.fnmatch(file_path.name, pattern):
                    return True
                    
        except ValueError:
            # File is outside project path
            return True
            
        return False
        
    def _update_file_stats(self, file_path: Path, analyzed: bool = True) -> None:
        """
        Update file statistics
        
        Args:
            file_path: Path that was processed
            analyzed: Whether file was analyzed or skipped
        """
        abs_path = str(file_path.resolve())
        
        self.file_stats["total_files"] += 1
        
        if analyzed:
            self.file_stats["analyzed_files"] += 1
            self.file_stats["analyzed_paths"].append(abs_path)
        else:
            self.file_stats["skipped_files"] += 1  
            self.file_stats["skipped_paths"].append(abs_path)
            
        # Track file types
        suffix = file_path.suffix.lower()
        if suffix:
            self.file_stats["file_types"][suffix] = self.file_stats["file_types"].get(suffix, 0) + 1
        else:
            self.file_stats["file_types"]["no_extension"] = self.file_stats["file_types"].get("no_extension", 0) + 1
            
        # Track directories
        self.file_stats["directories"].add(str(file_path.parent.resolve()))
        
    def _run_command(self, command: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """
        Run system command and return results
        
        Args:
            command: Command to run as list
            cwd: Working directory
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {' '.join(command)}")
            return -1, "", "Command timed out"
        except Exception as e:
            self.logger.error(f"Error running command {' '.join(command)}: {e}")
            return -1, "", str(e)
            
    def get_file_stats(self) -> Dict[str, Any]:
        """Get current file statistics"""
        stats = self.file_stats.copy()
        stats["directories"] = list(stats["directories"])
        return stats
        
    def reset_stats(self) -> None:
        """Reset file statistics"""
        self.file_stats = {
            "total_files": 0,
            "analyzed_files": 0,
            "skipped_files": 0,
            "analyzed_paths": [],
            "skipped_paths": [],
            "file_types": {},
            "directories": set(),
        }
        
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        Perform analysis and return results
        
        Returns:
            Dictionary containing analysis results
        """
        pass
        
    def __str__(self) -> str:
        """String representation of analyzer"""
        return f"{self.__class__.__name__}(project_path='{self.project_path}')"
        
    def __repr__(self) -> str:
        """Detailed representation of analyzer"""
        return (f"{self.__class__.__name__}("
                f"project_path='{self.project_path}', "
                f"ignore_patterns={len(self.ignore_patterns)}, "
                f"analyzed_files={self.file_stats['analyzed_files']})")

#!/usr/bin/env python3
"""
Application Monitor - Monitorowanie aplikacji i zbieranie metryk
"""

import subprocess
import time
import re
import json
import os
import psutil
import docker
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import requests
import ast
import threading
from datetime import datetime
import fnmatch

class ApplicationMonitor:
    """Monitor aplikacji - sprawdza testy, logi, metryki"""
    
    def __init__(self, project_dir: Path, config: Dict):
        self.project_dir = Path(project_dir)
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.docker_client = None
        self.process = None
        self.monitoring_thread = None
        self.logs_buffer = []
        self.ignore_patterns = self._load_ignore_patterns()
        
        # Tracking ścieżek dla ulepszonego raportowania
        self.analyzed_files = set()
        self.skipped_files = set()
        self.project_structure = {}
        self.code_fragments = []
        
        # Spróbuj połączyć z Docker
        try:
            self.docker_client = docker.from_env()
            self.logger.info("Docker client connected")
        except:
            self.logger.warning("Docker not available, will use subprocess")
    
    def _load_ignore_patterns(self) -> List[str]:
        """Wczytaj wzorce z .devixignore"""
        ignore_file = self.project_dir / '.devixignore'
        patterns = []
        
        self.logger.info(f"Looking for .devixignore at: {ignore_file}")
        self.logger.info(f"Project dir is: {self.project_dir}")
        self.logger.info(f".devixignore exists: {ignore_file.exists()}")
        
        if ignore_file.exists():
            try:
                with open(ignore_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
                self.logger.info(f"Loaded {len(patterns)} ignore patterns from .devixignore: {patterns}")
            except Exception as e:
                self.logger.error(f"Failed to read .devixignore: {e}")
        else:
            self.logger.warning(f".devixignore not found at {ignore_file}")
        
        return patterns
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Sprawdź czy plik powinien być ignorowany"""
        rel_path = file_path.relative_to(self.project_dir)
        rel_path_str = str(rel_path)
        file_name = file_path.name
        absolute_path = str(file_path.absolute())
        
        for pattern in self.ignore_patterns:
            # Sprawdź dokładną nazwę pliku
            if pattern == file_name:
                self.logger.debug(f"Ignoring {file_path} - matches filename pattern: {pattern}")
                self.skipped_files.add(absolute_path)
                return True
            
            # Sprawdź względną ścieżkę
            if pattern == rel_path_str:
                self.logger.debug(f"Ignoring {file_path} - matches path pattern: {pattern}")
                self.skipped_files.add(absolute_path)
                return True
            
            # Sprawdź czy folder jest ignorowany
            if pattern.endswith('/') and rel_path_str.startswith(pattern):
                self.logger.debug(f"Ignoring {file_path} - matches directory pattern: {pattern}")
                self.skipped_files.add(absolute_path)
                return True
            
            # Sprawdź wzorce wildcards
            if '*' in pattern:
                if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(rel_path_str, pattern):
                    self.logger.debug(f"Ignoring {file_path} - matches wildcard pattern: {pattern}")
                    self.skipped_files.add(absolute_path)
                    return True
        
        # Jeśli plik nie jest ignorowany, dodaj do analizowanych
        self.analyzed_files.add(absolute_path)
        return False
    
    def scan_project_structure(self) -> Dict:
        """Skanuj i zwróć strukturę projektu dla raportowania"""
        structure = {
            'total_files': 0,
            'analyzed_files_count': len(self.analyzed_files),
            'skipped_files_count': len(self.skipped_files),
            'analyzed_files_list': sorted(list(self.analyzed_files)),
            'skipped_files_list': sorted(list(self.skipped_files)),
            'directories': {},
            'file_types': {},
            'project_tree': self._generate_project_tree(),
            'analysis_summary': self._generate_analysis_summary()
        }
        
        # Skanuj wszystkie pliki w projekcie używając os.walk
        import os
        for root, dirs, files in os.walk(self.project_dir):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                structure['total_files'] += 1
                
                # Zlicz typy plików
                ext = file_path.suffix.lower() or 'no_extension'
                structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
                
                # Zlicz pliki w katalogach
                try:
                    rel_dir = str(file_path.parent.relative_to(self.project_dir))
                    if rel_dir == '.':
                        rel_dir = 'root'
                    structure['directories'][rel_dir] = structure['directories'].get(rel_dir, 0) + 1
                except ValueError:
                    # Handle case where file_path is not relative to project_dir
                    continue
        
        return structure
    
    def _generate_analysis_summary(self) -> Dict:
        """Generuj szczegółowe podsumowanie analizy z absolutnymi ścieżkami"""
        summary = {
            'analyzed_files_by_type': {},
            'skipped_files_by_type': {},
            'analyzed_files_by_directory': {},
            'skipped_files_by_directory': {},
            'total_analyzed_size': 0,
            'total_skipped_size': 0,
            'analysis_coverage_percentage': 0.0
        }
        
        # Analizuj pliki przeanalizowane
        for file_path in self.analyzed_files:
            path_obj = Path(file_path)
            if path_obj.exists():
                # Typ pliku
                ext = path_obj.suffix.lower() or 'no_extension'
                summary['analyzed_files_by_type'][ext] = summary['analyzed_files_by_type'].get(ext, 0) + 1
                
                # Katalog
                try:
                    rel_dir = str(path_obj.parent.relative_to(self.project_dir))
                    if rel_dir == '.':
                        rel_dir = 'root'
                    summary['analyzed_files_by_directory'][rel_dir] = summary['analyzed_files_by_directory'].get(rel_dir, 0) + 1
                except (ValueError, OSError):
                    pass
                
                # Rozmiar
                try:
                    summary['total_analyzed_size'] += path_obj.stat().st_size
                except (OSError, FileNotFoundError):
                    pass
        
        # Analizuj pliki pominięte
        for file_path in self.skipped_files:
            path_obj = Path(file_path)
            if path_obj.exists():
                # Typ pliku
                ext = path_obj.suffix.lower() or 'no_extension'
                summary['skipped_files_by_type'][ext] = summary['skipped_files_by_type'].get(ext, 0) + 1
                
                # Katalog
                try:
                    rel_dir = str(path_obj.parent.relative_to(self.project_dir))
                    if rel_dir == '.':
                        rel_dir = 'root'
                    summary['skipped_files_by_directory'][rel_dir] = summary['skipped_files_by_directory'].get(rel_dir, 0) + 1
                except (ValueError, OSError):
                    pass
                
                # Rozmiar
                try:
                    summary['total_skipped_size'] += path_obj.stat().st_size
                except (OSError, FileNotFoundError):
                    pass
        
        # Oblicz procent pokrycia analizy
        total_files = len(self.analyzed_files) + len(self.skipped_files)
        if total_files > 0:
            summary['analysis_coverage_percentage'] = (len(self.analyzed_files) / total_files) * 100
        
        return summary
    
    def _generate_project_tree(self, max_depth: int = 3) -> str:
        """Generuj ASCII art drzewa projektu"""
        tree_lines = []
        tree_lines.append(f"📁 {self.project_dir.name}/")
        
        def add_directory(path: Path, prefix: str, depth: int):
            if depth > max_depth:
                return
                
            items = []
            try:
                items = sorted([p for p in path.iterdir() if not self._should_ignore_file(p)])
            except PermissionError:
                return
                
            for i, item in enumerate(items[:10]):  # Limit to 10 items per directory
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                next_prefix = prefix + ("    " if is_last else "│   ")
                
                if item.is_dir():
                    tree_lines.append(f"{prefix}{current_prefix}📁 {item.name}/")
                    add_directory(item, next_prefix, depth + 1)
                else:
                    icon = self._get_file_icon(item.suffix)
                    tree_lines.append(f"{prefix}{current_prefix}{icon} {item.name}")
        
        add_directory(self.project_dir, "", 0)
        return "\n".join(tree_lines)
    
    def _get_file_icon(self, suffix: str) -> str:
        """Zwróć ikonę dla typu pliku"""
        icons = {
            '.py': '🐍', '.js': '⚡', '.ts': '🔷', '.html': '🌐', '.css': '🎨',
            '.json': '📄', '.yaml': '⚙️', '.yml': '⚙️', '.md': '📝', '.txt': '📄',
            '.sql': '🗃️', '.sh': '⚡', '.dockerfile': '🐳', '.gitignore': '🚫',
            '.env': '⚙️', '.ini': '⚙️', '.cfg': '⚙️', '.xml': '📄'
        }
        return icons.get(suffix.lower(), '📄')
    
    def extract_code_fragments(self, issues: List[str]) -> List[Dict]:
        """Wyciągnij fragmenty kodu związane z problemami"""
        fragments = []
        
        for issue in issues:
            # Spróbuj znaleźć plik i linię z issue
            if '::' in issue and any(ext in issue for ext in ['.py', '.js', '.ts']):
                try:
                    # Parsuj issue aby znaleźć plik i funkcję/klasę
                    parts = issue.split('::')
                    if len(parts) >= 2:
                        file_part = parts[0].split(' ')[-1]  # Ostatnia część przed ::
                        function_part = parts[1].split(' ')[0]  # Pierwsza część po ::
                        
                        # Znajdź plik w projekcie
                        for analyzed_file in self.analyzed_files:
                            if file_part in analyzed_file:
                                fragment = self._extract_fragment_from_file(
                                    Path(analyzed_file), function_part, issue
                                )
                                if fragment:
                                    fragments.append(fragment)
                                break
                except Exception as e:
                    self.logger.debug(f"Could not extract code fragment for issue: {issue}, error: {e}")
        
        return fragments
    
    def _extract_fragment_from_file(self, file_path: Path, target: str, issue: str) -> Optional[Dict]:
        """Wyciągnij fragment kodu z pliku"""
        try:
            if not file_path.exists() or file_path.suffix != '.py':
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Znajdź linię z target (funkcja/klasa)
            for i, line in enumerate(lines):
                if f'def {target}(' in line or f'class {target}(' in line:
                    # Wyciągnij fragment (funkcja + kilka linii kontekstu)
                    start_line = max(0, i - 2)
                    end_line = min(len(lines), i + 10)
                    
                    return {
                        'file': str(file_path.relative_to(self.project_dir)),
                        'absolute_path': str(file_path),
                        'line_start': start_line + 1,
                        'line_end': end_line + 1,
                        'target': target,
                        'issue': issue,
                        'code': ''.join(lines[start_line:end_line]),
                        'language': 'python'
                    }
        except Exception as e:
            self.logger.debug(f"Error extracting fragment from {file_path}: {e}")
        
        return None
    
    def check_all(self) -> Tuple[List[str], Dict]:
        """Sprawdź wszystkie metryki i zwróć issues oraz metrics"""
        issues = []
        metrics = {}
        
        # 1. Sprawdź testy
        test_issues, test_metrics = self.run_tests()
        issues.extend(test_issues)
        metrics.update(test_metrics)
        
        # 2. Sprawdź jakość kodu
        quality_issues, quality_metrics = self.check_code_quality()
        issues.extend(quality_issues)
        metrics.update(quality_metrics)
        
        # 3. Uruchom i monitoruj aplikację
        runtime_issues, runtime_metrics = self.monitor_runtime()
        issues.extend(runtime_issues)
        metrics.update(runtime_metrics)
        
        # 4. Sprawdź wydajność
        perf_issues, perf_metrics = self.check_performance()
        issues.extend(perf_issues)
        metrics.update(perf_metrics)
        
        # 5. Sprawdź bezpieczeństwo
        security_issues = self.check_security()
        issues.extend(security_issues)
        
        # 6. Sprawdź dokumentację
        doc_issues = self.check_documentation()
        issues.extend(doc_issues)
        
        return issues, metrics
    
    def run_tests(self) -> Tuple[List[str], Dict]:
        """Uruchom testy i analizuj wyniki"""
        self.logger.info("Starting test execution and analysis")
        issues = []
        metrics = {}
        
        try:
            # Sprawdź czy istnieje pytest.ini lub setup.cfg
            test_config = self._find_test_config()
            self.logger.debug(f"Found test config: {test_config}")
            
            # Uruchom pytest
            test_result = self._execute_pytest()
            if test_result is None:
                self.logger.error("Failed to execute pytest")
                return ["Failed to execute pytest"], {}
            
            # Analizuj wyniki testów
            test_issues = self._analyze_test_results(test_result)
            issues.extend(test_issues)
            
            # Analizuj coverage
            coverage_issues, coverage_metrics = self._analyze_coverage()
            issues.extend(coverage_issues)
            metrics.update(coverage_metrics)
            
            # Analizuj test report
            report_issues, report_metrics = self._analyze_test_report()
            issues.extend(report_issues)
            metrics.update(report_metrics)
            
            self.logger.info(f"Test analysis completed. Found {len(issues)} issues, {len(metrics)} metrics")
            
        except subprocess.TimeoutExpired:
            self.logger.error("Tests timed out after 5 minutes")
            issues.append("Tests timeout after 5 minutes")
        except Exception as e:
            self.logger.error(f"Test execution error: {e}", exc_info=True)
            issues.append(f"Test execution error: {str(e)}")
        
        return issues, metrics
    
    def _execute_pytest(self) -> Optional[subprocess.CompletedProcess]:
        """Execute pytest with coverage and return result"""
        self.logger.debug("Executing pytest with coverage")
        
        cmd = [
            'pytest',
            '--tb=short',
            '--cov=' + str(self.project_dir / 'src'),
            '--cov-report=json',
            '--cov-report=term',
            '--json-report',
            '--json-report-file=test-report.json',
            '-v'
        ]
        
        self.logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            self.logger.info(f"Pytest completed with return code: {result.returncode}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to execute pytest: {e}", exc_info=True)
            return None
    
    def _analyze_test_results(self, result: subprocess.CompletedProcess) -> List[str]:
        """Analyze pytest output for failed tests and errors"""
        self.logger.debug("Analyzing test results for failures and errors")
        issues = []
        
        if result.returncode != 0:
            self.logger.warning(f"Tests failed with return code: {result.returncode}")
            
            # Znajdź failed tests
            failed_tests = re.findall(r'FAILED (.*?) -', result.stdout)
            for test in failed_tests:
                self.logger.warning(f"Failed test found: {test}")
                issues.append(f"Test failed: {test}")
            
            # Znajdź errors
            errors = re.findall(r'ERROR (.*?) -', result.stdout)
            for error in errors:
                self.logger.error(f"Test error found: {error}")
                issues.append(f"Test error: {error}")
        else:
            self.logger.info("All tests passed successfully")
        
        return issues
    
    def _analyze_coverage(self) -> Tuple[List[str], Dict]:
        """Analyze test coverage data"""
        self.logger.debug("Analyzing test coverage data")
        issues = []
        metrics = {}
        
        coverage_file = self.project_dir / 'coverage.json'
        if not coverage_file.exists():
            self.logger.warning("Coverage file not found")
            return issues, metrics
        
        try:
            with open(coverage_file) as f:
                coverage_data = json.load(f)
                total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
                metrics['test_coverage'] = round(total_coverage, 2)
                self.logger.info(f"Total test coverage: {total_coverage:.2f}%")
                
                # Znajdź pliki z niskim coverage
                if 'files' in coverage_data:
                    low_coverage_count = 0
                    for file_path, file_data in coverage_data['files'].items():
                        file_coverage = file_data.get('summary', {}).get('percent_covered', 0)
                        if file_coverage < 50:
                            low_coverage_count += 1
                            self.logger.warning(f"Low coverage in {Path(file_path).name}: {file_coverage:.1f}%")
                            issues.append(f"Low coverage in {Path(file_path).name}: {file_coverage:.1f}%")
                    
                    if low_coverage_count == 0:
                        self.logger.info("All files have adequate test coverage (>50%)")
        
        except Exception as e:
            self.logger.error(f"Failed to analyze coverage: {e}", exc_info=True)
        
        return issues, metrics
    
    def _analyze_test_report(self) -> Tuple[List[str], Dict]:
        """Analyze detailed test report"""
        self.logger.debug("Analyzing detailed test report")
        issues = []
        metrics = {}
        
        test_report_file = self.project_dir / 'test-report.json'
        if not test_report_file.exists():
            self.logger.warning("Test report file not found")
            return issues, metrics
        
        try:
            with open(test_report_file) as f:
                test_report = json.load(f)
                
                # Extract metrics
                summary = test_report.get('summary', {})
                metrics['total_tests'] = summary.get('total', 0)
                metrics['passed_tests'] = summary.get('passed', 0)
                metrics['failed_tests'] = summary.get('failed', 0)
                
                self.logger.info(f"Test summary - Total: {metrics['total_tests']}, "
                               f"Passed: {metrics['passed_tests']}, Failed: {metrics['failed_tests']}")
                
                # Dodaj szczegóły o wolnych testach
                if 'tests' in test_report:
                    slow_tests = [t for t in test_report['tests'] 
                                if t.get('duration', 0) > 1.0]
                    
                    if slow_tests:
                        self.logger.info(f"Found {len(slow_tests)} slow tests (>1s)")
                        for test in slow_tests[:3]:  # Top 3 najwolniejsze
                            duration = test['duration']
                            self.logger.warning(f"Slow test: {test['nodeid']} ({duration:.2f}s)")
                            issues.append(f"Slow test: {test['nodeid']} ({duration:.2f}s)")
                    else:
                        self.logger.info("No slow tests detected")
        
        except Exception as e:
            self.logger.error(f"Failed to analyze test report: {e}", exc_info=True)
        
        return issues, metrics
    
    def check_code_quality(self) -> Tuple[List[str], Dict]:
        """Sprawdź jakość kodu za pomocą różnych narzędzi"""
        self.logger.info("Starting comprehensive code quality analysis")
        issues = []
        metrics = {}
        
        # Uruchom pylint
        pylint_issues, pylint_metrics = self._run_pylint_analysis()
        issues.extend(pylint_issues)
        metrics.update(pylint_metrics)
        
        # Uruchom flake8
        flake8_issues = self._run_flake8_analysis()
        issues.extend(flake8_issues)
        
        # Sprawdź złożoność kodu
        complexity_issues = self._run_complexity_analysis()
        issues.extend(complexity_issues)
        
        # Sprawdź code smells
        code_smells = self._detect_code_smells()
        issues.extend(code_smells)
        
        self.logger.info(f"Code quality analysis completed. Found {len(issues)} issues, {len(metrics)} metrics")
        return issues, metrics
    
    def _run_pylint_analysis(self) -> Tuple[List[str], Dict]:
        """Run pylint static analysis"""
        self.logger.debug("Running pylint static analysis")
        issues = []
        metrics = {}
        
        # Znajdź rzeczywiste foldery z kodem Python zamiast hardcoded 'src/'
        python_dirs = []
        for dir_name in ['backend', 'frontend/src', 'devix']:
            dir_path = self.project_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                python_dirs.append(str(dir_path))
        
        if not python_dirs:
            self.logger.warning("No Python source directories found for pylint analysis")
            return issues, metrics
            
        try:
            result = subprocess.run(
                ['pylint'] + python_dirs + ['--output-format=json'],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                pylint_results = json.loads(result.stdout)
                self.logger.info(f"Pylint found {len(pylint_results)} issues")
                
                # Oblicz score
                total_statements = sum(r.get('line', 0) for r in pylint_results)
                if total_statements > 0:
                    # Uproszczona kalkulacja score
                    errors = len([r for r in pylint_results if r['type'] == 'error'])
                    warnings = len([r for r in pylint_results if r['type'] == 'warning'])
                    score = max(0, 10 - (errors * 0.5 + warnings * 0.1))
                    metrics['code_quality'] = round(score, 2)
                    
                    self.logger.info(f"Pylint score: {score:.2f}/10 (Errors: {errors}, Warnings: {warnings})")
                
                # Zbierz najważniejsze problemy
                error_count = 0
                warning_count = 0
                for result_item in pylint_results[:10]:  # Top 10 issues
                    if result_item['type'] in ['error', 'fatal']:
                        error_count += 1
                        self.logger.error(f"Pylint error in {result_item['path']}: {result_item['message']}")
                        issues.append(f"Code error in {result_item['path']}: {result_item['message']}")
                    elif result_item['type'] == 'warning' and 'unused' not in result_item['message'].lower():
                        warning_count += 1
                        self.logger.warning(f"Pylint warning: {result_item['message']}")
                        issues.append(f"Code warning: {result_item['message']}")
                
                if error_count == 0 and warning_count == 0:
                    self.logger.info("No critical pylint issues found")
            else:
                self.logger.warning("Pylint produced no output")
                
        except FileNotFoundError:
            self.logger.warning("Pylint not found - skipping static analysis")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse pylint JSON output: {e}")
        except Exception as e:
            self.logger.error(f"Pylint analysis failed: {e}", exc_info=True)
        
        return issues, metrics
    
    def _run_flake8_analysis(self) -> List[str]:
        """Run flake8 style analysis"""
        self.logger.debug("Running flake8 style analysis")
        issues = []
        
        # Znajdź rzeczywiste foldery z kodem Python zamiast hardcoded 'src/'
        python_dirs = []
        for dir_name in ['backend', 'frontend/src', 'devix']:
            dir_path = self.project_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                python_dirs.append(str(dir_path))
        
        if not python_dirs:
            self.logger.warning("No Python source directories found for flake8 analysis")
            return issues, metrics
            
        try:
            result = subprocess.run(
                ['flake8'] + python_dirs + ['--format=json'],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                try:
                    flake8_issues = json.loads(result.stdout)
                    self.logger.info(f"Flake8 found {len(flake8_issues)} style issues")
                    
                    for issue in flake8_issues[:5]:  # Top 5
                        self.logger.warning(f"Style issue in {issue['filename']}: {issue['text']}")
                        issues.append(f"Style issue in {issue['filename']}: {issue['text']}")
                    
                    if len(flake8_issues) == 0:
                        self.logger.info("No flake8 style issues found")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse flake8 JSON output: {e}")
                    # Fallback - try to parse as plain text
                    if result.stdout:
                        lines = result.stdout.strip().split('\n')[:5]
                        for line in lines:
                            if line.strip():
                                issues.append(f"Style issue: {line}")
                        self.logger.info(f"Parsed {len(lines)} flake8 issues from plain text")
            else:
                self.logger.info("Flake8 found no issues")
                
        except FileNotFoundError:
            self.logger.warning("Flake8 not found - skipping style analysis")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse flake8 JSON output: {e}")
        except Exception as e:
            self.logger.error(f"Flake8 analysis failed: {e}", exc_info=True)
        
        return issues
    
    def _run_complexity_analysis(self) -> List[str]:
        """Run radon complexity analysis"""
        self.logger.debug("Running complexity analysis with radon")
        issues = []
        
        # Znajdź rzeczywiste foldery z kodem Python zamiast hardcoded 'src/'
        python_dirs = []
        for dir_name in ['backend', 'frontend/src', 'devix']:
            dir_path = self.project_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                python_dirs.append(str(dir_path))
        
        if not python_dirs:
            self.logger.warning("No Python source directories found for radon analysis")
            return issues, metrics
            
        try:
            result = subprocess.run(
                ['radon', 'cc'] + python_dirs + ['-j'],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                complexity_data = json.loads(result.stdout)
                high_complexity_count = 0
                
                for file_path, file_data in complexity_data.items():
                    # Sprawdź czy plik powinien być zignorowany
                    file_path_obj = Path(file_path)
                    if self._should_ignore_file(file_path_obj):
                        self.logger.debug(f"Ignoring complexity analysis for {file_path} (matches .devixignore pattern)")
                        continue
                        
                    for func in file_data:
                        if func['complexity'] > 10:
                            high_complexity_count += 1
                            self.logger.warning(
                                f"High complexity in {Path(file_path).name}::{func['name']} "
                                f"(CC={func['complexity']})"
                            )
                            issues.append(
                                f"High complexity in {Path(file_path).name}::{func['name']} "
                                f"(CC={func['complexity']})"
                            )
                
                if high_complexity_count == 0:
                    self.logger.info("No high complexity functions found (CC>10)")
                else:
                    self.logger.info(f"Found {high_complexity_count} high complexity functions")
            else:
                self.logger.info("Radon found no complexity issues")
                
        except FileNotFoundError:
            self.logger.warning("Radon not found - skipping complexity analysis")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse radon JSON output: {e}")
        except Exception as e:
            self.logger.error(f"Radon complexity analysis failed: {e}", exc_info=True)
        
        return issues
    
    def monitor_runtime(self) -> Tuple[List[str], Dict]:
        """Monitoruj działającą aplikację"""
        issues = []
        metrics = {}
        
        try:
            # Uruchom aplikację
            if self._is_docker_project():
                issues_docker, metrics_docker = self._monitor_docker()
                issues.extend(issues_docker)
                metrics.update(metrics_docker)
            else:
                issues_process, metrics_process = self._monitor_process()
                issues.extend(issues_process)
                metrics.update(metrics_process)
            
            # Analizuj logi
            log_issues = self._analyze_logs()
            issues.extend(log_issues)
            
        except Exception as e:
            issues.append(f"Runtime monitoring error: {str(e)}")
            self.logger.error(f"Runtime error: {e}", exc_info=True)
        
        return issues, metrics
    
    def check_performance(self) -> Tuple[List[str], Dict]:
        """Sprawdź wydajność aplikacji"""
        issues = []
        metrics = {}
        
        try:
            # Sprawdź czy aplikacja ma endpoint healthcheck
            health_url = self.config.get('health_endpoint', 'http://localhost:8011/health')
            
            # Test response time
            response_times = []
            for _ in range(5):
                start = time.time()
                try:
                    response = requests.get(health_url, timeout=5)
                    response_time = (time.time() - start) * 1000  # ms
                    response_times.append(response_time)
                    
                    if response.status_code != 200:
                        issues.append(f"Health check returned {response.status_code}")
                except requests.exceptions.RequestException as e:
                    issues.append(f"Health check failed: {str(e)}")
                    break
                
                time.sleep(0.5)
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                metrics['performance'] = round(avg_response_time, 2)
                
                if avg_response_time > self.config.get('performance_threshold', 1000):
                    issues.append(f"Slow response time: {avg_response_time:.0f}ms")
            
            # Memory usage
            memory_usage = self._check_memory_usage()
            if memory_usage:
                metrics['memory_mb'] = memory_usage
                if memory_usage > self.config.get('memory_threshold', 500):  # 500MB threshold
                    issues.append(f"High memory usage: {memory_usage}MB")
            
            # CPU usage
            cpu_usage = self._check_cpu_usage()
            if cpu_usage:
                metrics['cpu_percent'] = cpu_usage
                if cpu_usage > 80:
                    issues.append(f"High CPU usage: {cpu_usage}%")
            
        except Exception as e:
            self.logger.error(f"Performance check error: {e}")
        
        return issues, metrics
    
    def check_security(self) -> List[str]:
        """Sprawdź bezpieczeństwo kodu"""
        issues = []
        
        # Znajdź rzeczywiste foldery z kodem Python zamiast hardcoded 'src/'
        python_dirs = []
        for dir_name in ['backend', 'frontend/src', 'devix']:
            dir_path = self.project_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                python_dirs.append(str(dir_path))
        
        if not python_dirs:
            self.logger.warning("No Python source directories found for bandit analysis")
            return issues
            
        try:
            # Bandit dla Python - użyj rzeczywistych folderów
            result = subprocess.run(
                ['bandit', '-r'] + python_dirs + ['-f', 'json'],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                bandit_results = json.loads(result.stdout)
                for issue in bandit_results.get('results', [])[:5]:
                    # Sprawdź czy plik powinien być zignorowany
                    file_path_obj = Path(issue['filename'])
                    if self._should_ignore_file(file_path_obj):
                        self.logger.debug(f"Ignoring security issue in {issue['filename']} (matches .devixignore pattern)")
                        continue
                        
                    if issue['issue_severity'] in ['HIGH', 'MEDIUM']:
                        issues.append(f"Security issue: {issue['issue_text']} in {Path(issue['filename']).name}")
        except:
            pass
        
        # Sprawdź znane podatności w dependencies
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                safety_results = json.loads(result.stdout)
                for vuln in safety_results[:3]:
                    issues.append(f"Vulnerable dependency: {vuln['package']} {vuln['installed_version']}")
        except:
            pass
        
        # Sprawdź hardcoded secrets
        secrets = self._check_hardcoded_secrets()
        issues.extend(secrets)
        
        return issues
    
    def check_documentation(self) -> List[str]:
        """Sprawdź dokumentację"""
        issues = []
        
        # Sprawdź brakujące docstringi
        missing_docs = self._find_missing_docstrings()
        for item in missing_docs[:5]:  # Top 5
            issues.append(f"Missing docstring: {item}")
        
        # Sprawdź README
        readme_path = self.project_dir / 'README.md'
        if not readme_path.exists():
            issues.append("Missing README.md")
        elif readme_path.stat().st_size < 500:
            issues.append("README.md is too short (less than 500 characters)")
        
        # Sprawdź requirements.txt
        req_path = self.project_dir / 'requirements.txt'
        if not req_path.exists():
            issues.append("Missing requirements.txt")
        
        return issues
    
    # === Helper methods ===
    
    def _find_test_config(self) -> Optional[Path]:
        """Znajdź konfigurację testów"""
        for config_file in ['pytest.ini', 'setup.cfg', 'pyproject.toml']:
            path = self.project_dir / config_file
            if path.exists():
                return path
        return None
    
    def _is_docker_project(self) -> bool:
        """Sprawdź czy projekt używa Docker"""
        docker_compose = self.project_dir / self.config.get('docker_compose_file', 'docker-compose.yml')
        dockerfile = self.project_dir / 'Dockerfile'
        return docker_compose.exists() or dockerfile.exists()
    
    def _monitor_docker(self) -> Tuple[List[str], Dict]:
        """Monitoruj kontenery Docker"""
        issues = []
        metrics = {}
        
        if not self.docker_client:
            return issues, metrics
        
        try:
            # Uruchom docker-compose
            subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=self.project_dir,
                capture_output=True
            )
            
            time.sleep(5)  # Poczekaj na start
            
            # Sprawdź kontenery
            containers = self.docker_client.containers.list()
            for container in containers:
                if container.status != 'running':
                    issues.append(f"Container {container.name} is not running: {container.status}")
                
                # Zbierz logi
                logs = container.logs(tail=100).decode('utf-8')
                self.logs_buffer.append(logs)
                
                # Sprawdź zużycie zasobów
                stats = container.stats(stream=False)
                memory_usage = stats['memory_stats'].get('usage', 0) / 1024 / 1024  # MB
                if memory_usage > 500:
                    issues.append(f"Container {container.name} high memory: {memory_usage:.0f}MB")
            
        except Exception as e:
            issues.append(f"Docker monitoring error: {str(e)}")
        
        return issues, metrics
    
    def _monitor_process(self) -> Tuple[List[str], Dict]:
        """Monitoruj proces aplikacji"""
        issues = []
        metrics = {}
        
        try:
            # Uruchom aplikację
            run_command = self.config.get('run_command', 'python main.py')
            self.process = subprocess.Popen(
                run_command.split(),
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitoruj przez 10 sekund
            start_time = time.time()
            while time.time() - start_time < 10:
                if self.process.poll() is not None:
                    # Proces się zakończył
                    stdout, stderr = self.process.communicate()
                    if stderr:
                        issues.append(f"Application crashed: {stderr[:200]}")
                    break
                
                # Zbieraj logi
                try:
                    stdout_line = self.process.stdout.readline()
                    if stdout_line:
                        self.logs_buffer.append(stdout_line)
                except:
                    pass
                
                time.sleep(0.1)
            
            # Zatrzymaj proces
            if self.process and self.process.poll() is None:
                self.process.terminate()
                time.sleep(1)
                if self.process.poll() is None:
                    self.process.kill()
            
        except Exception as e:
            issues.append(f"Process monitoring error: {str(e)}")
        
        return issues, metrics
    
    def _analyze_logs(self) -> List[str]:
        """Analizuj zebrane logi"""
        issues = []
        
        all_logs = '\n'.join(self.logs_buffer)
        
        # Szukaj błędów
        error_patterns = self.config.get('error_patterns', [])
        for pattern in error_patterns:
            matches = re.findall(f'.*{pattern}.*', all_logs, re.IGNORECASE)
            for match in matches[:3]:  # Max 3 per pattern
                issues.append(f"Log error: {match[:100]}")
        
        # Sprawdź brak logów
        if len(self.logs_buffer) < 5:
            issues.append("Application produces very few logs")
        
        # Clear buffer
        self.logs_buffer = []
        
        return issues
    
    def _check_memory_usage(self) -> Optional[float]:
        """Sprawdź zużycie pamięci"""
        try:
            if self.process and self.process.poll() is None:
                process = psutil.Process(self.process.pid)
                return process.memory_info().rss / 1024 / 1024  # MB
        except:
            pass
        return None
    
    def _check_cpu_usage(self) -> Optional[float]:
        """Sprawdź zużycie CPU"""
        try:
            if self.process and self.process.poll() is None:
                process = psutil.Process(self.process.pid)
                return process.cpu_percent(interval=1.0)
        except:
            pass
        return None
    
    def _detect_code_smells(self) -> List[str]:
        """Wykryj code smells"""
        issues = []
        
        for py_file in self.project_dir.rglob('*.py'):
            if 'test' in py_file.name or '__pycache__' in str(py_file):
                continue
                
            # Sprawdź czy plik jest w .devixignore
            if self._should_ignore_file(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    lines = content.splitlines()
                
                # Długie pliki
                if len(lines) > 500:
                    issues.append(f"File too long: {py_file.name} ({len(lines)} lines)")
                
                # Długie funkcje
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_lines = node.end_lineno - node.lineno
                        if func_lines > 50:
                            issues.append(f"Long function: {py_file.name}::{node.name} ({func_lines} lines)")
                
                # TODO comments
                todos = len(re.findall(r'#\s*TODO', content))
                if todos > 3:
                    issues.append(f"Many TODOs in {py_file.name}: {todos}")
                
            except:
                pass
        
        return issues
    
    def _check_hardcoded_secrets(self) -> List[str]:
        """Sprawdź hardcoded secrets"""
        issues = []
        
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'][\w]+["\']', 'API key'),
            (r'password\s*=\s*["\'][\w]+["\']', 'Password'),
            (r'token\s*=\s*["\'][\w]+["\']', 'Token'),
            (r'secret\s*=\s*["\'][\w]+["\']', 'Secret'),
        ]
        
        for py_file in self.project_dir.rglob('*.py'):
            if 'test' in py_file.name:
                continue
                
            # Sprawdź czy plik jest w .devixignore
            if self._should_ignore_file(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                for pattern, name in secret_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues.append(f"Possible hardcoded {name} in {py_file.name}")
            except:
                pass
        
        return issues[:3]  # Max 3
    
    def _find_missing_docstrings(self) -> List[str]:
        """Znajdź brakujące docstringi"""
        missing = []
        
        for py_file in self.project_dir.rglob('*.py'):
            if 'test' in py_file.name or '__pycache__' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        docstring = ast.get_docstring(node)
                        if not docstring:
                            missing.append(f"{py_file.name}::{node.name}")
            except:
                pass
        
        return missing
    
    def cleanup(self):
        """Cleanup zasobów"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            time.sleep(1)
            if self.process.poll() is None:
                self.process.kill()
        
        if self.docker_client:
            try:
                subprocess.run(
                    ['docker-compose', 'down'],
                    cwd=self.project_dir,
                    capture_output=True
                )
            except:
                pass
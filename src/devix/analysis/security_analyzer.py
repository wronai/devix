#!/usr/bin/env python3
"""
Security Analyzer for Devix - Security vulnerability detection and analysis

This module provides comprehensive security analysis including:
- Static security analysis with bandit
- Sensitive data detection
- Dependency vulnerability scanning
- Security configuration checks
- Hardcoded credential detection
"""

import ast
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_analyzer import BaseAnalyzer


class SecurityAnalyzer(BaseAnalyzer):
    """Security analyzer for detecting vulnerabilities and security issues"""
    
    def __init__(self, project_path: str = "../", logger: Optional[logging.Logger] = None):
        super().__init__(project_path, logger)
        self.severity_threshold = "medium"
        self.credential_patterns = [
            r'(?i)(password|pwd)\s*[:=]\s*["\'][^"\']{8,}["\']',
            r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\'][^"\']{16,}["\']',
            r'(?i)(secret|token)\s*[:=]\s*["\'][^"\']{16,}["\']',
            r'(?i)(access[_-]?key|auth[_-]?token)\s*[:=]\s*["\'][^"\']{16,}["\']'
        ]
    
    def get_analyzer_name(self) -> str:
        return "Security Analyzer"
    
    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive security analysis"""
        self.logger.info("Starting security analysis")
        
        results = {
            "static_analysis": self._run_bandit_analysis(),
            "sensitive_data": self._check_sensitive_data(),
            "dependencies": self._check_dependency_security(),
            "configurations": self._check_security_configs(),
            "credentials": self._check_hardcoded_credentials(),
            "recommendations": self._generate_security_recommendations(),
            "summary": self._generate_security_summary()
        }
        
        self.logger.info("Security analysis completed")
        return results
        
    def _run_bandit_analysis(self) -> Dict[str, Any]:
        """Run bandit security analysis for Python files"""
        results = {
            "bandit_available": False,
            "issues": [],
            "summary": {"high": 0, "medium": 0, "low": 0}
        }
        
        # Check if bandit is available
        if not self._tool_available("bandit"):
            self.logger.warning("Bandit not available - skipping static security analysis")
            return results
            
        results["bandit_available"] = True
        
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
            
        try:
            # Run bandit analysis
            cmd = ["bandit", "-f", "json", "-r"] + [str(f) for f in python_files[:10]]
            proc_result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if proc_result.stdout:
                try:
                    bandit_data = json.loads(proc_result.stdout)
                    
                    for issue in bandit_data.get("results", []):
                        severity = issue.get("issue_severity", "unknown").lower()
                        confidence = issue.get("issue_confidence", "unknown").lower()
                        test_name = issue.get("test_name", "unknown")
                        filename = Path(issue.get("filename", "")).name
                        line_number = issue.get("line_number", 0)
                        issue_text = issue.get("issue_text", "")
                        
                        if self._should_report_security_issue(severity):
                            results["issues"].append({
                                "file": filename,
                                "line": line_number,
                                "severity": severity,
                                "confidence": confidence,
                                "test": test_name,
                                "message": issue_text
                            })
                            
                            # Update summary
                            if severity in results["summary"]:
                                results["summary"][severity] += 1
                                
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse bandit JSON output")
                    
        except subprocess.TimeoutExpired:
            self.logger.warning("Bandit analysis timed out")
        except Exception as e:
            self.logger.error(f"Bandit analysis failed: {e}")
            
        return results
        
    def _check_sensitive_data(self) -> Dict[str, Any]:
        """Check for sensitive data exposure in files"""
        results = {
            "issues": [],
            "patterns_checked": len(self.credential_patterns),
            "files_scanned": 0
        }
        
        sensitive_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded password'),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'hardcoded API key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'hardcoded secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'hardcoded token'),
            (r'aws[_-]?access[_-]?key', 'AWS access key'),
            (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', 'embedded private key')
        ]
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if (file_path.suffix in ['.py', '.js', '.ts', '.yaml', '.yml', '.json', '.env'] and
                    not self._should_ignore_file(file_path)):
                    
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore').lower()
                        results["files_scanned"] += 1
                        
                        for pattern, description in sensitive_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                results["issues"].append({
                                    "file": file_path.name,
                                    "type": description,
                                    "severity": "high"
                                })
                                break  # One issue per file is enough
                                
                    except Exception as e:
                        self.logger.debug(f"Error checking {file_path}: {e}")
                        
                if results["files_scanned"] >= 20:  # Limit scan
                    break
                    
        return results
        
    def _check_dependency_security(self) -> Dict[str, Any]:
        """Check dependency security vulnerabilities"""
        results = {
            "python": {"checked": False, "issues": []},
            "node": {"checked": False, "issues": []}
        }
        
        # Check Python dependencies
        req_file = Path(self.project_path) / "requirements.txt"
        if req_file.exists():
            results["python"] = self._check_python_dependencies()
            
        # Check Node.js dependencies
        package_file = Path(self.project_path) / "package.json"
        if package_file.exists():
            results["node"] = self._check_node_dependencies()
            
        return results
        
    def _check_python_dependencies(self) -> Dict[str, Any]:
        """Check Python dependency vulnerabilities using safety"""
        result = {"checked": True, "issues": [], "tool_available": False}
        
        if not self._tool_available("safety"):
            return result
            
        result["tool_available"] = True
        
        try:
            cmd = ["safety", "check", "--json"]
            proc_result = subprocess.run(
                cmd, 
                cwd=self.project_path,
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if proc_result.stdout:
                try:
                    safety_data = json.loads(proc_result.stdout)
                    for vuln in safety_data:
                        result["issues"].append({
                            "package": vuln.get("package", "unknown"),
                            "vulnerability": vuln.get("id", "unknown"),
                            "severity": "high"
                        })
                except json.JSONDecodeError:
                    if "vulnerabilities found" in proc_result.stdout:
                        result["issues"].append({
                            "package": "multiple",
                            "vulnerability": "parse_error",
                            "severity": "medium"
                        })
                        
        except subprocess.TimeoutExpired:
            self.logger.warning("Safety check timed out")
        except Exception as e:
            self.logger.debug(f"Safety check failed: {e}")
            
        return result
        
    def _check_node_dependencies(self) -> Dict[str, Any]:
        """Check Node.js dependency vulnerabilities using npm audit"""
        result = {"checked": True, "issues": [], "tool_available": False}
        
        if not self._tool_available("npm"):
            return result
            
        result["tool_available"] = True
        
        try:
            cmd = ["npm", "audit", "--json"]
            proc_result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if proc_result.stdout:
                try:
                    audit_data = json.loads(proc_result.stdout)
                    vulnerabilities = audit_data.get("vulnerabilities", {})
                    
                    for pkg, vuln_info in vulnerabilities.items():
                        severity = vuln_info.get("severity", "unknown")
                        if severity in ["high", "critical"]:
                            result["issues"].append({
                                "package": pkg,
                                "vulnerability": "npm_audit",
                                "severity": severity
                            })
                            
                except json.JSONDecodeError:
                    if "vulnerabilities" in proc_result.stdout:
                        result["issues"].append({
                            "package": "multiple",
                            "vulnerability": "parse_error", 
                            "severity": "medium"
                        })
                        
        except subprocess.TimeoutExpired:
            self.logger.warning("npm audit timed out")
        except Exception as e:
            self.logger.debug(f"npm audit failed: {e}")
            
        return result
        
    def _check_security_configs(self) -> Dict[str, Any]:
        """Check security configurations and settings"""
        results = {
            "issues": [],
            "files_checked": 0,
            "debug_mode_found": False,
            "dev_configs_found": False
        }
        
        config_files = [".env", ".env.example", "config.yaml", "config.json", "settings.py"]
        
        for config_file in config_files:
            config_path = Path(self.project_path) / config_file
            if config_path.exists():
                try:
                    content = config_path.read_text(encoding='utf-8', errors='ignore')
                    results["files_checked"] += 1
                    
                    # Check for debug mode
                    if re.search(r'debug\s*[:=]\s*true', content, re.IGNORECASE):
                        results["issues"].append({
                            "file": config_file,
                            "issue": "Debug mode enabled",
                            "severity": "medium"
                        })
                        results["debug_mode_found"] = True
                        
                    # Check for development settings
                    if "localhost" in content and "production" not in content.lower():
                        results["issues"].append({
                            "file": config_file,
                            "issue": "Development configuration detected",
                            "severity": "low"
                        })
                        results["dev_configs_found"] = True
                        
                except Exception as e:
                    self.logger.debug(f"Error checking {config_file}: {e}")
                    
        return results
        
    def _check_hardcoded_credentials(self) -> Dict[str, Any]:
        """Check for hardcoded credentials and secrets"""
        results = {
            "issues": [],
            "files_scanned": 0,
            "patterns_matched": 0
        }
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._should_ignore_file(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                if (file_path.suffix in ['.py', '.js', '.ts', '.yaml', '.yml', '.json'] and
                    not self._should_ignore_file(file_path)):
                    
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        results["files_scanned"] += 1
                        
                        for pattern in self.credential_patterns:
                            if re.search(pattern, content):
                                results["issues"].append({
                                    "file": file_path.name,
                                    "issue": "Potential hardcoded credentials",
                                    "severity": "high"
                                })
                                results["patterns_matched"] += 1
                                break  # One issue per file
                                
                    except Exception as e:
                        self.logger.debug(f"Error checking credentials in {file_path}: {e}")
                        
                if results["files_scanned"] >= 15:  # Limit scan
                    break
                    
        return results
        
    def _should_report_security_issue(self, severity: str) -> bool:
        """Check if security issue should be reported based on severity threshold"""
        severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        threshold_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        
        return (severity_levels.get(severity, 0) >= 
                threshold_levels.get(self.severity_threshold, 2))
                
    def _generate_security_recommendations(self) -> List[str]:
        """Generate security improvement recommendations"""
        recommendations = []
        
        # Check for available tools
        if not self._tool_available("bandit"):
            recommendations.append("Install bandit for Python security analysis")
            
        if not self._tool_available("safety"):
            recommendations.append("Install safety for Python dependency vulnerability scanning")
            
        # Check for security configurations
        security_files = ["bandit.yaml", ".bandit", "security.yaml", ".pre-commit-config.yaml"]
        has_security_config = any((Path(self.project_path) / f).exists() for f in security_files)
        
        if not has_security_config:
            recommendations.append("Add security configuration files (bandit.yaml, .pre-commit-config.yaml)")
            
        # Check for .env file
        env_file = Path(self.project_path) / ".env"
        if not env_file.exists():
            recommendations.append("Create .env file for environment variables")
            
        recommendations.append("Regularly update dependencies to patch security vulnerabilities")
        recommendations.append("Use secrets management instead of hardcoded credentials")
        recommendations.append("Enable debug mode only in development environments")
        
        return recommendations
        
    def _generate_security_summary(self) -> Dict[str, Any]:
        """Generate security analysis summary"""
        return {
            "bandit_available": self._tool_available("bandit"),
            "safety_available": self._tool_available("safety"),
            "npm_available": self._tool_available("npm"),
            "security_tools_count": sum([
                self._tool_available("bandit"),
                self._tool_available("safety"), 
                self._tool_available("npm")
            ]),
            "has_python_files": any(
                f.suffix == '.py' 
                for f in Path(self.project_path).rglob('*.py')
                if not self._should_ignore_file(f)
            ),
            "has_node_files": (Path(self.project_path) / "package.json").exists(),
            "severity_threshold": self.severity_threshold
        }
        
    def get_security_summary(self) -> Dict[str, Any]:
        """Get high-level security summary"""
        return {
            "tools_available": sum([
                self._tool_available("bandit"),
                self._tool_available("safety"),
                self._tool_available("npm")
            ]),
            "severity_threshold": self.severity_threshold,
            "recommendations_count": 5,  # Base recommendations
        }
    
    def _tool_available(self, tool_name: str) -> bool:
        """Check if a security analysis tool is available in the system"""
        try:
            result = subprocess.run(
                [tool_name, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

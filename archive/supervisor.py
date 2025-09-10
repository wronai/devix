#!/usr/bin/env python3
"""
devix Supervisor - Automatyczny system rozwoju i naprawy kodu
"""

import os
import sys
import time
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import json
import signal
import threading

# Dodaj ścieżkę projektu nadrzędnego do sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from devix.monitor import ApplicationMonitor
from devix.prompter import PromptGenerator
from devix.enhanced_prompter import EnhancedPromptGenerator
from devix.windsurf_controller import WindsurfController

# Import for HTTP server
import http.server
import socketserver

class devixSupervisor:
    """Główny supervisor automatycznego rozwoju"""
    
    def __init__(self, config_path: str = "devix/config.yaml"):
        self.project_dir = Path(__file__).parent.parent  # Główny folder projektu
        self.base_dir = self.project_dir 
        # Initialize logging before loading config to ensure logger is available
        self._setup_logging()
        self.config = self._load_config(config_path)
        self.iteration = 0
        self.max_iterations = self.config.get('max_iterations', 50)
        self.issues_history = []
        self.metrics_history = []
        self.running = True
        
        # Inicjalizacja komponentów
        self.monitor = ApplicationMonitor(self.project_dir, self.config)
        self.prompter = PromptGenerator(self.config)
        self.enhanced_prompter = EnhancedPromptGenerator(self.config, self.monitor)
        self.windsurf = WindsurfController(self.config)
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize HTTP server for health and metrics endpoints
        self._setup_http_server()
    
    def _setup_http_server(self):
        """Set up HTTP server for health and metrics endpoints."""
        health_endpoint = self.config.get('health_endpoint', 'http://localhost:8011/health')
        metrics_endpoint = self.config.get('metrics_endpoint', 'http://localhost:8011/metrics')
        
        # Extract port from health endpoint URL
        try:
            port_str = health_endpoint.split(':')[-1].split('/')[0]
            self.port = int(port_str)
        except (IndexError, ValueError):
            self.logger.error(f"Invalid health endpoint format: {health_endpoint}. Defaulting to port 8011.")
            self.port = 8011
        
        # Define a simple HTTP handler
        class EndpointHandler(http.server.BaseHTTPRequestHandler):
            def __init__(self, supervisor, *args, **kwargs):
                self.supervisor = supervisor
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {'status': 'OK', 'message': 'devix Supervisor is running'}
                    self.wfile.write(json.dumps(response).encode())
                elif self.path == '/metrics':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    metrics = self.supervisor.metrics_history[-1] if self.supervisor.metrics_history else {'total_tests': 0, 'passed_tests': 0, 'failed_tests': 0}
                    self.wfile.write(json.dumps(metrics).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'Not found')
        
        # Create HTTP server
        try:
            Handler = lambda *args, **kwargs: EndpointHandler(self, *args, **kwargs)
            self.http_server = socketserver.TCPServer(('', self.port), Handler)
            # Start server in a separate thread
            self.http_thread = threading.Thread(target=self.http_server.serve_forever)
            self.http_thread.daemon = True
            self.http_thread.start()
            self.logger.info(f"HTTP server started on port {self.port} for health and metrics endpoints")
        except Exception as e:
            self.logger.error(f"Failed to start HTTP server on port {self.port}: {e}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Wczytaj konfigurację"""
        config_file = self.project_dir / config_path
        if not config_file.exists():
            # Use logger if available, otherwise fallback to print
            if hasattr(self, "logger"):
                self.logger.warning(f"Config file {config_file} not found, using defaults")
            else:
                print(f"Config file {config_file} not found, using defaults")
            return self._get_default_config()
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Merge z domyślną konfiguracją
        default_config = self._get_default_config()
        default_config.update(config)
        return default_config
    
    def _get_default_config(self) -> Dict:
        """Domyślna konfiguracja"""
        return {
            'max_iterations': 50,
            'iteration_delay': 30,
            'test_coverage_threshold': 80,
            'code_quality_threshold': 8.0,
            'performance_threshold': 1000,  # ms
            'auto_continue': True,
            'monitor_interval': 10,
            'docker_compose_file': 'docker-compose.yml',
            'makefile_path': 'Makefile',
            'test_command': 'pytest',
            'run_command': 'python main.py',
            'log_level': 'INFO',
            'error_patterns': [
                'error', 'exception', 'failed', 'failure',
                'critical', 'fatal', 'traceback', 'crashed'
            ],
            'improvement_goals': {
                'add_logging': True,
                'add_tests': True,
                'add_error_handling': True,
                'add_documentation': True,
                'refactor_long_functions': True,
                'add_type_hints': True,
                'optimize_performance': True
            }
        }
    
    def _setup_logging(self):
        """Konfiguracja logowania"""
        log_dir = self.base_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'devix_{timestamp}.log'
        
        # Determine log level: if config is already loaded use its setting, otherwise default to INFO
        if hasattr(self, "config") and isinstance(self.config, dict):
            level_name = self.config.get('log_level', 'INFO')
        else:
            level_name = 'INFO'
        logging.basicConfig(
            level=getattr(logging, level_name),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"devix Supervisor started - Log: {log_file}")
    
    def _signal_handler(self, signum, frame):
        """Obsługa sygnałów systemowych"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def run(self):
        """Główna pętla supervisora - orchestrates the entire devix process"""
        self.logger.info(f"Starting devix Supervisor for project: {self.project_dir}")
        self.logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
        
        try:
            self._run_supervisor_loop()
        except KeyboardInterrupt:
            self.logger.info("Supervisor interrupted by user")
        except Exception as e:
            self.logger.error(f"Critical supervisor error: {e}", exc_info=True)
        finally:
            self._cleanup_and_report()
    
    def _run_supervisor_loop(self):
        """Execute the main supervisor iteration loop"""
        while self.running and self.iteration < self.max_iterations:
            try:
                self.iteration += 1
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"🔄 ITERATION {self.iteration}/{self.max_iterations}")
                self.logger.info(f"{'='*60}")
                
                # Execute monitoring and analysis
                issues, metrics = self._execute_monitoring_phase()
                
                # Determine if fixes are needed and apply them
                fix_result = self._execute_fix_phase(issues, metrics)
                
                # Check completion criteria
                if self._check_completion_criteria(issues, metrics, fix_result):
                    break
                
                # Wait before next iteration
                self._wait_for_next_iteration()
                
            except KeyboardInterrupt:
                self.logger.info("Iteration interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in iteration {self.iteration}: {str(e)}", exc_info=True)
                if not self._handle_error(e):
                    break
    
    def _execute_monitoring_phase(self) -> Tuple[List[str], Dict]:
        """Execute application monitoring and collect issues/metrics"""
        self.logger.info("📊 Starting monitoring phase...")
        
        try:
            issues, metrics = self.monitor.check_all()
            
            self.issues_history.append(issues)
            self.metrics_history.append(metrics)
            
            self.logger.info(f"Monitoring completed - Found {len(issues)} issues")
            self.logger.debug(f"Issues: {issues[:5]}{'...' if len(issues) > 5 else ''}")
            self.logger.info(f"Metrics collected: {list(metrics.keys())}")
            self.logger.debug(f"Metrics: {json.dumps(metrics, indent=2)}")
            
            return issues, metrics
            
        except Exception as e:
            self.logger.error(f"Monitoring phase failed: {e}", exc_info=True)
            return [], {}
    
    def _execute_fix_phase(self, issues: List[str], metrics: Dict) -> bool:
        """Execute fix generation and application phase"""
        needs_fix = self._needs_fixing(issues, metrics)
        
        if not needs_fix:
            self.logger.info("✅ No fixes needed - all checks passed!")
            return True
        
        self.logger.info("❌ Issues detected, starting fix phase...")
        
        try:
            # Generate and save enhanced fix prompts
            txt_content, md_content = self._generate_fix_prompt(issues, metrics)
            prompt_files = self._save_prompt(txt_content, md_content)
            
            # Apply the fix (use txt content for compatibility)
            success = self._apply_fix(txt_content, prompt_files['txt'])
            
            if success:
                self.logger.info("✅ Fix phase completed successfully")
            else:
                self.logger.error("❌ Fix phase failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Fix phase failed: {e}", exc_info=True)
            return False
    
    def _generate_fix_prompt(self, issues: List[str], metrics: Dict) -> Tuple[str, str]:
        """Generate comprehensive fix prompt based on issues and metrics - returns (txt_content, md_content)"""
        self.logger.debug("Generating enhanced fix prompts (.txt and .md)...")
        
        try:
            # Generate enhanced reports with both formats
            txt_content, md_content = self.enhanced_prompter.generate_reports(
                issues=issues,
                metrics=metrics,
                iteration=self.iteration,
                history=self.issues_history[-5:],  # Last 5 iterations
                output_dir=self.base_dir / 'logs'
            )
            
            # Also generate legacy format for backward compatibility
            legacy_prompt = self.prompter.generate(
                issues=issues,
                metrics=metrics,
                iteration=self.iteration,
                history=self.issues_history[-5:]
            )
            
            self.logger.info(f"Generated enhanced prompts - TXT: {len(txt_content)} chars, MD: {len(md_content)} chars")
            return txt_content, md_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate enhanced prompts: {e}", exc_info=True)
            # Fallback to legacy prompt generator
            self.logger.warning("Falling back to legacy prompt generator...")
            try:
                legacy_prompt = self.prompter.generate(
                    issues=issues,
                    metrics=metrics,
                    iteration=self.iteration,
                    history=self.issues_history[-5:]
                )
                return legacy_prompt, ""
            except Exception as fallback_e:
                self.logger.error(f"Legacy prompt generation also failed: {fallback_e}", exc_info=True)
                raise
    
    def _save_prompt(self, txt_content: str, md_content: str = "") -> Dict[str, Path]:
        """Save prompt to both .txt and .md files for debugging and review"""
        logs_dir = self.base_dir / 'logs'
        txt_file = logs_dir / f'prompt_{self.iteration}.txt'
        md_file = logs_dir / f'prompt_{self.iteration}.md'
        
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Save TXT file
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            self.logger.debug(f"TXT prompt saved to: {txt_file}")
            
            # Save MD file (if content provided)
            if md_content:
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                self.logger.debug(f"MD prompt saved to: {md_file}")
            
            result = {'txt': txt_file}
            if md_content:
                result['md'] = md_file
            
            self.logger.info(f"Enhanced prompts saved - TXT: {txt_file.name}, MD: {md_file.name if md_content else 'N/A'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to save prompts: {e}", exc_info=True)
            raise
    
    def _apply_fix(self, prompt: str, prompt_file: Path) -> bool:
        """Apply the generated fix via Windsurf or manual mode"""
        if self.config.get('auto_continue', True):
            return self._apply_automatic_fix(prompt)
        else:
            return self._apply_manual_fix(prompt_file)
    
    def _apply_automatic_fix(self, prompt: str) -> bool:
        """Apply fix automatically via Windsurf integration"""
        self.logger.info("📝 Sending prompt to Windsurf for automatic fix...")
        
        try:
            success = self.windsurf.send_prompt_and_continue(prompt)
            
            if success:
                delay = self.config.get('iteration_delay', 30)
                self.logger.info(f"✅ Fix applied successfully, waiting {delay}s for changes...")
                time.sleep(delay)
                return True
            else:
                self.logger.error("❌ Windsurf failed to apply fix")
                return self._handle_windsurf_failure()
                
        except Exception as e:
            self.logger.error(f"Automatic fix application failed: {e}", exc_info=True)
            return False
    
    def _apply_manual_fix(self, prompt_file: Path) -> bool:
        """Apply fix manually with user interaction"""
        self.logger.info(f"Manual mode - prompt saved to: {prompt_file}")
        self.logger.info("Please review and apply fixes manually...")
        
        try:
            input("Press Enter after applying fixes manually...")
            self.logger.info("Manual fix application completed")
            return True
        except KeyboardInterrupt:
            self.logger.info("Manual fix application cancelled")
            return False
    
    def _check_completion_criteria(self, issues: List[str], metrics: Dict, fix_result: bool) -> bool:
        """Check if supervisor should stop based on completion criteria"""
        if not fix_result and len(issues) == 0:
            # No issues but fix failed - might be goals achieved
            if self._goals_achieved(metrics):
                self.logger.info("🎉 All goals achieved! Stopping supervisor.")
                return True
            else:
                self.logger.info("📈 Goals not yet achieved, continuing improvements...")
        
        return False
    
    def _wait_for_next_iteration(self):
        """Wait appropriate delay before next iteration"""
        if self.iteration < self.max_iterations:
            delay = self.config.get('iteration_delay', 30)
            self.logger.info(f"⏳ Waiting {delay} seconds before next iteration...")
            time.sleep(delay)
    
    def _cleanup_and_report(self):
        """Execute final cleanup and reporting"""
        try:
            self._final_report()
            self.cleanup()
            self.logger.info("Supervisor cleanup completed successfully")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}", exc_info=True)
    
    def _needs_fixing(self, issues: List[str], metrics: Dict) -> bool:
        """Sprawdź czy potrzebna jest naprawa"""
        if issues:
            return True
        
        thresholds = {
            'test_coverage': self.config.get('test_coverage_threshold', 80),
            'code_quality': self.config.get('code_quality_threshold', 8.0),
            'performance': self.config.get('performance_threshold', 1000)
        }
        
        for metric, threshold in thresholds.items():
            if metric in metrics:
                if metric == 'performance':
                    if metrics[metric] > threshold:
                        self.logger.info(f"Performance {metrics[metric]}ms > {threshold}ms")
                        return True
                else:
                    if metrics[metric] < threshold:
                        self.logger.info(f"{metric}: {metrics[metric]} < {threshold}")
                        return True
        
        return False
    
    def _goals_achieved(self, metrics: Dict) -> bool:
        """Sprawdź czy osiągnięto wszystkie cele"""
        goals = {
            'test_coverage': self.config.get('test_coverage_threshold', 80),
            'code_quality': self.config.get('code_quality_threshold', 8.0),
            'performance': self.config.get('performance_threshold', 1000)
        }
        
        for goal, threshold in goals.items():
            if goal in metrics:
                if goal == 'performance':
                    if metrics[goal] > threshold:
                        return False
                else:
                    if metrics[goal] < threshold:
                        return False
        
        return True
    
    def _handle_windsurf_failure(self) -> bool:
        """Obsłuż błąd Windsurf"""
        retry_count = 3
        for i in range(retry_count):
            self.logger.info(f"Retrying Windsurf connection ({i+1}/{retry_count})...")
            time.sleep(5)
            if self.windsurf.test_connection():
                return True
        
        self.logger.error("Failed to connect to Windsurf after retries")
        return False
    
    def _handle_error(self, error: Exception) -> bool:
        """Obsłuż błąd w iteracji"""
        self.logger.error(f"Handling error: {str(error)}")
        
        # Jeśli to problem z projektem, spróbuj go naprawić
        if "ModuleNotFoundError" in str(error) or "ImportError" in str(error):
            self.logger.info("Detected import error, trying to fix dependencies...")
            subprocess.run(["pip", "install", "-r", "requirements.txt"], 
                         cwd=self.project_dir)
            return True
        
        # Inne błędy - kontynuuj
        return True
    
    def _final_report(self):
        """Generuj raport końcowy"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 FINAL REPORT")
        self.logger.info("="*60)
        
        report = {
            'total_iterations': self.iteration,
            'total_issues_found': sum(len(issues) for issues in self.issues_history),
            'final_metrics': self.metrics_history[-1] if self.metrics_history else {},
            'improvement': self._calculate_improvement()
        }
        
        report_file = self.base_dir / 'logs' / f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Report saved to: {report_file}")
        self.logger.info(json.dumps(report, indent=2))
    
    def _calculate_improvement(self) -> Dict:
        """Oblicz poprawę metryk"""
        if len(self.metrics_history) < 2:
            return {}
        
        first = self.metrics_history[0]
        last = self.metrics_history[-1]
        
        improvement = {}
        for key in first:
            if key in last and isinstance(first[key], (int, float)):
                improvement[key] = {
                    'start': first[key],
                    'end': last[key],
                    'change': last[key] - first[key],
                    'percent': ((last[key] - first[key]) / first[key] * 100) if first[key] != 0 else 0
                }
        
        return improvement
    
    def cleanup(self):
        """Cleanup przed zakończeniem"""
        self.logger.info("Cleaning up...")
        self.monitor.cleanup()
        self.windsurf.cleanup()
        if hasattr(self, 'http_server'):
            self.http_server.shutdown()
            self.http_thread.join()

def main():
    """Główna funkcja"""
    import argparse
    
    parser = argparse.ArgumentParser(description='devix Supervisor')
    parser.add_argument('--config', default='devix/config.yaml', help='Path to config file')
    parser.add_argument('--project', default='..', help='Path to project directory')
    parser.add_argument('--max-iterations', type=int, help='Override max iterations')
    parser.add_argument('--auto', action='store_true', help='Enable auto mode')
    
    args = parser.parse_args()
    
    # Zmień katalog roboczy na projekt
    if args.project:
        os.chdir(args.project)
    
    supervisor = devixSupervisor(args.config)
    
    # Override konfiguracji z linii poleceń
    if args.max_iterations:
        supervisor.max_iterations = args.max_iterations
    if args.auto:
        supervisor.config['auto_continue'] = True
    
    supervisor.run()

if __name__ == "__main__":
    main()
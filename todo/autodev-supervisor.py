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

from monitor import ApplicationMonitor
from prompter import PromptGenerator
from windsurf_controller import WindsurfController

class devixSupervisor:
    """Główny supervisor automatycznego rozwoju"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.base_dir = Path(__file__).parent
        self.project_dir = self.base_dir.parent  # Główny folder projektu
        self.config = self._load_config(config_path)
        self.iteration = 0
        self.max_iterations = self.config.get('max_iterations', 50)
        self.issues_history = []
        self.metrics_history = []
        self.running = True
        
        # Inicjalizacja komponentów
        self.monitor = ApplicationMonitor(self.project_dir, self.config)
        self.prompter = PromptGenerator(self.config)
        self.windsurf = WindsurfController(self.config)
        
        # Logging
        self._setup_logging()
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: str) -> Dict:
        """Wczytaj konfigurację"""
        config_file = self.base_dir / config_path
        if not config_file.exists():
            self.logger.warning(f"Config file {config_file} not found, using defaults")
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
        
        logging.basicConfig(
            level=getattr(logging, self.config.get('log_level', 'INFO')),
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
        """Główna pętla supervisora"""
        self.logger.info(f"Starting devix Supervisor for project: {self.project_dir}")
        self.logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
        
        while self.running and self.iteration < self.max_iterations:
            try:
                self.iteration += 1
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"🔄 ITERATION {self.iteration}/{self.max_iterations}")
                self.logger.info(f"{'='*60}")
                
                # 1. Monitoruj aplikację
                self.logger.info("📊 Monitoring application...")
                issues, metrics = self.monitor.check_all()
                
                self.issues_history.append(issues)
                self.metrics_history.append(metrics)
                
                # 2. Analizuj wyniki
                self.logger.info(f"Found {len(issues)} issues")
                self.logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")
                
                # 3. Sprawdź czy potrzebna naprawa
                needs_fix = self._needs_fixing(issues, metrics)
                
                if needs_fix:
                    self.logger.info("❌ Issues detected, generating fix...")
                    
                    # 4. Generuj prompt
                    prompt = self.prompter.generate(
                        issues=issues,
                        metrics=metrics,
                        iteration=self.iteration,
                        history=self.issues_history[-5:]  # Ostatnie 5 iteracji
                    )
                    
                    # 5. Zapisz prompt do pliku (dla debugowania)
                    prompt_file = self.base_dir / 'logs' / f'prompt_{self.iteration}.txt'
                    with open(prompt_file, 'w') as f:
                        f.write(prompt)
                    
                    # 6. Wyślij do Windsurf/Claude
                    if self.config.get('auto_continue', True):
                        self.logger.info("📝 Sending prompt to Windsurf...")
                        success = self.windsurf.send_prompt_and_continue(prompt)
                        
                        if success:
                            self.logger.info("✅ Fix applied, waiting for changes...")
                            time.sleep(self.config.get('iteration_delay', 30))
                        else:
                            self.logger.error("❌ Failed to apply fix")
                            if not self._handle_windsurf_failure():
                                break
                    else:
                        self.logger.info("Manual mode - prompt saved to: {prompt_file}")
                        input("Press Enter after applying fixes manually...")
                    
                else:
                    self.logger.info("✅ All checks passed!")
                    
                    # Sprawdź czy osiągnięto cele
                    if self._goals_achieved(metrics):
                        self.logger.info("🎉 All goals achieved! Stopping supervisor.")
                        break
                    else:
                        self.logger.info("📈 Goals not yet achieved, continuing improvements...")
                
                # 7. Pauza między iteracjami
                if self.iteration < self.max_iterations:
                    delay = self.config.get('iteration_delay', 30)
                    self.logger.info(f"⏳ Waiting {delay} seconds before next iteration...")
                    time.sleep(delay)
                
            except KeyboardInterrupt:
                self.logger.info("Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in iteration {self.iteration}: {str(e)}", exc_info=True)
                if not self._handle_error(e):
                    break
        
        self._final_report()
        self.cleanup()
    
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
        if self.windsurf:
            self.windsurf.cleanup()
        if self.jetbrains:
            self.jetbrains.cleanup()

def main():
    """Główna funkcja"""
    import argparse
    
    parser = argparse.ArgumentParser(description='devix Supervisor')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
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
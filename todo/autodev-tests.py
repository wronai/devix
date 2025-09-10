#!/usr/bin/env python3
"""
Testy jednostkowe dla devix
"""

# ===== devix/tests/test_monitor.py =====
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitor import ApplicationMonitor

class TestApplicationMonitor:
    """Testy dla ApplicationMonitor"""
    
    @pytest.fixture
    def monitor(self, tmp_path):
        """Fixture dla monitora"""
        config = {
            'test_coverage_threshold': 80,
            'code_quality_threshold': 8.0,
            'performance_threshold': 1000,
            'error_patterns': ['error', 'failed']
        }
        return ApplicationMonitor(tmp_path, config)
    
    def test_init(self, monitor):
        """Test inicjalizacji"""
        assert monitor is not None
        assert monitor.config['test_coverage_threshold'] == 80
    
    @patch('subprocess.run')
    def test_run_tests_success(self, mock_run, monitor, tmp_path):
        """Test uruchamiania testów - sukces"""
        # Mock subprocess result
        mock_run.return_value = Mock(
            returncode=0,
            stdout='All tests passed',
            stderr=''
        )
        
        # Create fake coverage.json
        coverage_data = {
            'totals': {'percent_covered': 85.5},
            'files': {}
        }
        coverage_file = tmp_path / 'coverage.json'
        with open(coverage_file, 'w') as f:
            json.dump(coverage_data, f)
        
        issues, metrics = monitor.run_tests()
        
        assert len(issues) == 0
        assert metrics['test_coverage'] == 85.5
    
    @patch('subprocess.run')
    def test_run_tests_failure(self, mock_run, monitor):
        """Test uruchamiania testów - błąd"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout='FAILED test_example.py::test_function - AssertionError',
            stderr='Error'
        )
        
        issues, metrics = monitor.run_tests()
        
        assert len(issues) > 0
        assert any('Test failed' in issue for issue in issues)
    
    @patch('subprocess.run')
    def test_check_code_quality(self, mock_run, monitor):
        """Test sprawdzania jakości kodu"""
        # Mock pylint output
        pylint_output = json.dumps([
            {
                'type': 'error',
                'path': 'test.py',
                'line': 10,
                'message': 'Undefined variable'
            }
        ])
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout=pylint_output,
            stderr=''
        )
        
        issues, metrics = monitor.check_code_quality()
        
        assert len(issues) > 0
        assert any('Code error' in issue for issue in issues)
    
    @patch('requests.get')
    def test_check_performance(self, mock_get, monitor):
        """Test sprawdzania wydajności"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        issues, metrics = monitor.check_performance()
        
        assert 'performance' in metrics
        assert metrics['performance'] >= 0
    
    def test_analyze_logs(self, monitor):
        """Test analizy logów"""
        monitor.logs_buffer = [
            'Starting application...',
            'ERROR: Database connection failed',
            'WARNING: Low memory',
            'Application crashed with exception'
        ]
        
        issues = monitor._analyze_logs()
        
        assert len(issues) > 0
        assert any('error' in issue.lower() for issue in issues)
    
    def test_detect_code_smells(self, monitor, tmp_path):
        """Test wykrywania code smells"""
        # Create test file with long function
        test_file = tmp_path / 'src' / 'test.py'
        test_file.parent.mkdir(exist_ok=True)
        
        with open(test_file, 'w') as f:
            f.write('''
def very_long_function():
    """ This is a very long function """
''' + '\n'.join(['    pass'] * 60))  # 60+ lines function
        
        issues = monitor._detect_code_smells()
        
        assert any('Long function' in issue for issue in issues)
    
    def test_check_security(self, monitor, tmp_path):
        """Test sprawdzania bezpieczeństwa"""
        # Create file with hardcoded secret
        test_file = tmp_path / 'src' / 'config.py'
        test_file.parent.mkdir(exist_ok=True)
        
        with open(test_file, 'w') as f:
            f.write('API_KEY = "hardcoded-secret-key-12345"')
        
        issues = monitor._check_hardcoded_secrets()
        
        assert len(issues) > 0
        assert any('API key' in issue for issue in issues)


# ===== devix/tests/test_prompter.py =====
class TestPromptGenerator:
    """Testy dla PromptGenerator"""
    
    @pytest.fixture
    def prompter(self):
        """Fixture dla promptera"""
        from prompter import PromptGenerator
        config = {
            'test_coverage_threshold': 80,
            'code_quality_threshold': 8.0,
            'improvement_goals': {
                'add_logging': True,
                'add_tests': True
            }
        }
        return PromptGenerator(config)
    
    def test_analyze_priorities(self, prompter):
        """Test analizy priorytetów"""
        issues = [
            'Application crashed',
            'Test failed: test_example',
            'Low test coverage: 60%'
        ]
        metrics = {
            'test_coverage': 60,
            'failed_tests': 2
        }
        
        priorities = prompter._analyze_priorities(issues, metrics)
        
        assert 'FIX_CRITICAL_ERRORS' in priorities
        assert 'FIX_FAILING_TESTS' in priorities
        assert 'INCREASE_TEST_COVERAGE' in priorities
    
    def test_generate_prompt(self, prompter):
        """Test generowania promptu"""
        issues = ['Test failed']
        metrics = {'test_coverage': 70}
        
        prompt = prompter.generate(
            issues=issues,
            metrics=metrics,
            iteration=1,
            history=[]
        )
        
        assert 'AUTOMATYCZNA KONTYNUACJA' in prompt
        assert 'NIE PYTAJ O POTWIERDZENIE' in prompt
        assert 'Test failed' in prompt
        assert '70%' in prompt
    
    def test_group_issues(self, prompter):
        """Test grupowania issues"""
        issues = [
            'Test failed: test_1',
            'Application crashed',
            'Missing docstring in function',
            'High memory usage: 800MB',
            'Security issue: hardcoded password'
        ]
        
        grouped = prompter._group_issues(issues)
        
        assert 'Błędy krytyczne' in grouped
        assert 'Testy' in grouped
        assert 'Dokumentacja' in grouped
        assert 'Wydajność' in grouped
        assert 'Bezpieczeństwo' in grouped


# ===== devix/tests/test_windsurf_controller.py =====
class TestWindsurfController:
    """Testy dla WindsurfController"""
    
    @pytest.fixture
    def controller(self):
        """Fixture dla kontrolera"""
        from windsurf_controller import WindsurfController
        config = {
            'use_windsurf_api': False,
            'use_gui_automation': False,
            'windsurf_path': 'windsurf'
        }
        return WindsurfController(config)
    
    @patch('subprocess.run')
    def test_send_via_cli(self, mock_run, controller, tmp_path):
        """Test wysyłania przez CLI"""
        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
        
        result = controller._send_via_cli('Test prompt')
        
        assert result == True
        mock_run.assert_called_once()
    
    @patch('requests.post')
    def test_send_via_api(self, mock_post, controller):
        """Test wysyłania przez API"""
        controller.use_api = True
        controller.api_key = 'test-key'
        
        mock_post.return_value = Mock(status_code=200)
        
        result = controller._send_via_api('Test prompt')
        
        assert result == True
        mock_post.assert_called_once()
    
    @patch('pyautogui.locateOnScreen')
    @patch('pyautogui.click')
    def test_gui_automation(self, mock_click, mock_locate, controller):
        """Test automatyzacji GUI"""
        mock_locate.return_value = (100, 100, 50, 50)
        
        # Utworz fake images
        controller.button_images = {
            'chat': Mock(exists=Mock(return_value=True)),
            'continue': Mock(exists=Mock(return_value=True))
        }
        
        result = controller._try_image_based_automation('Test prompt')
        
        # Sprawdź czy kliknięcia zostały wykonane
        assert mock_click.called


# ===== devix/tests/test_supervisor.py =====
class TestdevixSupervisor:
    """Testy dla głównego supervisora"""
    
    @pytest.fixture
    def supervisor(self, tmp_path):
        """Fixture dla supervisora"""
        from supervisor import devixSupervisor
        
        # Create config file
        config_file = tmp_path / 'config.yaml'
        config_file.write_text('''
max_iterations: 3
test_coverage_threshold: 80
auto_continue: false
        ''')
        
        with patch('supervisor.ApplicationMonitor'):
            with patch('supervisor.PromptGenerator'):
                with patch('supervisor.WindsurfController'):
                    return devixSupervisor(str(config_file))
    
    def test_init(self, supervisor):
        """Test inicjalizacji supervisora"""
        assert supervisor is not None
        assert supervisor.max_iterations == 3
        assert supervisor.iteration == 0
    
    def test_needs_fixing(self, supervisor):
        """Test sprawdzania czy potrzebna naprawa"""
        # Z issues
        assert supervisor._needs_fixing(['Error'], {}) == True
        
        # Bez issues ale niskie metryki
        assert supervisor._needs_fixing([], {'test_coverage': 50}) == True
        
        # Wszystko OK
        assert supervisor._needs_fixing([], {'test_coverage': 90}) == False
    
    def test_goals_achieved(self, supervisor):
        """Test sprawdzania osiągnięcia celów"""
        metrics = {
            'test_coverage': 85,
            'code_quality': 9.0,
            'performance': 500
        }
        
        assert supervisor._goals_achieved(metrics) == True
        
        metrics['test_coverage'] = 70
        assert supervisor._goals_achieved(metrics) == False
    
    @patch('time.sleep')
    def test_run_loop(self, mock_sleep, supervisor):
        """Test głównej pętli"""
        # Mock monitor results
        supervisor.monitor.check_all = Mock(
            side_effect=[
                (['Error'], {'test_coverage': 60}),  # Iteration 1 - issues
                ([], {'test_coverage': 85}),          # Iteration 2 - fixed
            ]
        )
        
        # Mock prompter
        supervisor.prompter.generate = Mock(return_value='Fix prompt')
        
        # Mock windsurf
        supervisor.windsurf.send_prompt_and_continue = Mock(return_value=True)
        
        # Ustaw max 2 iteracje
        supervisor.max_iterations = 2
        
        # Uruchom
        supervisor.run()
        
        # Sprawdź czy wywołano odpowiednie metody
        assert supervisor.monitor.check_all.call_count == 2
        assert supervisor.prompter.generate.called
        assert supervisor.windsurf.send_prompt_and_continue.called


# ===== devix/tests/test_integration.py =====
class TestIntegration:
    """Testy integracyjne"""
    
    @pytest.fixture
    def setup_project(self, tmp_path):
        """Przygotuj testowy projekt"""
        # Struktura projektu
        (tmp_path / 'src').mkdir()
        (tmp_path / 'tests').mkdir()
        (tmp_path / 'devix').mkdir()
        
        # Przykładowy kod z błędem
        main_file = tmp_path / 'src' / 'main.py'
        main_file.write_text('''
def calculate(x, y):
    return x / y  # Potential ZeroDivisionError

def main():
    result = calculate(10, 0)
    print(result)

if __name__ == "__main__":
    main()
        ''')
        
        # Test który failuje
        test_file = tmp_path / 'tests' / 'test_main.py'
        test_file.write_text('''
from src.main import calculate

def test_calculate():
    assert calculate(10, 2) == 5
    
def test_calculate_zero():
    # This will fail
    assert calculate(10, 0) == 0
        ''')
        
        # Requirements
        req_file = tmp_path / 'requirements.txt'
        req_file.write_text('pytest\npytest-cov\n')
        
        return tmp_path
    
    @patch('windsurf_controller.WindsurfController.send_prompt_and_continue')
    def test_full_workflow(self, mock_windsurf, setup_project):
        """Test pełnego workflow"""
        from supervisor import devixSupervisor
        from monitor import ApplicationMonitor
        from prompter import PromptGenerator
        
        # Konfiguracja
        config = {
            'max_iterations': 2,
            'test_coverage_threshold': 80,
            'auto_continue': True
        }
        
        # Monitor
        monitor = ApplicationMonitor(setup_project, config)
        issues, metrics = monitor.check_all()
        
        # Powinny być issues
        assert len(issues) > 0
        
        # Prompter
        prompter = PromptGenerator(config)
        prompt = prompter.generate(issues, metrics, 1)
        
        # Prompt powinien zawierać issues
        assert any(issue in prompt for issue in issues)
        
        # Mock windsurf response
        mock_windsurf.return_value = True
        
        # Supervisor
        with patch('supervisor.ApplicationMonitor', return_value=monitor):
            with patch('supervisor.PromptGenerator', return_value=prompter):
                supervisor = devixSupervisor()
                supervisor.max_iterations = 1
                
                # Jedna iteracja
                supervisor.run()
                
                # Sprawdź czy prompt został wysłany
                assert mock_windsurf.called


# ===== devix/tests/conftest.py =====
"""
Pytest configuration for devix tests
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(autouse=True)
def reset_modules():
    """Reset imported modules between tests"""
    yield
    # Cleanup
    modules_to_remove = [m for m in sys.modules if 'devix' in m]
    for module in modules_to_remove:
        del sys.modules[module]

@pytest.fixture
def mock_config():
    """Standard test configuration"""
    return {
        'max_iterations': 5,
        'iteration_delay': 1,
        'test_coverage_threshold': 80,
        'code_quality_threshold': 8.0,
        'performance_threshold': 1000,
        'auto_continue': False,
        'error_patterns': ['error', 'failed', 'exception'],
        'improvement_goals': {
            'add_logging': True,
            'add_tests': True,
            'add_error_handling': True
        }
    }

# Disable GUI features in tests
import os
os.environ['DISPLAY'] = ':99'
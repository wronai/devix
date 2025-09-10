#!/usr/bin/env python3
"""
Testy jednostkowe dla JetBrains Controller
"""

# ===== devix/tests/test_jetbrains_controller.py =====

import pytest
import sys
import platform
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent.parent))

from jetbrains_controller import (
    JetBrainsController, 
    PyCharmPlugin, 
    IntelliJPlugin, 
    WebStormPlugin,
    get_jetbrains_controller
)


class TestJetBrainsController:
    """Testy dla głównego kontrolera JetBrains"""
    
    @pytest.fixture
    def controller(self):
        """Fixture dla kontrolera"""
        config = {
            'jetbrains_ide': 'pycharm',
            'jetbrains_http_port': 63342,
            'jetbrains_gateway_port': 63343,
            'jetbrains_ai_assistant': False
        }
        with patch('jetbrains_controller.psutil.process_iter'):
            return JetBrainsController(config)
    
    def test_init(self, controller):
        """Test inicjalizacji"""
        assert controller is not None
        assert controller.http_port == 63342
        assert controller.gateway_port == 63343
    
    @patch('jetbrains_controller.psutil.process_iter')
    def test_detect_ide_type(self, mock_process_iter):
        """Test wykrywania typu IDE"""
        # Mock procesu PyCharm
        mock_proc = Mock()
        mock_proc.info = {'name': 'pycharm64.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        controller = JetBrainsController({})
        assert controller._detect_ide_type() == 'pycharm'
    
    @patch('jetbrains_controller.Path.exists')
    @patch('jetbrains_controller.platform.system')
    def test_find_ide_path_mac(self, mock_system, mock_exists):
        """Test znajdowania ścieżki IDE na macOS"""
        mock_system.return_value = 'Darwin'
        mock_exists.return_value = True
        
        controller = JetBrainsController({'jetbrains_ide': 'pycharm'})
        ide_path = controller._find_ide_path()
        
        assert ide_path is not None
        assert 'PyCharm' in str(ide_path)
    
    @patch('jetbrains_controller.Path.exists')
    @patch('jetbrains_controller.platform.system')
    def test_find_ide_path_windows(self, mock_system, mock_exists):
        """Test znajdowania ścieżki IDE na Windows"""
        mock_system.return_value = 'Windows'
        mock_exists.return_value = True
        
        controller = JetBrainsController({'jetbrains_ide': 'pycharm'})
        ide_path = controller._find_ide_path()
        
        assert ide_path is not None
        assert 'pycharm' in str(ide_path).lower()
    
    @patch('jetbrains_controller.requests.get')
    @patch('jetbrains_controller.requests.post')
    def test_send_via_http_api_success(self, mock_post, mock_get, controller):
        """Test wysyłania przez HTTP API - sukces"""
        # Mock successful API check
        mock_get.return_value = Mock(status_code=200)
        mock_post.return_value = Mock(status_code=200)
        
        result = controller._send_via_http_api('test content', 'fix')
        
        assert result == True
        mock_get.assert_called_once()
        mock_post.assert_called_once()
    
    @patch('jetbrains_controller.requests.get')
    def test_send_via_http_api_failure(self, mock_get, controller):
        """Test wysyłania przez HTTP API - błąd"""
        # Mock API not available
        mock_get.side_effect = Exception("Connection refused")
        
        result = controller._send_via_http_api('test content', 'fix')
        
        assert result == False
    
    @patch('jetbrains_controller.subprocess.run')
    def test_send_via_command_line(self, mock_run, controller):
        """Test wysyłania przez linię poleceń"""
        controller.ide_path = Path('/usr/bin/pycharm')
        mock_run.return_value = Mock(returncode=0)
        
        with patch('builtins.open', mock_open()):
            result = controller._send_via_command_line('test content', 'open')
        
        assert result == True
        mock_run.assert_called_once()
    
    @patch('jetbrains_controller.pyautogui.getWindowsWithTitle')
    def test_focus_ide_window(self, mock_get_windows, controller):
        """Test ustawiania fokusu na oknie IDE"""
        mock_window = Mock()
        mock_window.activate = Mock()
        mock_get_windows.return_value = [mock_window]
        
        result = controller._focus_ide_window()
        
        assert result == True
        mock_window.activate.assert_called_once()
    
    def test_create_external_tool_config(self, controller):
        """Test tworzenia konfiguracji External Tool"""
        config = controller._create_external_tool_config('test')
        
        assert '<?xml version' in config
        assert 'devix test' in config
        assert 'python' in config
    
    def test_create_file_watcher_config(self, controller):
        """Test tworzenia konfiguracji File Watcher"""
        config = controller._create_file_watcher_config('analyze')
        
        assert '<?xml version' in config
        assert 'devix analyze' in config
        assert 'devix' in config
    
    @patch('jetbrains_controller.Path.exists')
    def test_find_project_file(self, mock_exists, controller):
        """Test znajdowania pliku projektu"""
        mock_exists.return_value = True
        
        project_file = controller._find_project_file()
        
        assert project_file is not None
    
    @patch('builtins.open', new_callable=mock_open, read_data='<xml></xml>')
    @patch('jetbrains_controller.Path.exists')
    def test_get_recent_files(self, mock_exists, mock_file, controller):
        """Test pobierania ostatnio otwartych plików"""
        mock_exists.return_value = True
        controller.jetbrains_config_dir = Path('/mock/config')
        
        recent = controller._get_recent_files()
        
        assert isinstance(recent, list)
    
    @patch('jetbrains_controller.subprocess.run')
    def test_run_inspection(self, mock_run, controller):
        """Test uruchamiania inspekcji"""
        controller.ide_path = Path('/usr/bin/pycharm')
        mock_run.return_value = Mock(returncode=0)
        
        # Mock inspection results file
        with patch('jetbrains_controller.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='<xml><problem severity="ERROR"/></xml>')):
                results = controller.run_inspection()
        
        assert isinstance(results, dict)
    
    @patch('jetbrains_controller.pyautogui.hotkey')
    @patch('jetbrains_controller.pyautogui.press')
    @patch('jetbrains_controller.subprocess.run')
    def test_apply_quick_fixes(self, mock_run, mock_press, mock_hotkey, controller):
        """Test aplikowania quick fixes"""
        controller.ide_path = Path('/usr/bin/pycharm')
        
        fixes = [
            {'file': 'test.py', 'line': 10, 'type': 'import'}
        ]
        
        result = controller.apply_quick_fixes(fixes)
        
        assert result == True
        mock_hotkey.assert_called()


class TestPyCharmPlugin:
    """Testy dla PyCharm plugin"""
    
    @pytest.fixture
    def plugin(self):
        """Fixture dla PyCharm plugin"""
        config = {'jetbrains_ide': 'pycharm'}
        with patch('jetbrains_controller.psutil.process_iter'):
            return PyCharmPlugin(config)
    
    def test_init(self, plugin):
        """Test inicjalizacji"""
        assert plugin.ide_type == 'pycharm'
    
    @patch('jetbrains_controller.subprocess.run')
    def test_run_pytest(self, mock_run, plugin):
        """Test uruchamiania pytest"""
        plugin.ide_path = Path('/usr/bin/pycharm')
        mock_run.return_value = Mock(
            returncode=0,
            stdout='All tests passed'
        )
        
        result = plugin.run_pytest('tests/')
        
        assert result['passed'] == True
        assert 'All tests passed' in result['output']
    
    @patch('jetbrains_controller.pyautogui.hotkey')
    def test_profile_code(self, mock_hotkey, plugin):
        """Test profilowania kodu"""
        result = plugin.profile_code()
        
        assert result['status'] == 'profiling_started'
        mock_hotkey.assert_called()


class TestIntelliJPlugin:
    """Testy dla IntelliJ plugin"""
    
    @pytest.fixture
    def plugin(self):
        """Fixture dla IntelliJ plugin"""
        config = {'jetbrains_ide': 'intellij'}
        with patch('jetbrains_controller.psutil.process_iter'):
            return IntelliJPlugin(config)
    
    def test_init(self, plugin):
        """Test inicjalizacji"""
        assert plugin.ide_type == 'intellij'
    
    @patch('jetbrains_controller.subprocess.run')
    def test_run_maven(self, mock_run, plugin):
        """Test uruchamiania Maven"""
        plugin.ide_path = Path('/usr/bin/idea')
        mock_run.return_value = Mock(
            returncode=0,
            stdout='BUILD SUCCESS'
        )
        
        result = plugin.run_maven('test')
        
        assert result['success'] == True
        assert 'BUILD SUCCESS' in result['output']


class TestWebStormPlugin:
    """Testy dla WebStorm plugin"""
    
    @pytest.fixture
    def plugin(self):
        """Fixture dla WebStorm plugin"""
        config = {'jetbrains_ide': 'webstorm'}
        with patch('jetbrains_controller.psutil.process_iter'):
            return WebStormPlugin(config)
    
    def test_init(self, plugin):
        """Test inicjalizacji"""
        assert plugin.ide_type == 'webstorm'
    
    @patch('jetbrains_controller.subprocess.run')
    def test_run_npm_script(self, mock_run, plugin):
        """Test uruchamiania npm script"""
        plugin.ide_path = Path('/usr/bin/webstorm')
        mock_run.return_value = Mock(
            returncode=0,
            stdout='Test suite passed'
        )
        
        result = plugin.run_npm_script('test')
        
        assert result['success'] == True
        assert 'Test suite passed' in result['output']


class TestFactoryFunction:
    """Testy dla factory function"""
    
    @patch('jetbrains_controller.psutil.process_iter')
    def test_get_jetbrains_controller_auto(self, mock_process_iter):
        """Test auto-detection"""
        mock_proc = Mock()
        mock_proc.info = {'name': 'pycharm'}
        mock_process_iter.return_value = [mock_proc]
        
        controller = get_jetbrains_controller({'jetbrains_ide': 'auto'})
        
        assert isinstance(controller, PyCharmPlugin)
    
    @patch('jetbrains_controller.psutil.process_iter')
    def test_get_jetbrains_controller_specific(self, mock_process_iter):
        """Test specific IDE"""
        controller = get_jetbrains_controller({'jetbrains_ide': 'intellij'})
        
        assert isinstance(controller, IntelliJPlugin)


class TestIntegrationScenarios:
    """Testy scenariuszy integracyjnych"""
    
    @pytest.fixture
    def full_config(self):
        """Pełna konfiguracja"""
        return {
            'jetbrains_ide': 'pycharm',
            'jetbrains_http_port': 63342,
            'jetbrains_ai_assistant': True,
            'use_inspections': True,
            'use_quick_fixes': True,
            'sync_on_save': True
        }
    
    @patch('jetbrains_controller.requests.post')
    @patch('jetbrains_controller.requests.get')
    @patch('jetbrains_controller.psutil.process_iter')
    def test_full_workflow(self, mock_process_iter, mock_get, mock_post, full_config):
        """Test pełnego workflow"""
        # Setup
        mock_proc = Mock()
        mock_proc.info = {'name': 'pycharm'}
        mock_process_iter.return_value = [mock_proc]
        
        mock_get.return_value = Mock(status_code=200)
        mock_post.return_value = Mock(status_code=200)
        
        # Create controller
        controller = get_jetbrains_controller(full_config)
        
        # Test sending content
        success = controller.send_to_ide('Fix this code', 'fix')
        assert success == True
        
        # Test inspection
        with patch('builtins.open', mock_open(read_data='<xml><problem/></xml>')):
            with patch('jetbrains_controller.Path.exists', return_value=True):
                with patch('jetbrains_controller.subprocess.run', return_value=Mock(returncode=0)):
                    results = controller.run_inspection()
                    assert isinstance(results, dict)
    
    @patch('jetbrains_controller.watchdog.observers.Observer')
    @patch('jetbrains_controller.psutil.process_iter')
    def test_file_sync_setup(self, mock_process_iter, mock_observer, full_config):
        """Test konfiguracji synchronizacji plików"""
        mock_process_iter.return_value = []
        
        controller = JetBrainsController(full_config)
        
        # Mock watchdog
        mock_observer_instance = Mock()
        mock_observer.return_value = mock_observer_instance
        
        controller._setup_file_sync()
        
        assert controller.file_watcher is not None


# ===== devix/tests/test_jetbrains_integration.py =====
"""
Testy integracyjne dla JetBrains z resztą systemu
"""

class TestJetBrainsWithSupervisor:
    """Testy integracji z Supervisorem"""
    
    @pytest.fixture
    def supervisor_with_jetbrains(self, tmp_path):
        """Supervisor z JetBrains"""
        from supervisor import devixSupervisor
        
        config_file = tmp_path / 'config.yaml'
        config_file.write_text('''
ide_type: jetbrains
jetbrains_integration:
  jetbrains_ide: pycharm
max_iterations: 2
auto_continue: true
        ''')
        
        with patch('supervisor.ApplicationMonitor'):
            with patch('supervisor.PromptGenerator'):
                with patch('supervisor.get_jetbrains_controller'):
                    return devixSupervisor(str(config_file))
    
    def test_supervisor_uses_jetbrains(self, supervisor_with_jetbrains):
        """Test że supervisor używa JetBrains"""
        assert supervisor_with_jetbrains.jetbrains is not None
        assert supervisor_with_jetbrains.windsurf is None
    
    @patch('time.sleep')
    def test_supervisor_sends_to_jetbrains(self, mock_sleep, supervisor_with_jetbrains):
        """Test wysyłania do JetBrains przez supervisor"""
        # Mock monitor results
        supervisor_with_jetbrains.monitor.check_all = Mock(
            return_value=(['Error'], {'test_coverage': 60})
        )
        
        # Mock prompter
        supervisor_with_jetbrains.prompter.generate = Mock(
            return_value='Fix this error'
        )
        
        # Mock JetBrains controller
        supervisor_with_jetbrains.jetbrains.send_to_ide = Mock(return_value=True)
        supervisor_with_jetbrains.jetbrains.run_inspection = Mock(
            return_value={'errors': []}
        )
        
        # Run one iteration
        supervisor_with_jetbrains.max_iterations = 1
        supervisor_with_jetbrains.run()
        
        # Verify JetBrains was called
        supervisor_with_jetbrains.jetbrains.send_to_ide.assert_called()
        supervisor_with_jetbrains.jetbrains.run_inspection.assert_called()


class TestJetBrainsWithMonitor:
    """Testy integracji z Monitorem"""
    
    @patch('subprocess.run')
    @patch('jetbrains_controller.psutil.process_iter')
    def test_monitor_triggers_jetbrains_inspection(self, mock_process_iter, mock_run):
        """Test że monitor może triggerować inspekcję JetBrains"""
        from monitor import ApplicationMonitor
        from jetbrains_controller import PyCharmPlugin
        
        mock_process_iter.return_value = []
        
        # Create monitor
        monitor = ApplicationMonitor(Path.cwd(), {})
        
        # Create JetBrains controller
        jetbrains = PyCharmPlugin({})
        jetbrains.ide_path = Path('/usr/bin/pycharm')
        
        # Mock subprocess for inspection
        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
        
        # Run inspection through JetBrains
        with patch('builtins.open', mock_open(read_data='<xml></xml>')):
            with patch('jetbrains_controller.Path.exists', return_value=True):
                results = jetbrains.run_inspection()
        
        assert isinstance(results, dict)
        mock_run.assert_called()


# ===== devix/tests/conftest_jetbrains.py =====
"""
Pytest configuration dla testów JetBrains
"""

import pytest
import os

@pytest.fixture(autouse=True)
def mock_jetbrains_env():
    """Mock environment dla testów JetBrains"""
    os.environ['JETBRAINS_TEST_MODE'] = '1'
    yield
    del os.environ['JETBRAINS_TEST_MODE']

@pytest.fixture
def mock_ide_running():
    """Mock running IDE process"""
    import psutil
    from unittest.mock import Mock
    
    mock_proc = Mock()
    mock_proc.info = {'name': 'pycharm64.exe'}
    mock_proc.cpu_percent = Mock(return_value=5.0)
    
    with patch('psutil.process_iter', return_value=[mock_proc]):
        yield mock_proc
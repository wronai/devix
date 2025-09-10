#!/usr/bin/env python3
"""
Windsurf Controller - Integracja z Windsurf/Claude
"""

import time
import subprocess
import logging
import json
import os
from pathlib import Path
from typing import Dict, Optional

# Attempt to import pyautogui and related GUI automation libraries.
# In headless environments (e.g., CI, Docker without X server) these imports may fail.
# We handle failures gracefully by setting a fallback flag.
_GUI_AVAILABLE = False
try:
    import pyautogui
    import pyperclip
    # The following line can raise DisplayConnectionError if DISPLAY is not set
    pyautogui.size() 
    _GUI_AVAILABLE = True
except Exception as e:  # Catch broad exceptions including DisplayConnectionError
    # Log the issue at import time; actual logger will be configured later.
    logging.getLogger(__name__).warning(
        f"GUI automation libraries not available: {e}. "
        "WindsurfController will operate in non-GUI mode."
    )

class WindsurfController:
    """Kontroler do automatycznej interakcji z Windsurf"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.windsurf_path = config.get('windsurf_path', 'windsurf')
        self.use_api = config.get('use_windsurf_api', False)
        # If GUI libraries are unavailable, force automation off regardless of config.
        self.use_automation = config.get('use_gui_automation', True) and _GUI_AVAILABLE
        self.api_key = os.getenv('WINDSURF_API_KEY')
        
        # Konfiguracja PyAutoGUI – only if available.
        if _GUI_AVAILABLE:
            pyautogui.PAUSE = 0.5
            pyautogui.FAILSAFE = True
        
        # Obrazy przycisków (opcjonalne)
        self.button_images = {
            'continue': Path(__file__).parent / 'images' / 'continue_button.png',
            'submit': Path(__file__).parent / 'images' / 'submit_button.png',
            'chat': Path(__file__).parent / 'images' / 'chat_area.png'
        }
    
    def send_prompt_and_continue(self, prompt: str) -> bool:
        """Wyślij prompt do Windsurf i automatycznie kontynuuj"""
        try:
            if self.use_api and self.api_key:
                return self._send_via_api(prompt)
            elif self.use_automation:
                return self._send_via_gui_automation(prompt)
            else:
                return self._send_via_cli(prompt)
        except Exception as e:
            self.logger.error(f"Failed to send prompt: {e}", exc_info=True)
            return False
    
    def _send_via_api(self, prompt: str) -> bool:
        """Wyślij przez API Windsurf (jeśli dostępne)"""
        try:
            import requests
            
            # Przykładowe API - dostosuj do rzeczywistego
            api_url = self.config.get('windsurf_api_url', 'http://localhost:8091/api')
            
            response = requests.post(
                f"{api_url}/continue",
                json={
                    'prompt': prompt,
                    'auto_continue': True,
                    'max_iterations': 5
                },
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info("Prompt sent via API successfully")
                return True
            else:
                self.logger.error(f"API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"API error: {e}")
            return False
    
    def _send_via_gui_automation(self, prompt: str) -> bool:
        """Wyślij przez automatyzację GUI"""
        if not _GUI_AVAILABLE:
            self.logger.debug("GUI automation libraries unavailable; skipping GUI path.")
            return False
        try:
            self.logger.info("Using GUI automation to send prompt")
            
            # Metoda 1: Szukanie obrazu przycisku
            if self._try_image_based_automation(prompt):
                return True
            
            # Metoda 2: Skróty klawiszowe
            if self._try_keyboard_shortcuts(prompt):
                return True
            
            # Metoda 3: Współrzędne bezwzględne
            if self._try_coordinate_based_automation(prompt):
                return True
            
            self.logger.warning("All GUI automation methods failed")
            return False
            
        except Exception as e:
            self.logger.error(f"GUI automation error: {e}")
            return False
    
    def _try_image_based_automation(self, prompt: str) -> bool:
        """Próba automatyzacji bazującej na obrazach"""
        try:
            # Znajdź obszar czatu
            if self.button_images['chat'].exists():
                chat_location = pyautogui.locateOnScreen(
                    str(self.button_images['chat']),
                    confidence=0.8
                )
                
                if chat_location:
                    # Kliknij w obszar czatu
                    pyautogui.click(chat_location)
                    time.sleep(0.5)
                    
                    # Wyczyść i wpisz nowy prompt
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.2)
                    
                    # Użyj schowka dla długich tekstów
                    pyperclip.copy(prompt)
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(0.5)
                    
                    # Znajdź i kliknij continue
                    if self.button_images['continue'].exists():
                        continue_button = pyautogui.locateOnScreen(
                            str(self.button_images['continue']),
                            confidence=0.8
                        )
                        if continue_button:
                            pyautogui.click(continue_button)
                            self.logger.info("Prompt sent via image recognition")
                            return True
            
        except Exception as e:
            self.logger.debug(f"Image-based automation failed: {e}")
        
        return False
    
    def _try_keyboard_shortcuts(self, prompt: str) -> bool:
        """Próba użycia skrótów klawiszowych"""
        try:
            # Fokus na Windsurf (Alt+Tab lub specyficzny skrót)
            self._focus_windsurf_window()
            time.sleep(1)
            
            # Otwórz chat/prompt (różne kombinacje)
            shortcuts_to_try = [
                ['ctrl', 'shift', 'p'],  # Command palette
                ['ctrl', 'shift', 'c'],  # Continue
                ['ctrl', 'k'],           # Quick chat
                ['alt', 'c'],            # Alternative chat
            ]
            
            for shortcut in shortcuts_to_try:
                pyautogui.hotkey(*shortcut)
                time.sleep(0.5)
                
                # Sprawdź czy się otworzyło (wpisz test)
                pyautogui.typewrite("test", interval=0.01)
                time.sleep(0.2)
                
                # Jeśli się wpisało, wyczyść i wpisz prawdziwy prompt
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                
                # Wklej prompt
                pyperclip.copy(prompt)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)
                
                # Enter lub Ctrl+Enter żeby wysłać
                pyautogui.hotkey('ctrl', 'enter')
                time.sleep(0.5)
                
                # Sprawdź czy zadziałało
                if self._check_if_processing():
                    self.logger.info(f"Prompt sent via keyboard shortcut: {shortcut}")
                    return True
            
        except Exception as e:
            self.logger.debug(f"Keyboard shortcuts failed: {e}")
        
        return False
    
    def _try_coordinate_based_automation(self, prompt: str) -> bool:
        """Próba automatyzacji bazującej na współrzędnych"""
        try:
            # Pobierz zapisane współrzędne lub użyj domyślnych
            coords = self._get_saved_coordinates()
            
            if coords:
                # Kliknij w obszar czatu
                pyautogui.click(coords['chat_x'], coords['chat_y'])
                time.sleep(0.5)
                
                # Wyczyść
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                
                # Wklej prompt
                pyperclip.copy(prompt)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)
                
                # Kliknij continue
                pyautogui.click(coords['continue_x'], coords['continue_y'])
                
                self.logger.info("Prompt sent via coordinates")
                return True
            
        except Exception as e:
            self.logger.debug(f"Coordinate-based automation failed: {e}")
        
        return False
    
    def _send_via_cli(self, prompt: str) -> bool:
        """Wyślij przez CLI Windsurf (jeśli dostępne)"""
        try:
            # Zapisz prompt do pliku
            prompt_file = Path('/tmp/windsurf_prompt.txt')
            with open(prompt_file, 'w') as f:
                f.write(prompt)
            
            # Wywołaj Windsurf CLI
            result = subprocess.run(
                [self.windsurf_path, 'continue', '--prompt-file', str(prompt_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info("Prompt sent via CLI successfully")
                return True
            else:
                self.logger.error(f"CLI error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.logger.error("Windsurf CLI not found")
            return False
        except Exception as e:
            self.logger.error(f"CLI error: {e}")
            return False
    
    def _focus_windsurf_window(self):
        """Ustaw fokus na oknie Windsurf"""
        try:
            # Metoda 1: Przez nazwę okna
            windows = pyautogui.getWindowsWithTitle('Windsurf')
            if windows:
                windows[0].activate()
                return
            
            # Metoda 2: Przez VS Code
            windows = pyautogui.getWindowsWithTitle('Visual Studio Code')
            if windows:
                windows[0].activate()
                return
            
            # Metoda 3: Alt+Tab
            pyautogui.keyDown('alt')
            pyautogui.press('tab')
            time.sleep(0.5)
            pyautogui.keyUp('alt')
            
        except Exception as e:
            self.logger.debug(f"Could not focus window: {e}")
    
    def _check_if_processing(self) -> bool:
        """Sprawdź czy Windsurf przetwarza prompt"""
        # Heurystyka - sprawdź czy CPU wzrosło, lub poszukaj wskaźnika
        try:
            import psutil
            
            # Sprawdź procesy
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                if 'windsurf' in proc.info['name'].lower() or 'code' in proc.info['name'].lower():
                    if proc.info['cpu_percent'] > 10:
                        return True
            
        except:
            pass
        
        # Zakładamy że działa
        return True
    
    def _get_saved_coordinates(self) -> Optional[Dict]:
        """Pobierz zapisane współrzędne przycisków"""
        coords_file = Path(__file__).parent / 'gui_coordinates.json'
        
        if coords_file.exists():
            with open(coords_file) as f:
                return json.load(f)
        
        # Domyślne współrzędne (dostosuj do swojego ekranu)
        return {
            'chat_x': 400,
            'chat_y': 600,
            'continue_x': 800,
            'continue_y': 700
        }
    
    def calibrate_gui(self):
        """Kalibruj współrzędne GUI (helper)"""
        print("GUI Calibration Mode")
        if not self.use_automation:
            print("WARNING: GUI automation is not available in this environment.")
            print("Calibration cannot proceed without GUI support. Please run this script in a GUI environment with proper display authorization.")
            return
        print("Move mouse to chat area and press Enter...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nCalibration interrupted by user.")
            return
        except Exception as e:
            print(f"\nAn error occurred during calibration input: {e}")
            return
        # Record position
        self.chat_position = pyautogui.position()
        print(f"Chat area position recorded: {self.chat_position}")
    
    def test_connection(self) -> bool:
        """Test połączenia z Windsurf"""
        try:
            if self.use_api:
                import requests
                response = requests.get(
                    f"{self.config.get('windsurf_api_url', 'http://localhost:8091/api')}/health",
                    timeout=5
                )
                return response.status_code == 200
            else:
                # Sprawdź czy proces działa
                result = subprocess.run(
                    ['pgrep', '-f', 'windsurf'],
                    capture_output=True
                )
                return result.returncode == 0
        except:
            return False
    
    def cleanup(self):
        """Cleanup"""
        pass


# Funkcja pomocnicza do kalibracji
def calibrate():
    """Kalibruj współrzędne GUI"""
    controller = WindsurfController({'use_gui_automation': True})
    controller.calibrate_gui()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'calibrate':
        calibrate()
    else:
        print("Usage: python windsurf_controller.py calibrate")
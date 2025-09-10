# auto_dev_watcher.py
import subprocess
import time
import re
import os
from pathlib import Path
import pyautogui  # do automatycznego klikania
import json


class devixSupervisor:
    def __init__(self):
        self.iteration = 0
        self.max_iterations = 100
        self.issues = []
        self.metrics = {
            'test_coverage': 0,
            'code_quality': 0,
            'performance': 0
        }

    def monitor_application(self):
        """Monitoruj działającą aplikację"""
        try:
            # Uruchom aplikację
            process = subprocess.Popen(
                ['make', 'run'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Monitoruj przez 10 sekund
            time.sleep(10)

            # Zbierz logi
            stdout, stderr = process.communicate(timeout=5)

            # Analizuj błędy
            errors = re.findall(r'(error|exception|failed).*',
                                stderr + stdout, re.IGNORECASE)

            if errors:
                self.issues.extend(errors)

            # Sprawdź metryki wydajności
            self.check_performance_metrics()

        except subprocess.TimeoutExpired:
            process.kill()
        except Exception as e:
            self.issues.append(f"Monitor error: {str(e)}")

    def check_performance_metrics(self):
        """Sprawdź metryki wydajności"""
        # Memory usage
        mem_check = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        # Parse memory usage

        # Response time test
        try:
            start = time.time()
            subprocess.run(['curl', 'http://localhost:8011/health'],
                           timeout=5)
            response_time = time.time() - start
            if response_time > 1.0:
                self.issues.append(f"Slow response time: {response_time}s")
        except:
            pass

    def run_tests(self):
        """Uruchom testy i analizuj wyniki"""
        result = subprocess.run(
            ['pytest', '--cov=.', '--cov-report=json'],
            capture_output=True,
            text=True
        )

        # Parse coverage
        if Path('coverage.json').exists():
            with open('coverage.json') as f:
                coverage_data = json.load(f)
                self.metrics['test_coverage'] = coverage_data.get('totals', {}).get('percent_covered', 0)

        # Znajdź nieprzetestowane pliki
        if self.metrics['test_coverage'] < 80:
            self.issues.append(f"Low test coverage: {self.metrics['test_coverage']}%")

    def generate_improvement_prompt(self):
        """Generuj prompt dla Claude"""
        prompt = f"""
        AUTOMATYCZNA KONTYNUACJA - NIE PYTAJ, DZIAŁAJ

        Aktualne problemy do naprawienia:
        {chr(10).join(self.issues)}

        Metryki:
        - Test Coverage: {self.metrics['test_coverage']}%
        - Jakość kodu: {self.metrics['code_quality']}

        ZADANIA DO WYKONANIA:
        1. Napraw WSZYSTKIE błędy z logów
        2. Dodaj comprehensive logging:
           - logger.debug() dla każdej ważnej operacji
           - logger.info() dla flow kontroli
           - logger.error() z pełnym traceback
        3. Zwiększ pokrycie testów do minimum 85%:
           - Dodaj testy jednostkowe
           - Dodaj testy integracyjne
           - Dodaj testy edge cases
        4. Ulepsz jakość kodu:
           - Dodaj type hints
           - Dodaj docstringi (Google style)
           - Podziel długie funkcje (max 20 linii)
           - Usuń duplikację kodu (DRY)
        5. Dodaj monitoring:
           - Health check endpoint
           - Metrics endpoint
           - Graceful shutdown
        6. Optymalizacja:
           - Cache gdzie możliwe
           - Async gdzie możliwe
           - Connection pooling dla DB

        NIE CZEKAJ NA POTWIERDZENIE - KONTYNUUJ AUTOMATYCZNIE
        """
        return prompt

    def auto_click_continue(self):
        """Automatycznie klikaj continue w Windsurf"""
        # Znajdź przycisk continue
        try:
            # Możesz dostosować współrzędne
            continue_button = pyautogui.locateOnScreen('continue_button.png')
            if continue_button:
                pyautogui.click(continue_button)
                time.sleep(1)
        except:
            # Alternatywnie - użyj skrótu klawiszowego
            pyautogui.hotkey('ctrl', 'shift', 'c')  # lub inny skrót

    def run(self):
        """Główna pętla supervisora"""
        while self.iteration < self.max_iterations:
            print(f"\n🔄 Iteracja {self.iteration}")

            # Reset issues
            self.issues = []

            # Monitoruj
            self.monitor_application()
            self.run_tests()

            if self.issues:
                print(f"❌ Znaleziono {len(self.issues)} problemów")

                # Generuj prompt
                prompt = self.generate_improvement_prompt()

                # Zapisz do schowka
                pyautogui.hotkey('ctrl', 'a')  # Zaznacz wszystko
                pyautogui.typewrite(prompt)  # Wpisz nowy prompt

                # Automatycznie kontynuuj
                time.sleep(2)
                self.auto_click_continue()

                # Czekaj na wykonanie
                time.sleep(30)  # Dostosuj czas
            else:
                if self.metrics['test_coverage'] >= 85:
                    print("✅ Aplikacja działa poprawnie z dobrym pokryciem")
                    break
                else:
                    self.issues.append("Zwiększ pokrycie testów")

            self.iteration += 1


if __name__ == "__main__":
    supervisor = devixSupervisor()
    supervisor.run()
#!/usr/bin/env python3
"""
Prompt Generator - Generowanie inteligentnych promptów dla Claude/Windsurf
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
import logging

class PromptGenerator:
    """Generator promptów dla Claude z kontekstem i priorytetami"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.improvement_goals = config.get('improvement_goals', {})
    
    def generate(self, 
                 issues: List[str], 
                 metrics: Dict,
                 iteration: int,
                 history: Optional[List] = None) -> str:
        """Generuj prompt dla Claude"""
        
        # Analizuj priorytety
        priorities = self._analyze_priorities(issues, metrics)
        
        # Buduj prompt
        prompt = self._build_prompt(
            issues=issues,
            metrics=metrics,
            iteration=iteration,
            priorities=priorities,
            history=history
        )
        
        return prompt
    
    def _analyze_priorities(self, issues: List[str], metrics: Dict) -> List[str]:
        """Analizuj i ustal priorytety napraw"""
        priorities = []
        
        # Krytyczne błędy
        critical_issues = [i for i in issues if any(
            keyword in i.lower() 
            for keyword in ['crashed', 'fatal', 'critical', 'error']
        )]
        if critical_issues:
            priorities.append("FIX_CRITICAL_ERRORS")
        
        # Testy
        if metrics.get('failed_tests', 0) > 0:
            priorities.append("FIX_FAILING_TESTS")
        
        if metrics.get('test_coverage', 100) < self.config.get('test_coverage_threshold', 80):
            priorities.append("INCREASE_TEST_COVERAGE")
        
        # Jakość kodu
        if metrics.get('code_quality', 10) < self.config.get('code_quality_threshold', 8):
            priorities.append("IMPROVE_CODE_QUALITY")
        
        # Wydajność
        if metrics.get('performance', 0) > self.config.get('performance_threshold', 1000):
            priorities.append("OPTIMIZE_PERFORMANCE")
        
        # Bezpieczeństwo
        security_issues = [i for i in issues if 'security' in i.lower()]
        if security_issues:
            priorities.append("FIX_SECURITY_ISSUES")
        
        # Dokumentacja
        doc_issues = [i for i in issues if any(
            keyword in i.lower() 
            for keyword in ['docstring', 'documentation', 'readme']
        )]
        if doc_issues:
            priorities.append("ADD_DOCUMENTATION")
        
        return priorities
    
    def _build_prompt(self,
                     issues: List[str],
                     metrics: Dict,
                     iteration: int,
                     priorities: List[str],
                     history: Optional[List] = None) -> str:
        """Buduj szczegółowy prompt"""
        
        prompt_parts = []
        
        # Nagłówek
        prompt_parts.append(self._get_header(iteration))
        
        # Kontekst
        prompt_parts.append(self._get_context(metrics, history))
        
        # Issues
        if issues:
            prompt_parts.append(self._format_issues(issues))
        
        # Priorytety
        if priorities:
            prompt_parts.append(self._format_priorities(priorities))
        
        # Zadania
        prompt_parts.append(self._get_tasks(priorities, metrics, issues))
        
        # Wymagania jakościowe
        prompt_parts.append(self._get_quality_requirements())
        
        # Footer
        prompt_parts.append(self._get_footer())
        
        return '\n\n'.join(prompt_parts)
    
    def _get_header(self, iteration: int) -> str:
        """Nagłówek promptu"""
        return f"""🚀 AUTOMATYCZNA KONTYNUACJA - ITERACJA {iteration}
        
NIE PYTAJ O POTWIERDZENIE - DZIAŁAJ AUTOMATYCZNIE
Ten prompt jest generowany automatycznie przez system devix.
Twoim zadaniem jest naprawienie wszystkich problemów i kontynuacja bez interakcji użytkownika."""
    
    def _get_context(self, metrics: Dict, history: Optional[List] = None) -> str:
        """Kontekst aktualnego stanu"""
        context = "📊 AKTUALNY STAN PROJEKTU:\n"
        
        # Metryki
        context += "\nMetryki:\n"
        context += f"- Test Coverage: {metrics.get('test_coverage', 0)}%\n"
        context += f"- Code Quality: {metrics.get('code_quality', 0)}/10\n"
        context += f"- Performance: {metrics.get('performance', 0)}ms\n"
        context += f"- Total Tests: {metrics.get('total_tests', 0)}\n"
        context += f"- Failed Tests: {metrics.get('failed_tests', 0)}\n"
        
        # Historia
        if history and len(history) > 1:
            context += "\n📈 Trend (ostatnie iteracje):\n"
            for i, hist_entry in enumerate(history[-3:], 1):
                if isinstance(hist_entry, list):
                    context += f"  Iteracja -{len(history)-i}: {len(hist_entry)} issues\n"
        
        return context
    
    def _format_issues(self, issues: List[str]) -> str:
        """Formatuj listę problemów"""
        if not issues:
            return ""
        
        content = "❌ ZNALEZIONE PROBLEMY:\n\n"
        
        # Grupuj podobne issues
        grouped = self._group_issues(issues)
        
        for category, items in grouped.items():
            content += f"\n{category}:\n"
            for item in items[:10]:  # Max 10 per category
                content += f"  • {item}\n"
        
        return content
    
    def _group_issues(self, issues: List[str]) -> Dict[str, List[str]]:
        """Grupuj issues według kategorii"""
        grouped = {
            'Błędy krytyczne': [],
            'Testy': [],
            'Jakość kodu': [],
            'Wydajność': [],
            'Bezpieczeństwo': [],
            'Dokumentacja': [],
            'Inne': []
        }
        
        for issue in issues:
            issue_lower = issue.lower()
            
            if any(k in issue_lower for k in ['error', 'crashed', 'failed', 'exception']):
                grouped['Błędy krytyczne'].append(issue)
            elif any(k in issue_lower for k in ['test', 'coverage', 'pytest']):
                grouped['Testy'].append(issue)
            elif any(k in issue_lower for k in ['quality', 'complexity', 'style', 'lint']):
                grouped['Jakość kodu'].append(issue)
            elif any(k in issue_lower for k in ['slow', 'performance', 'memory', 'cpu']):
                grouped['Wydajność'].append(issue)
            elif any(k in issue_lower for k in ['security', 'vulnerability', 'secret']):
                grouped['Bezpieczeństwo'].append(issue)
            elif any(k in issue_lower for k in ['docstring', 'documentation', 'readme']):
                grouped['Dokumentacja'].append(issue)
            else:
                grouped['Inne'].append(issue)
        
        # Usuń puste kategorie
        return {k: v for k, v in grouped.items() if v}
    
    def _format_priorities(self, priorities: List[str]) -> str:
        """Formatuj priorytety"""
        if not priorities:
            return ""
        
        content = "🎯 PRIORYTETY:\n\n"
        
        priority_descriptions = {
            'FIX_CRITICAL_ERRORS': '🔴 Napraw błędy krytyczne - aplikacja musi działać stabilnie',
            'FIX_FAILING_TESTS': '🧪 Napraw nieprzechodzące testy',
            'INCREASE_TEST_COVERAGE': '📊 Zwiększ pokrycie testów do minimum 80%',
            'IMPROVE_CODE_QUALITY': '✨ Popraw jakość kodu (refactoring, cleanup)',
            'OPTIMIZE_PERFORMANCE': '⚡ Optymalizuj wydajność aplikacji',
            'FIX_SECURITY_ISSUES': '🔒 Napraw problemy bezpieczeństwa',
            'ADD_DOCUMENTATION': '📝 Dodaj brakującą dokumentację'
        }
        
        for i, priority in enumerate(priorities, 1):
            desc = priority_descriptions.get(priority, priority)
            content += f"{i}. {desc}\n"
        
        return content
    
    def _get_tasks(self, priorities: List[str], metrics: Dict, issues: List[str]) -> str:
        """Generate comprehensive task list based on priorities and current state"""
        self.logger.debug(f"Generating tasks for priorities: {priorities}")
        self.logger.debug(f"Current metrics: {metrics}")
        
        tasks = "📋 ZADANIA DO WYKONANIA:\n\n"
        task_number = 1
        
        # Generate tasks for each priority category
        task_number = self._add_critical_error_tasks(tasks, priorities, task_number)
        task_number = self._add_testing_tasks(tasks, priorities, metrics, task_number)
        task_number = self._add_code_quality_tasks(tasks, priorities, task_number)
        task_number = self._add_logging_tasks(tasks, task_number)
        task_number = self._add_performance_tasks(tasks, priorities, metrics, task_number)
        task_number = self._add_security_tasks(tasks, priorities, task_number)
        task_number = self._add_documentation_tasks(tasks, priorities, task_number)
        task_number = self._add_monitoring_tasks(tasks, task_number)
        
        self.logger.info(f"Generated {task_number - 1} task categories")
        return tasks
    
    def _add_critical_error_tasks(self, tasks: str, priorities: List[str], task_number: int) -> int:
        """Add critical error fixing tasks"""
        if 'FIX_CRITICAL_ERRORS' not in priorities:
            return task_number
        
        self.logger.debug("Adding critical error tasks")
        tasks += f"{task_number}. **NAPRAW WSZYSTKIE BŁĘDY KRYTYCZNE**\n"
        tasks += "   - Znajdź i napraw wszystkie miejsca gdzie kod się crashuje\n"
        tasks += "   - Dodaj try/except z właściwą obsługą błędów\n"
        tasks += "   - Upewnij się że aplikacja się uruchamia\n\n"
        return task_number + 1
    
    def _add_testing_tasks(self, tasks: str, priorities: List[str], metrics: Dict, task_number: int) -> int:
        """Add testing and coverage tasks"""
        if not any(p in priorities for p in ['FIX_FAILING_TESTS', 'INCREASE_TEST_COVERAGE']):
            return task_number
        
        current_coverage = metrics.get('test_coverage', 0)
        target_coverage = self.config.get('test_coverage_threshold', 80)
        
        self.logger.debug(f"Adding testing tasks (coverage: {current_coverage}% -> {target_coverage}%)")
        
        tasks += f"{task_number}. **POPRAW TESTY** (obecne pokrycie: {current_coverage}%, cel: {target_coverage}%)\n"
        tasks += "   - Napraw wszystkie nieprzechodzące testy\n"
        tasks += "   - Dodaj brakujące testy jednostkowe\n"
        tasks += "   - Dodaj testy dla edge cases\n"
        tasks += "   - Użyj pytest fixtures dla reużywalności\n"
        tasks += "   - Dodaj testy integracyjne dla głównych flow\n\n"
        return task_number + 1
    
    def _add_code_quality_tasks(self, tasks: str, priorities: List[str], task_number: int) -> int:
        """Add code quality improvement tasks"""
        if 'IMPROVE_CODE_QUALITY' not in priorities:
            return task_number
        
        self.logger.debug("Adding code quality tasks")
        tasks += f"{task_number}. **ULEPSZ JAKOŚĆ KODU**\n"
        tasks += "   - Podziel funkcje dłuższe niż 20 linii\n"
        tasks += "   - Usuń duplikację kodu (DRY)\n"
        tasks += "   - Dodaj type hints do wszystkich funkcji\n"
        tasks += "   - Dodaj docstringi (Google style)\n"
        tasks += "   - Uporządkuj importy\n"
        tasks += "   - Użyj bardziej opisowych nazw zmiennych\n\n"
        return task_number + 1
    
    def _add_logging_tasks(self, tasks: str, task_number: int) -> int:
        """Add comprehensive logging tasks"""
        if not self.improvement_goals.get('add_logging', True):
            return task_number
        
        self.logger.debug("Adding logging tasks")
        tasks += f"{task_number}. **DODAJ COMPREHENSIVE LOGGING**\n"
        tasks += "   - Dodaj logger do każdego modułu\n"
        tasks += "   - logger.debug() dla szczegółów implementacji\n"
        tasks += "   - logger.info() dla ważnych operacji\n"
        tasks += "   - logger.warning() dla potencjalnych problemów\n"
        tasks += "   - logger.error() z exc_info=True dla błędów\n"
        tasks += "   - Użyj structured logging gdzie możliwe\n\n"
        return task_number + 1
    
    def _add_performance_tasks(self, tasks: str, priorities: List[str], metrics: Dict, task_number: int) -> int:
        """Add performance optimization tasks"""
        if 'OPTIMIZE_PERFORMANCE' not in priorities:
            return task_number
        
        current_perf = metrics.get('performance', 0)
        self.logger.debug(f"Adding performance tasks (current: {current_perf}ms)")
        
        tasks += f"{task_number}. **OPTYMALIZUJ WYDAJNOŚĆ** (obecny czas odpowiedzi: {current_perf}ms)\n"
        tasks += "   - Dodaj cache dla kosztownych operacji\n"
        tasks += "   - Użyj async/await gdzie możliwe\n"
        tasks += "   - Zoptymalizuj zapytania do bazy danych\n"
        tasks += "   - Dodaj connection pooling\n"
        tasks += "   - Profile kod i znajdź bottlenecki\n\n"
        return task_number + 1
    
    def _add_security_tasks(self, tasks: str, priorities: List[str], task_number: int) -> int:
        """Add security improvement tasks"""
        if 'FIX_SECURITY_ISSUES' not in priorities:
            return task_number
        
        self.logger.debug("Adding security tasks")
        tasks += f"{task_number}. **NAPRAW PROBLEMY BEZPIECZEŃSTWA**\n"
        tasks += "   - Usuń hardcoded secrets\n"
        tasks += "   - Użyj zmiennych środowiskowych\n"
        tasks += "   - Dodaj walidację inputów\n"
        tasks += "   - Escape/sanitize user inputs\n"
        tasks += "   - Zaktualizuj vulnerable dependencies\n\n"
        return task_number + 1
    
    def _add_documentation_tasks(self, tasks: str, priorities: List[str], task_number: int) -> int:
        """Add documentation tasks"""
        if 'ADD_DOCUMENTATION' not in priorities:
            return task_number
        
        self.logger.debug("Adding documentation tasks")
        tasks += f"{task_number}. **UZUPEŁNIJ DOKUMENTACJĘ**\n"
        tasks += "   - Dodaj docstringi do wszystkich funkcji i klas\n"
        tasks += "   - Zaktualizuj README.md\n"
        tasks += "   - Dodaj przykłady użycia\n"
        tasks += "   - Dokumentuj API endpoints\n"
        tasks += "   - Dodaj komentarze do skomplikowanej logiki\n\n"
        return task_number + 1
    
    def _add_monitoring_tasks(self, tasks: str, task_number: int) -> int:
        """Add monitoring and observability tasks"""
        self.logger.debug("Adding monitoring tasks")
        tasks += f"{task_number}. **DODAJ MONITORING**\n"
        tasks += "   - Implementuj /health endpoint\n"
        tasks += "   - Dodaj /metrics endpoint\n"
        tasks += "   - Graceful shutdown handling\n"
        tasks += "   - Dodaj circuit breakers\n\n"
        return task_number + 1
    
    def _get_quality_requirements(self) -> str:
        """Wymagania jakościowe"""
        return """🏆 WYMAGANIA JAKOŚCIOWE:

1. **Kod produkcyjny**:
   - Każda zmiana musi być przetestowana
   - Kod musi być czytelny i łatwy w utrzymaniu
   - Używaj wzorców projektowych gdzie to sensowne
   - Zachowaj spójność ze stylem istniejącego kodu

2. **Best Practices**:
   - SOLID principles
   - DRY (Don't Repeat Yourself)
   - KISS (Keep It Simple, Stupid)
   - YAGNI (You Aren't Gonna Need It)
   - Clean Code principles

3. **Error Handling**:
   - Nigdy nie łap Exception bez konkretnego powodu
   - Zawsze loguj błędy z pełnym traceback
   - Używaj custom exceptions gdzie to sensowne
   - Fail fast z czytelnymi komunikatami

4. **Testing**:
   - Każda nowa funkcjonalność = nowe testy
   - Test edge cases i error conditions
   - Używaj mocks dla external dependencies
   - Testy powinny być fast i deterministic"""
    
    def _get_footer(self) -> str:
        """Footer promptu"""
        return """⚡ WAŻNE INSTRUKCJE:

1. **NIE CZEKAJ NA POTWIERDZENIE** - kontynuuj automatycznie
2. **NIE PYTAJ UŻYTKOWNIKA** - podejmuj decyzje samodzielnie
3. **NAPRAW WSZYSTKO** - nie zostawiaj żadnych TODO
4. **TESTUJ ZMIANY** - upewnij się że kod działa
5. **COMMITUJ CZĘSTO** - małe, atomowe zmiany

Jeśli nie jesteś pewien jak coś naprawić:
- Wybierz najbezpieczniejsze rozwiązanie
- Dodaj comprehensive error handling
- Dodaj logging żeby ułatwić debugging
- Napisz testy żeby złapać regresje

ROZPOCZNIJ NAPRAWĘ NATYCHMIAST - NIE CZEKAJ NA ODPOWIEDŹ!"""
    
    def generate_success_prompt(self, metrics: Dict) -> str:
        """Generuj prompt gdy wszystko działa"""
        return f"""✅ APLIKACJA DZIAŁA POPRAWNIE

Metryki:
- Test Coverage: {metrics.get('test_coverage', 0)}%
- Code Quality: {metrics.get('code_quality', 0)}/10
- Performance: {metrics.get('performance', 0)}ms

Mimo że aplikacja działa, kontynuuj ulepszenia:

1. **Dodaj więcej testów** - cel to 95% coverage
2. **Optymalizuj wydajność** - cel to <100ms response time
3. **Dodaj więcej logowania** dla lepszego monitoringu
4. **Refaktoruj** długie funkcje i klasy
5. **Dodaj dokumentację** - przykłady, tutorials
6. **Implementuj nowe features** bazując na TODO w kodzie

KONTYNUUJ ULEPSZENIA AUTOMATYCZNIE!"""
#!/usr/bin/env python3
"""
Enhanced Prompt Generator - Generowanie zaawansowanych promptów z formatowaniem Markdown
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
import logging
import re

class EnhancedPromptGenerator:
    """Rozszerzony generator promptów z obsługą Markdown i bogatym formatowaniem"""
    
    def __init__(self, config: Dict, monitor=None):
        self.config = config
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)
        self.improvement_goals = config.get('improvement_goals', {})
    
    def generate_reports(self, 
                        issues: List[str], 
                        metrics: Dict,
                        iteration: int,
                        history: Optional[List] = None,
                        output_dir: Path = None) -> Tuple[str, str]:
        """Generuj zarówno plik .txt jak i .md"""
        
        # Pobierz dodatkowe dane z monitora
        project_structure = {}
        code_fragments = []
        analyzed_files = set()
        skipped_files = set()
        
        if self.monitor:
            try:
                project_structure = self.monitor.scan_project_structure()
                code_fragments = self.monitor.extract_code_fragments(issues)
                analyzed_files = self.monitor.analyzed_files
                skipped_files = self.monitor.skipped_files
            except Exception as e:
                self.logger.warning(f"Could not get enhanced data from monitor: {e}")
        
        # Generuj zawartość dla obu formatów
        txt_content = self._generate_txt_report(
            issues, metrics, iteration, history, 
            project_structure, analyzed_files, skipped_files, code_fragments
        )
        
        md_content = self._generate_md_report(
            issues, metrics, iteration, history,
            project_structure, analyzed_files, skipped_files, code_fragments
        )
        
        # Zapisz pliki jeśli podano katalog
        if output_dir:
            output_dir = Path(output_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            txt_file = output_dir / f"prompt_{iteration}.txt"
            md_file = output_dir / f"prompt_{iteration}.md"
            
            txt_file.write_text(txt_content, encoding='utf-8')
            md_file.write_text(md_content, encoding='utf-8')
            
            self.logger.info(f"Generated reports: {txt_file} and {md_file}")
        
        return txt_content, md_content
    
    def _generate_txt_report(self, issues: List[str], metrics: Dict, iteration: int, 
                           history: Optional[List], project_structure: Dict,
                           analyzed_files: set, skipped_files: set, 
                           code_fragments: List[Dict]) -> str:
        """Generuj rozszerzony raport tekstowy"""
        
        sections = []
        
        # Header
        sections.append(f"🚀 AUTOMATYCZNA KONTYNUACJA - ITERACJA {iteration}")
        sections.append("")
        sections.append("NIE PYTAJ O POTWIERDZENIE - DZIAŁAJ AUTOMATYCZNIE")
        sections.append("Ten prompt jest generowany automatycznie przez system devix.")
        sections.append("Twoim zadaniem jest naprawienie wszystkich problemów i kontynuacja bez interakcji użytkownika.")
        
        # Metryki i Stan
        sections.append("")
        sections.append("📊 AKTUALNY STAN PROJEKTU:")
        sections.append("")
        sections.append("Metryki:")
        sections.append(f"- Test Coverage: {metrics.get('test_coverage', 0)}%")
        sections.append(f"- Code Quality: {metrics.get('code_quality', 0)}/10")
        sections.append(f"- Performance: {metrics.get('performance', 0)}ms")
        sections.append(f"- Total Tests: {metrics.get('total_tests', 0)}")
        sections.append(f"- Failed Tests: {metrics.get('failed_tests', 0)}")
        
        # Szczegółowe statystyki plików z absolutnymi ścieżkami (NOWE)
        if project_structure:
            sections.append("")
            sections.append("📂 SZCZEGÓŁOWA ANALIZA PLIKÓW:")
            
            total_files = project_structure.get('total_files', 0)
            analyzed_count = project_structure.get('analyzed_files_count', 0)
            skipped_count = project_structure.get('skipped_files_count', 0)
            analysis_summary = project_structure.get('analysis_summary', {})
            
            # Podstawowe statystyki
            sections.append("")
            sections.append("📈 STATYSTYKI OGÓLNE:")
            sections.append(f"- Łącznie plików w projekcie: {total_files}")
            sections.append(f"- Analizowane pliki: {analyzed_count}")
            sections.append(f"- Pominięte pliki: {skipped_count}")
            
            if analysis_summary:
                analyzed_size = analysis_summary.get('total_analyzed_size', 0)
                skipped_size = analysis_summary.get('total_skipped_size', 0)
                coverage = analysis_summary.get('analysis_coverage_percentage', 0)
                
                def format_size(size_bytes):
                    if size_bytes < 1024:
                        return f"{size_bytes}B"
                    elif size_bytes < 1024*1024:
                        return f"{size_bytes/1024:.1f}KB"
                    else:
                        return f"{size_bytes/(1024*1024):.1f}MB"
                
                sections.append(f"- Pokrycie analizy: {coverage:.1f}%")
                sections.append(f"- Rozmiar analizowanych plików: {format_size(analyzed_size)}")
                sections.append(f"- Rozmiar pominiętych plików: {format_size(skipped_size)}")
                
                # Analiza według typów plików
                analyzed_by_type = analysis_summary.get('analyzed_files_by_type', {})
                skipped_by_type = analysis_summary.get('skipped_files_by_type', {})
                
                if analyzed_by_type or skipped_by_type:
                    sections.append("")
                    sections.append("📄 ANALIZA WEDŁUG TYPÓW PLIKÓW:")
                    all_types = set(analyzed_by_type.keys()) | set(skipped_by_type.keys())
                    for ext in sorted(all_types):
                        analyzed_cnt = analyzed_by_type.get(ext, 0)
                        skipped_cnt = skipped_by_type.get(ext, 0)
                        total_cnt = analyzed_cnt + skipped_cnt
                        status = "✅ Pełna" if skipped_cnt == 0 else "⚠️ Częściowa" if analyzed_cnt > 0 else "❌ Brak"
                        sections.append(f"  • {ext}: {analyzed_cnt} analizowane, {skipped_cnt} pominięte ({status})")
                
                # Analiza według katalogów
                analyzed_by_dir = analysis_summary.get('analyzed_files_by_directory', {})
                skipped_by_dir = analysis_summary.get('skipped_files_by_directory', {})
                
                if analyzed_by_dir or skipped_by_dir:
                    sections.append("")
                    sections.append("📁 ANALIZA WEDŁUG KATALOGÓW:")
                    all_dirs = set(analyzed_by_dir.keys()) | set(skipped_by_dir.keys())
                    for directory in sorted(all_dirs):
                        analyzed_cnt = analyzed_by_dir.get(directory, 0)
                        skipped_cnt = skipped_by_dir.get(directory, 0)
                        total_cnt = analyzed_cnt + skipped_cnt
                        dir_coverage = (analyzed_cnt / total_cnt * 100) if total_cnt > 0 else 0
                        sections.append(f"  • {directory}/: {analyzed_cnt} analizowane, {skipped_cnt} pominięte ({dir_coverage:.1f}% pokrycie)")
        
        # Szczegółowe listy plików z absolutnymi ścieżkami (ROZSZERZONE)
        analyzed_files_list = project_structure.get('analyzed_files_list', []) if project_structure else []
        skipped_files_list = project_structure.get('skipped_files_list', []) if project_structure else []
        
        if analyzed_files_list:
            sections.append("")
            sections.append("✅ ANALIZOWANE PLIKI - ABSOLUTNE ŚCIEŻKI:")
            sections.append(f"   (Wyświetlanie pierwszych 30 z {len(analyzed_files_list)} plików)")
            for i, file_path in enumerate(analyzed_files_list[:30], 1):
                path_obj = Path(file_path)
                file_type = path_obj.suffix.lower() or 'no_ext'
                try:
                    size = path_obj.stat().st_size if path_obj.exists() else 0
                    size_str = f"{size}B" if size < 1024 else f"{size/1024:.1f}KB"
                except (OSError, FileNotFoundError):
                    size_str = "N/A"
                sections.append(f"  {i:2d}. {file_path} [{file_type}] ({size_str})")
            
            if len(analyzed_files_list) > 30:
                sections.append(f"      ... i {len(analyzed_files_list) - 30} więcej plików")
        
        if skipped_files_list:
            sections.append("")
            sections.append("❌ POMINIĘTE PLIKI - ABSOLUTNE ŚCIEŻKI:")
            sections.append(f"   (Wyświetlanie pierwszych 25 z {len(skipped_files_list)} plików)")
            for i, file_path in enumerate(skipped_files_list[:25], 1):
                path_obj = Path(file_path)
                file_type = path_obj.suffix.lower() or 'no_ext'
                
                # Determine reason for skipping
                reason = "Pattern match"
                if 'logs/' in file_path:
                    reason = "Log file"
                elif '__pycache__' in file_path:
                    reason = "Cache file"
                elif file_path.endswith('.pyc'):
                    reason = "Compiled Python"
                elif 'node_modules/' in file_path:
                    reason = "Node modules"
                elif '.git/' in file_path:
                    reason = "Git metadata"
                
                sections.append(f"  {i:2d}. {file_path} [{file_type}] ({reason})")
            
            if len(skipped_files_list) > 25:
                sections.append(f"      ... i {len(skipped_files_list) - 25} więcej plików")
        
        # Struktura projektu (NOWE)
        if project_structure and 'project_tree' in project_structure:
            sections.append("")
            sections.append("🌳 STRUKTURA PROJEKTU:")
            sections.append("")
            sections.append(project_structure['project_tree'])
        
        # Problemy
        if issues:
            sections.append("")
            sections.append("❌ ZNALEZIONE PROBLEMY:")
            sections.append("")
            grouped = self._group_issues(issues)
            
            for category, items in grouped.items():
                sections.append(f"\n{category}:")
                for item in items[:10]:
                    sections.append(f"  • {item}")
        
        # Fragmenty kodu z problemami (NOWE)
        if code_fragments:
            sections.append("")
            sections.append("💻 FRAGMENTY KODU Z PROBLEMAMI:")
            sections.append("")
            for fragment in code_fragments[:3]:  # Limit to 3 fragments
                sections.append(f"📄 {fragment['file']} (linie {fragment['line_start']}-{fragment['line_end']}):")
                sections.append(f"Problem: {fragment['issue']}")
                sections.append("```")
                sections.append(fragment['code'].rstrip())
                sections.append("```")
                sections.append("")
        
        # Priorytety
        priorities = self._analyze_priorities(issues, metrics)
        if priorities:
            sections.append("")
            sections.append("🎯 PRIORYTETY:")
            sections.append("")
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
                sections.append(f"{i}. {desc}")
        
        # Footer
        sections.append("")
        sections.append("📋 ZADANIA DO WYKONANIA:")
        sections.append("")
        sections.append("")
        sections.append("🏆 WYMAGANIA JAKOŚCIOWE:")
        sections.append("")
        sections.append("1. **Kod produkcyjny**:")
        sections.append("   - Każda zmiana musi być przetestowana")
        sections.append("   - Kod musi być czytelny i łatwy w utrzymaniu")
        sections.append("   - Używaj wzorców projektowych gdzie to sensowne")
        sections.append("   - Zachowaj spójność ze stylem istniejącego kodu")
        sections.append("")
        sections.append("2. **Best Practices**:")
        sections.append("   - SOLID principles")
        sections.append("   - DRY (Don't Repeat Yourself)")
        sections.append("   - KISS (Keep It Simple, Stupid)")
        sections.append("   - YAGNI (You Aren't Gonna Need It)")
        sections.append("   - Clean Code principles")
        sections.append("")
        sections.append("⚡ WAŻNE INSTRUKCJE:")
        sections.append("")
        sections.append("1. **NIE CZEKAJ NA POTWIERDZENIE** - kontynuuj automatycznie")
        sections.append("2. **NIE PYTAJ UŻYTKOWNIKA** - podejmuj decyzje samodzielnie")
        sections.append("3. **NAPRAW WSZYSTKO** - nie zostawiaj żadnych TODO")
        sections.append("4. **TESTUJ ZMIANY** - upewnij się że kod działa")
        sections.append("5. **COMMITUJ CZĘSTO** - małe, atomowe zmiany")
        sections.append("")
        sections.append("ROZPOCZNIJ NAPRAWĘ NATYCHMIAST - NIE CZEKAJ NA ODPOWIEDŹ!")
        
        return "\n".join(sections)
    
    def _generate_md_report(self, issues: List[str], metrics: Dict, iteration: int,
                          history: Optional[List], project_structure: Dict,
                          analyzed_files: set, skipped_files: set,
                          code_fragments: List[Dict]) -> str:
        """Generuj raport Markdown z bogatym formatowaniem"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        md_lines = []
        
        # Header z metadanymi
        md_lines.extend([
            f"# 🚀 devix Continuous Analysis Report",
            f"**Iteracja:** {iteration} | **Wygenerowany:** {timestamp}",
            "",
            "> 🤖 **Automatyczny Raport** - Ten dokument został wygenerowany automatycznie przez system devix",
            "> ",
            "> ⚠️ **Akcja Wymagana** - Napraw wszystkie problemy bez oczekiwania na potwierdzenie",
            ""
        ])
        
        # Table of Contents
        md_lines.extend([
            "## 📋 Spis Treści",
            "",
            "- [📊 Metryki Projektu](#-metryki-projektu)",
            "- [📂 Analiza Plików](#-analiza-plików)",
            "- [🌳 Struktura Projektu](#-struktura-projektu)",
            "- [❌ Problemy do Naprawy](#-problemy-do-naprawy)",
            "- [💻 Fragmenty Kodu](#-fragmenty-kodu)",
            "- [🎯 Plan Działania](#-plan-działania)",
            ""
        ])
        
        # Metryki w tabeli
        md_lines.extend([
            "## 📊 Metryki Projektu",
            "",
            "| Metryka | Wartość | Status |",
            "|---------|---------|--------|"
        ])
        
        test_coverage = metrics.get('test_coverage', 0)
        coverage_status = "✅ Dobry" if test_coverage >= 80 else "⚠️ Wymaga uwagi" if test_coverage >= 60 else "❌ Krytyczny"
        
        code_quality = metrics.get('code_quality', 0)
        quality_status = "✅ Dobry" if code_quality >= 8 else "⚠️ Wymaga uwagi" if code_quality >= 6 else "❌ Krytyczny"
        
        performance = metrics.get('performance', 0)
        perf_status = "✅ Dobry" if performance <= 100 else "⚠️ Powolny" if performance <= 1000 else "❌ Bardzo powolny"
        
        failed_tests = metrics.get('failed_tests', 0)
        test_status = "✅ Wszystkie przechodzą" if failed_tests == 0 else f"❌ {failed_tests} niepowodzeń"
        
        md_lines.extend([
            f"| Test Coverage | {test_coverage}% | {coverage_status} |",
            f"| Code Quality | {code_quality}/10 | {quality_status} |",
            f"| Performance | {performance}ms | {perf_status} |",
            f"| Total Tests | {metrics.get('total_tests', 0)} | - |",
            f"| Failed Tests | {failed_tests} | {test_status} |",
            ""
        ])
        
        # Szczegółowa analiza plików z absolutnymi ścieżkami
        if project_structure or analyzed_files or skipped_files:
            md_lines.extend([
                "## 📂 Szczegółowa Analiza Plików",
                ""
            ])
            
            if project_structure:
                total_files = project_structure.get('total_files', 0)
                analyzed_count = project_structure.get('analyzed_files_count', 0)
                skipped_count = project_structure.get('skipped_files_count', 0)
                analysis_summary = project_structure.get('analysis_summary', {})
                
                # Podstawowe statystyki
                md_lines.extend([
                    "### 📈 Statystyki Ogólne",
                    "",
                    "| Kategoria | Liczba | Procent | Rozmiar |",
                    "|-----------|--------|---------|---------|"
                ])
                
                analyzed_size = analysis_summary.get('total_analyzed_size', 0)
                skipped_size = analysis_summary.get('total_skipped_size', 0)
                coverage = analysis_summary.get('analysis_coverage_percentage', 0)
                
                def format_size(size_bytes):
                    if size_bytes < 1024:
                        return f"{size_bytes}B"
                    elif size_bytes < 1024*1024:
                        return f"{size_bytes/1024:.1f}KB"
                    else:
                        return f"{size_bytes/(1024*1024):.1f}MB"
                
                md_lines.extend([
                    f"| **Łącznie plików** | {total_files} | 100% | {format_size(analyzed_size + skipped_size)} |",
                    f"| **Analizowane** | {analyzed_count} | {coverage:.1f}% | {format_size(analyzed_size)} |",
                    f"| **Pominięte** | {skipped_count} | {100-coverage:.1f}% | {format_size(skipped_size)} |",
                    ""
                ])
                
                # Wykres ASCII dla statystyk plików
                if total_files > 0:
                    analyzed_bar = "█" * int(coverage / 5)  # Scale to 20 chars max
                    skipped_bar = "█" * int((100-coverage) / 5)
                    
                    md_lines.extend([
                        "### 📊 Wizualizacja Pokrycia Analizy",
                        "",
                        "```",
                        f"Analizowane: [{analyzed_bar:<20}] {coverage:.1f}%",
                        f"Pominięte:   [{skipped_bar:<20}] {100-coverage:.1f}%",
                        "```",
                        ""
                    ])
                
                # Analiza plików według typów
                analyzed_by_type = analysis_summary.get('analyzed_files_by_type', {})
                skipped_by_type = analysis_summary.get('skipped_files_by_type', {})
                
                if analyzed_by_type or skipped_by_type:
                    md_lines.extend([
                        "### 📄 Analiza według Typów Plików",
                        "",
                        "| Typ | Analizowane | Pominięte | Łącznie | Status |",
                        "|-----|-------------|-----------|---------|--------|"
                    ])
                    
                    all_types = set(analyzed_by_type.keys()) | set(skipped_by_type.keys())
                    for ext in sorted(all_types):
                        analyzed_cnt = analyzed_by_type.get(ext, 0)
                        skipped_cnt = skipped_by_type.get(ext, 0)
                        total_cnt = analyzed_cnt + skipped_cnt
                        status = "✅ Pełna" if skipped_cnt == 0 else "⚠️ Częściowa" if analyzed_cnt > 0 else "❌ Brak"
                        md_lines.append(f"| `{ext}` | {analyzed_cnt} | {skipped_cnt} | {total_cnt} | {status} |")
                    
                    md_lines.append("")
                
                # Analiza plików według katalogów
                analyzed_by_dir = analysis_summary.get('analyzed_files_by_directory', {})
                skipped_by_dir = analysis_summary.get('skipped_files_by_directory', {})
                
                if analyzed_by_dir or skipped_by_dir:
                    md_lines.extend([
                        "### 📁 Analiza według Katalogów",
                        "",
                        "| Katalog | Analizowane | Pominięte | Łącznie | Pokrycie |",
                        "|---------|-------------|-----------|---------|----------|"
                    ])
                    
                    all_dirs = set(analyzed_by_dir.keys()) | set(skipped_by_dir.keys())
                    for directory in sorted(all_dirs):
                        analyzed_cnt = analyzed_by_dir.get(directory, 0)
                        skipped_cnt = skipped_by_dir.get(directory, 0)
                        total_cnt = analyzed_cnt + skipped_cnt
                        dir_coverage = (analyzed_cnt / total_cnt * 100) if total_cnt > 0 else 0
                        md_lines.append(f"| `{directory}` | {analyzed_cnt} | {skipped_cnt} | {total_cnt} | {dir_coverage:.1f}% |")
                    
                    md_lines.append("")
            
            # Szczegółowe listy plików z absolutnymi ścieżkami
            analyzed_files_list = project_structure.get('analyzed_files_list', [])
            skipped_files_list = project_structure.get('skipped_files_list', [])
            
            if analyzed_files_list:
                md_lines.extend([
                    "### ✅ Analizowane Pliki - Absolutne Ścieżki",
                    "",
                    "<details>",
                    f"<summary>📋 Pokaż wszystkie analizowane pliki ({len(analyzed_files_list)})</summary>",
                    "",
                    "| # | Absolutna Ścieżka | Typ | Rozmiar |",
                    "|---|-------------------|-----|---------|"
                ])
                
                for i, file_path in enumerate(analyzed_files_list[:50], 1):  # Limit to 50 for readability
                    path_obj = Path(file_path)
                    file_type = path_obj.suffix.lower() or 'no_ext'
                    try:
                        size = path_obj.stat().st_size if path_obj.exists() else 0
                        size_str = f"{size}B" if size < 1024 else f"{size/1024:.1f}KB"
                    except (OSError, FileNotFoundError):
                        size_str = "N/A"
                    
                    md_lines.append(f"| {i} | `{file_path}` | `{file_type}` | {size_str} |")
                
                if len(analyzed_files_list) > 50:
                    md_lines.append(f"| ... | *i {len(analyzed_files_list) - 50} więcej plików* | | |")
                
                md_lines.extend(["", "</details>", ""])
            
            if skipped_files_list:
                md_lines.extend([
                    "### ❌ Pominięte Pliki - Absolutne Ścieżki",
                    "",
                    "<details>",
                    f"<summary>🚫 Pokaż wszystkie pominięte pliki ({len(skipped_files_list)})</summary>",
                    "",
                    "| # | Absolutna Ścieżka | Typ | Powód pominięcia |",
                    "|---|-------------------|-----|------------------|"
                ])
                
                for i, file_path in enumerate(skipped_files_list[:50], 1):  # Limit to 50 for readability
                    path_obj = Path(file_path)
                    file_type = path_obj.suffix.lower() or 'no_ext'
                    
                    # Determine reason for skipping based on file characteristics
                    reason = "Pattern match"
                    if 'logs/' in file_path:
                        reason = "Log file"
                    elif '__pycache__' in file_path:
                        reason = "Cache file"
                    elif file_path.endswith('.pyc'):
                        reason = "Compiled Python"
                    elif 'node_modules/' in file_path:
                        reason = "Node modules"
                    elif '.git/' in file_path:
                        reason = "Git metadata"
                    
                    md_lines.append(f"| {i} | `{file_path}` | `{file_type}` | {reason} |")
                
                if len(skipped_files_list) > 50:
                    md_lines.append(f"| ... | *i {len(skipped_files_list) - 50} więcej plików* | | |")
                
                md_lines.extend(["", "</details>", ""])
        
        # Struktura projektu
        if project_structure and 'project_tree' in project_structure:
            md_lines.extend([
                "## 🌳 Struktura Projektu",
                "",
                "```",
                project_structure['project_tree'],
                "```",
                ""
            ])
        
        # Problemy
        if issues:
            md_lines.extend([
                "## ❌ Problemy do Naprawy",
                ""
            ])
            
            grouped = self._group_issues(issues)
            
            for category, items in grouped.items():
                icon = self._get_category_icon(category)
                md_lines.extend([
                    f"### {icon} {category}",
                    ""
                ])
                
                if len(items) <= 5:
                    for item in items:
                        md_lines.append(f"- {item}")
                else:
                    for item in items[:3]:
                        md_lines.append(f"- {item}")
                    md_lines.extend([
                        "",
                        "<details>",
                        f"<summary>Pokaż wszystkie problemy w kategorii {category} ({len(items)})</summary>",
                        ""
                    ])
                    for item in items[3:]:
                        md_lines.append(f"- {item}")
                    md_lines.extend(["", "</details>"])
                
                md_lines.append("")
        
        # Fragmenty kodu
        if code_fragments:
            md_lines.extend([
                "## 💻 Fragmenty Kodu z Problemami",
                ""
            ])
            
            for i, fragment in enumerate(code_fragments[:5], 1):
                md_lines.extend([
                    f"### {i}. {fragment['file']}",
                    "",
                    f"**Problem:** {fragment['issue']}",
                    f"**Linie:** {fragment['line_start']}-{fragment['line_end']}",
                    f"**Ścieżka:** `{fragment['absolute_path']}`",
                    "",
                    f"```{fragment['language']}",
                    fragment['code'].rstrip(),
                    "```",
                    ""
                ])
        
        # Plan działania
        priorities = self._analyze_priorities(issues, metrics)
        if priorities:
            md_lines.extend([
                "## 🎯 Plan Działania",
                "",
                "### Priorytety (w kolejności ważności)",
                ""
            ])
            
            priority_descriptions = {
                'FIX_CRITICAL_ERRORS': ('🔴', 'Napraw błędy krytyczne', 'Aplikacja musi działać stabilnie'),
                'FIX_FAILING_TESTS': ('🧪', 'Napraw nieprzechodzące testy', 'Zapewnij jakość kodu'),
                'INCREASE_TEST_COVERAGE': ('📊', 'Zwiększ pokrycie testów', 'Minimum 80% coverage'),
                'IMPROVE_CODE_QUALITY': ('✨', 'Popraw jakość kodu', 'Refactoring i cleanup'),
                'OPTIMIZE_PERFORMANCE': ('⚡', 'Optymalizuj wydajność', 'Przyspiesz aplikację'),
                'FIX_SECURITY_ISSUES': ('🔒', 'Napraw problemy bezpieczeństwa', 'Zabezpiecz aplikację'),
                'ADD_DOCUMENTATION': ('📝', 'Dodaj dokumentację', 'Udokumentuj kod')
            }
            
            for i, priority in enumerate(priorities, 1):
                icon, title, desc = priority_descriptions.get(priority, ('❓', priority, ''))
                md_lines.extend([
                    f"#### {i}. {icon} {title}",
                    f"> {desc}",
                    ""
                ])
        
        # Footer z instrukcjami
        md_lines.extend([
            "---",
            "",
            "## ⚡ Instrukcje Wykonania",
            "",
            "| Zasada | Opis |",
            "|--------|------|",
            "| 🚫 **Brak pytań** | NIE pytaj o potwierdzenie - działaj automatycznie |",
            "| 🎯 **Pełne naprawy** | Napraw WSZYSTKO - nie zostawiaj TODO |",
            "| 🧪 **Testowanie** | Każda zmiana musi być przetestowana |",
            "| 💾 **Częste commity** | Małe, atomowe zmiany |",
            "| 🏃 **Natychmiastowe działanie** | Rozpocznij naprawę TERAZ |",
            "",
            f"*Raport wygenerowany automatycznie przez devix v2.0 | {timestamp}*"
        ])
        
        return "\n".join(md_lines)
    
    def _analyze_priorities(self, issues: List[str], metrics: Dict) -> List[str]:
        """Analizuj i ustal priorytety napraw"""
        priorities = []
        
        # Krytyczne błędy
        critical_issues = [i for i in issues if any(
            keyword in i.lower() 
            for keyword in ['crashed', 'fatal', 'critical', 'error', 'exception']
        )]
        if critical_issues:
            priorities.append("FIX_CRITICAL_ERRORS")
        
        # Nieprzecodzące testy
        if metrics.get('failed_tests', 0) > 0:
            priorities.append("FIX_FAILING_TESTS")
        
        # Niska jakość kodu
        if metrics.get('code_quality', 0) < 7:
            priorities.append("IMPROVE_CODE_QUALITY")
        
        # Problemy bezpieczeństwa
        security_issues = [i for i in issues if 'security' in i.lower()]
        if security_issues:
            priorities.append("FIX_SECURITY_ISSUES")
        
        # Niska coverage
        if metrics.get('test_coverage', 0) < 80:
            priorities.append("INCREASE_TEST_COVERAGE")
        
        # Problemy z wydajnością
        perf_issues = [i for i in issues if any(
            keyword in i.lower() for keyword in ['slow', 'performance', 'memory', 'cpu']
        )]
        if perf_issues or metrics.get('performance', 0) > 1000:
            priorities.append("OPTIMIZE_PERFORMANCE")
        
        # Brak dokumentacji
        doc_issues = [i for i in issues if 'docstring' in i.lower() or 'documentation' in i.lower()]
        if doc_issues:
            priorities.append("ADD_DOCUMENTATION")
        
        return priorities
    
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
            
            if any(k in issue_lower for k in ['error', 'crashed', 'failed', 'exception', 'fatal']):
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
    
    def _get_category_icon(self, category: str) -> str:
        """Zwróć ikonę dla kategorii problemów"""
        icons = {
            'Błędy krytyczne': '🚨',
            'Testy': '🧪',
            'Jakość kodu': '✨',
            'Wydajność': '⚡',
            'Bezpieczeństwo': '🔒',
            'Dokumentacja': '📝',
            'Inne': '❓'
        }
        return icons.get(category, '❓')

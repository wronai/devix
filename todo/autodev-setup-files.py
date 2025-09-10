# ===== devix/requirements.txt =====
"""
# devix Requirements
# Zależności dla automatycznego systemu rozwoju

# Core
pyyaml>=6.0
pathlib>=1.0

# Monitoring & Testing
pytest>=7.0.0
pytest-cov>=3.0.0
pytest-json-report>=1.5.0

# Code Quality
pylint>=2.15.0
flake8>=5.0.0
black>=22.0.0
radon>=5.1.0
bandit>=1.7.0
safety>=2.3.0

# GUI Automation
pyautogui>=0.9.53
pyperclip>=1.8.2
Pillow>=9.0.0

# System Monitoring
psutil>=5.9.0
docker>=6.0.0

# Web
requests>=2.28.0

# File Watching (dla JetBrains sync)
watchdog>=2.2.0

# XML parsing (dla JetBrains config)
lxml>=4.9.0

# Utilities
python-dotenv>=0.21.0
colorama>=0.4.5
rich>=12.6.0

# Optional - dla lepszej integracji IDE
pywinrm>=0.4.3  # Windows only
python-xlib>=0.31  # Linux only
pyobjc-core>=8.5  # macOS only
"""

# ===== devix/docker-compose.yml =====
"""
version: '3.8'

services:
  devix:
    build: .
    container_name: devix-supervisor
    volumes:
      - ..:/workspace
      - ./logs:/app/logs
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DISPLAY=${DISPLAY}
      - WINDSURF_API_KEY=${WINDSURF_API_KEY}
      - PYTHONUNBUFFERED=1
    network_mode: host
    privileged: true
    command: python supervisor.py --config config.yaml --auto
    restart: unless-stopped
    
  devix-monitor:
    build: .
    container_name: devix-monitor
    volumes:
      - ..:/workspace
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    network_mode: host
    command: python -m monitor
    restart: unless-stopped
"""

# ===== devix/Dockerfile =====
"""
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    make \\
    curl \\
    docker.io \\
    xvfb \\
    x11vnc \\
    scrot \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy devix files
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Set Python path
ENV PYTHONPATH=/workspace:/app

# Entry point
CMD ["python", "supervisor.py"]
"""

# ===== devix/.env.example =====
"""
# devix Environment Variables

# Windsurf/Claude API
WINDSURF_API_KEY=your-api-key-here
WINDSURF_API_URL=http://localhost:8080/api

# GUI Automation
DISPLAY=:0

# Project Settings
PROJECT_PATH=..
MAX_ITERATIONS=50
AUTO_CONTINUE=true

# Thresholds
TEST_COVERAGE_THRESHOLD=80
CODE_QUALITY_THRESHOLD=8.0
PERFORMANCE_THRESHOLD=1000

# Logging
LOG_LEVEL=INFO
"""

# ===== devix/__init__.py =====
"""
#!/usr/bin/env python3
'''
devix - Automatyczny System Rozwoju i Naprawy Kodu
'''

__version__ = '1.0.0'
__author__ = 'Tom Sapletta'

from .supervisor import devixSupervisor
from .monitor import ApplicationMonitor
from .prompter import PromptGenerator
from .windsurf_controller import WindsurfController

__all__ = [
    'devixSupervisor',
    'ApplicationMonitor', 
    'PromptGenerator',
    'WindsurfController'
]
"""

# ===== devix/setup.py =====
"""
#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="devix",
    version="1.0.0",
    author="Tom Sapletta",
    description="Automatyczny system rozwoju i naprawy kodu",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "pytest>=7.0.0",
        "pylint>=2.15.0",
        "pyautogui>=0.9.53",
        "psutil>=5.9.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "devix=devix.supervisor:main",
        ],
    },
)
"""

# ===== devix/run.sh =====
"""
#!/bin/bash
# devix Quick Start Script

set -e

# Colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "${GREEN}🚀 devix - Automatyczny System Rozwoju${NC}"
echo "========================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 nie jest zainstalowany${NC}"
    exit 1
fi

# Check if in devix directory
if [ ! -f "supervisor.py" ]; then
    echo -e "${YELLOW}📁 Przechodzę do katalogu devix...${NC}"
    cd devix 2>/dev/null || { echo -e "${RED}❌ Nie znaleziono katalogu devix${NC}"; exit 1; }
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Tworzę środowisko wirtualne...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Create logs directory
mkdir -p logs

# Parse arguments
MODE="auto"
ITERATIONS=50

while [[ $# -gt 0 ]]; do
    case $1 in
        --manual)
            MODE="manual"
            shift
            ;;
        --monitor)
            MODE="monitor"
            shift
            ;;
        --iterations)
            ITERATIONS="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Run based on mode
case $MODE in
    auto)
        echo -e "${GREEN}🤖 Uruchamianie w trybie AUTO (${ITERATIONS} iteracji)...${NC}"
        python supervisor.py --auto --max-iterations $ITERATIONS
        ;;
    manual)
        echo -e "${YELLOW}👤 Uruchamianie w trybie MANUAL...${NC}"
        python supervisor.py --max-iterations $ITERATIONS
        ;;
    monitor)
        echo -e "${YELLOW}👁️ Uruchamianie w trybie MONITOR...${NC}"
        python -m monitor
        ;;
esac

echo -e "${GREEN}✅ Zakończono${NC}"
"""

# ===== devix/README.md =====
"""
# 🚀 devix - Automatyczny System Rozwoju

Automatyczny system monitorowania, naprawiania i ulepszania kodu z integracją Windsurf/Claude.

## 📋 Funkcje

- ✅ Automatyczne wykrywanie i naprawianie błędów
- 📊 Monitoring testów i pokrycia kodu
- 🔍 Analiza jakości kodu
- ⚡ Optymalizacja wydajności
- 📝 Automatyczne dodawanie dokumentacji
- 🔒 Sprawdzanie bezpieczeństwa
- 🤖 Integracja z Windsurf/Claude

## 🛠️ Instalacja

### Szybki start

```bash
# Klonuj lub skopiuj folder devix do swojego projektu
cp -r devix /path/to/your/project/

# Przejdź do projektu
cd /path/to/your/project

# Uruchom devix
make -C devix run
```

### Instalacja krok po kroku

1. **Skopiuj folder `devix/` do swojego projektu**

2. **Zainstaluj zależności:**
```bash
cd devix
pip install -r requirements.txt
```

3. **Skonfiguruj (opcjonalnie):**
```bash
cp .env.example .env
# Edytuj .env i config.yaml według potrzeb
```

4. **Uruchom:**
```bash
make run
```

## 🎮 Użycie

### Podstawowe komendy

```bash
# Uruchom w trybie auto (pełna automatyzacja)
make run-auto

# Uruchom w trybie manual (wymaga potwierdzenia)
make run-manual

# Tylko monitoruj (bez naprawiania)
make monitor

# Kalibruj GUI automation
make calibrate

# Generuj raport
make report
```

### Użycie z linii poleceń

```bash
# Podstawowe uruchomienie
python devix/supervisor.py

# Z custom config
python devix/supervisor.py --config my-config.yaml

# Określ max iteracji
python devix/supervisor.py --max-iterations 100

# Tryb auto
python devix/supervisor.py --auto
```

### Użycie w Docker

```bash
# Uruchom w Docker
make docker-run

# Zobacz logi
make docker-logs

# Zatrzymaj
make docker-stop
```

## ⚙️ Konfiguracja

### Główne parametry (`config.yaml`)

- `max_iterations`: Maksymalna liczba iteracji napraw
- `test_coverage_threshold`: Minimalny poziom pokrycia testów
- `code_quality_threshold`: Minimalna ocena jakości kodu
- `performance_threshold`: Maksymalny czas odpowiedzi
- `auto_continue`: Automatyczna kontynuacja bez pytania

### Profile projektów

devix zawiera predefiniowane profile dla różnych typów projektów:
- `web_app`: Aplikacje webowe
- `api`: REST API
- `cli_tool`: Narzędzia CLI
- `data_science`: Projekty data science

## 🔧 Integracja z Windsurf/Claude

### Metoda 1: GUI Automation (domyślna)

1. Otwórz Windsurf/VS Code
2. Uruchom kalibrację: `make calibrate`
3. Postępuj zgodnie z instrukcjami

### Metoda 2: API (jeśli dostępne)

1. Ustaw `WINDSURF_API_KEY` w `.env`
2. W `config.yaml` ustaw `use_windsurf_api: true`

### Metoda 3: CLI (jeśli dostępne)

1. Zainstaluj Windsurf CLI
2. W `config.yaml` ustaw `windsurf_path`

## 📊 Monitorowane metryki

- **Testy**: Pokrycie, liczba testów, czas wykonania
- **Jakość kodu**: Pylint score, złożoność cyklomatyczna
- **Wydajność**: Czas odpowiedzi, zużycie pamięci, CPU
- **Bezpieczeństwo**: Vulnerabilities, hardcoded secrets
- **Dokumentacja**: Docstrings, README

## 🚨 Rozwiązywanie problemów

### devix nie widzi Windsurf

1. Sprawdź czy Windsurf jest otwarty
2. Uruchom kalibrację: `make calibrate`
3. Sprawdź logi: `tail -f logs/*.log`

### Testy nie przechodzą

1. Sprawdź czy masz wszystkie zależności projektu
2. Uruchom: `make -C devix monitor` aby zobaczyć szczegóły

### Za wolne działanie

1. Zmniejsz `iteration_delay` w config.yaml
2. Zwiększ `max_iterations`
3. Użyj trybu Docker dla izolacji

## 📝 Przykład workflow

1. **Inicjalizacja projektu:**
```bash
cd my-project
cp -r /path/to/devix .
make -C devix init-project
```

2. **Pierwsza analiza:**
```bash
make -C devix monitor
```

3. **Automatyczna naprawa:**
```bash
make -C devix run-auto
```

4. **Sprawdź wyniki:**
```bash
make -C devix report
```

## 🤝 Wsparcie

- Logi znajdują się w `devix/logs/`
- Raporty JSON w `devix/logs/report_*.json`
- Sprawdź status: `make -C devix status`

## 📄 Licencja

MIT

## 🙏 Credits

Stworzony z ❤️ dla automatyzacji rozwoju oprogramowania.
"""
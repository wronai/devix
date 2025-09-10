#!/bin/bash
# ===== devix/quickstart.sh =====
# devix Quick Start - Automatyczna konfiguracja i uruchomienie

set -e

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║                                                       ║"
echo "║       🚀 devix - Automatyczny Rozwój Kodu 🚀       ║"
echo "║                                                       ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Funkcje pomocnicze
print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Sprawdź gdzie jesteśmy
CURRENT_DIR=$(pwd)
devix_DIR=""
PROJECT_DIR=""

if [ -f "supervisor.py" ]; then
    # Jesteśmy w folderze devix
    devix_DIR=$(pwd)
    PROJECT_DIR=$(dirname "$devix_DIR")
    print_success "Znaleziono devix w: $devix_DIR"
elif [ -d "devix" ]; then
    # Jesteśmy w projekcie z folderem devix
    PROJECT_DIR=$(pwd)
    devix_DIR="$PROJECT_DIR/devix"
    print_success "Znaleziono projekt z devix: $PROJECT_DIR"
else
    # Nie ma devix - zapytaj czy utworzyć
    print_warning "Nie znaleziono devix w bieżącym katalogu"
    echo -e "${YELLOW}Czy chcesz zainstalować devix w tym projekcie? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        PROJECT_DIR=$(pwd)
        devix_DIR="$PROJECT_DIR/devix"
        mkdir -p "$devix_DIR"
        print_success "Tworzę folder devix: $devix_DIR"
        
        # Tutaj normalnie skopiowałbyś pliki devix
        print_warning "Skopiuj pliki devix do $devix_DIR i uruchom ponownie ten skrypt"
        exit 0
    else
        print_error "Anulowano instalację"
        exit 1
    fi
fi

# Menu główne
echo ""
echo -e "${PURPLE}═══════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}                    MENU GŁÓWNE                        ${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "  1) 🚀 Quick Start (Automatyczna konfiguracja)"
echo "  2) 🤖 Uruchom w trybie FULL AUTO"
echo "  3) 👤 Uruchom w trybie MANUAL"
echo "  4) 👁️  Tylko monitoruj (bez naprawiania)"
echo "  5) 🎯 Kalibruj GUI automation"
echo "  6) 📊 Generuj raport"
echo "  7) 🔧 Zaawansowana konfiguracja"
echo "  8) 🐳 Uruchom w Docker"
echo "  9) 🧪 Uruchom testy devix"
echo "  10) 📚 Pokaż dokumentację"
echo "  11) ❌ Wyjdź"
echo ""
echo -n "Wybierz opcję [1-11]: "
read -r choice

case $choice in
    1)
        # Quick Start
        echo ""
        print_step "Quick Start - Automatyczna konfiguracja"
        echo ""
        
        # Sprawdź Python
        print_step "Sprawdzam Python..."
        if command -v python3 &> /dev/null; then
            PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
            print_success "Python $PYTHON_VERSION znaleziony"
        else
            print_error "Python 3 nie jest zainstalowany!"
            echo "Zainstaluj Python 3.8+ i spróbuj ponownie"
            exit 1
        fi
        
        # Sprawdź/utwórz venv
        print_step "Konfiguruję środowisko wirtualne..."
        cd "$devix_DIR"
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            print_success "Utworzono środowisko wirtualne"
        else
            print_success "Środowisko wirtualne już istnieje"
        fi
        
        # Aktywuj venv
        source venv/bin/activate
        
        # Instaluj zależności
        print_step "Instaluję zależności..."
        pip install -q --upgrade pip
        pip install -q -r requirements.txt
        print_success "Zależności zainstalowane"
        
        # Sprawdź strukturę projektu
        print_step "Analizuję projekt..."
        cd "$PROJECT_DIR"
        
        PROJECT_TYPE="unknown"
        if [ -f "manage.py" ]; then
            PROJECT_TYPE="django"
            print_success "Wykryto projekt Django"
        elif [ -f "app.py" ] || [ -f "application.py" ]; then
            PROJECT_TYPE="flask"
            print_success "Wykryto projekt Flask"
        elif [ -f "main.py" ]; then
            PROJECT_TYPE="python"
            print_success "Wykryto projekt Python"
        elif [ -f "package.json" ]; then
            PROJECT_TYPE="nodejs"
            print_success "Wykryto projekt Node.js"
        else
            print_warning "Nieznany typ projektu - używam domyślnej konfiguracji"
        fi
        
        # Generuj konfigurację
        print_step "Generuję konfigurację dla typu: $PROJECT_TYPE..."
        
        cat > "$devix_DIR/config.yaml" << EOF
# devix Configuration - Generated for $PROJECT_TYPE
max_iterations: 50
iteration_delay: 30
auto_continue: true
log_level: INFO

test_coverage_threshold: 80
code_quality_threshold: 8.0
performance_threshold: 1000

test_command: pytest
run_command: python main.py
docker_compose_file: docker-compose.yml

error_patterns:
  - error
  - exception
  - failed
  - critical

improvement_goals:
  add_logging: true
  add_tests: true
  add_error_handling: true
  add_documentation: true
  refactor_long_functions: true
  add_type_hints: true
  optimize_performance: true
EOF
        
        print_success "Konfiguracja wygenerowana"
        
        # Utwórz przykładowe testy jeśli nie ma
        if [ ! -d "$PROJECT_DIR/tests" ]; then
            print_step "Tworzę folder tests..."
            mkdir -p "$PROJECT_DIR/tests"
            echo "def test_placeholder():" > "$PROJECT_DIR/tests/test_basic.py"
            echo "    assert True" >> "$PROJECT_DIR/tests/test_basic.py"
            print_success "Utworzono podstawowe testy"
        fi
        
        # Pytanie o uruchomienie
        echo ""
        echo -e "${GREEN}✅ Konfiguracja zakończona!${NC}"
        echo ""
        echo -e "${YELLOW}Czy chcesz teraz uruchomić devix? (y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_step "Uruchamiam devix..."
            cd "$PROJECT_DIR"
            python "$devix_DIR/supervisor.py" --config "$devix_DIR/config.yaml" --auto
        else
            echo ""
            echo "Aby uruchomić devix później, użyj:"
            echo -e "${CYAN}  cd $PROJECT_DIR${NC}"
            echo -e "${CYAN}  python $devix_DIR/supervisor.py${NC}"
        fi
        ;;
        
    2)
        # Full Auto
        print_step "Uruchamianie w trybie FULL AUTO..."
        cd "$PROJECT_DIR"
        source "$devix_DIR/venv/bin/activate" 2>/dev/null || true
        python "$devix_DIR/supervisor.py" --config "$devix_DIR/config.yaml" --auto --max-iterations 100
        ;;
        
    3)
        # Manual
        print_step "Uruchamianie w trybie MANUAL..."
        cd "$PROJECT_DIR"
        source "$devix_DIR/venv/bin/activate" 2>/dev/null || true
        python "$devix_DIR/supervisor.py" --config "$devix_DIR/config.yaml" --max-iterations 10
        ;;
        
    4)
        # Monitor only
        print_step "Uruchamianie trybu MONITOR..."
        cd "$PROJECT_DIR"
        source "$devix_DIR/venv/bin/activate" 2>/dev/null || true
        python -c "
from devix.monitor import ApplicationMonitor
import yaml
import json
from pathlib import Path

config_path = Path('$devix_DIR/config.yaml')
if config_path.exists():
    with open(config_path) as f:
        config = yaml.safe_load(f)
else:
    config = {}

monitor = ApplicationMonitor('.', config)
issues, metrics = monitor.check_all()

print('\\n📊 WYNIKI MONITORINGU:')
print('=' * 50)
print(f'Znaleziono {len(issues)} problemów')
print('\\nMetryki:')
for key, value in metrics.items():
    print(f'  {key}: {value}')
print('\\nProblemy:')
for i, issue in enumerate(issues[:10], 1):
    print(f'  {i}. {issue}')
if len(issues) > 10:
    print(f'  ... i {len(issues)-10} więcej')
"
        ;;
        
    5)
        # Kalibracja GUI
        print_step "Uruchamianie kalibracji GUI..."
        cd "$devix_DIR"
        source venv/bin/activate 2>/dev/null || true
        python windsurf_controller.py calibrate
        ;;
        
    6)
        # Raport
        print_step "Generowanie raportu..."
        cd "$devix_DIR"
        if ls logs/report_*.json 1> /dev/null 2>&1; then
            LATEST_REPORT=$(ls -t logs/report_*.json | head -1)
            echo ""
            echo -e "${CYAN}📊 NAJNOWSZY RAPORT: $LATEST_REPORT${NC}"
            echo "=" 
            python -m json.tool "$LATEST_REPORT"
        else
            print_warning "Brak raportów do wyświetlenia"
            echo "Uruchom devix przynajmniej raz aby wygenerować raport"
        fi
        ;;
        
    7)
        # Zaawansowana konfiguracja
        echo ""
        echo -e "${PURPLE}ZAAWANSOWANA KONFIGURACJA${NC}"
        echo ""
        echo "1) Edytuj config.yaml"
        echo "2) Ustaw zmienne środowiskowe"
        echo "3) Wybierz profil projektu"
        echo "4) Konfiguruj integrację z Windsurf"
        echo "5) Powrót"
        echo ""
        echo -n "Wybierz [1-5]: "
        read -r config_choice
        
        case $config_choice in
            1)
                ${EDITOR:-nano} "$devix_DIR/config.yaml"
                ;;
            2)
                if [ ! -f "$devix_DIR/.env" ]; then
                    cp "$devix_DIR/.env.example" "$devix_DIR/.env" 2>/dev/null || true
                fi
                ${EDITOR:-nano} "$devix_DIR/.env"
                ;;
            3)
                echo "Dostępne profile:"
                echo "  1) web_app - Aplikacje webowe"
                echo "  2) api - REST API" 
                echo "  3) cli_tool - Narzędzia CLI"
                echo "  4) data_science - Projekty ML/DS"
                echo -n "Wybierz profil [1-4]: "
                read -r profile_choice
                # Tu dodaj logikę wyboru profilu
                ;;
            4)
                echo "Konfiguracja Windsurf:"
                echo "  1) Użyj GUI automation (domyślne)"
                echo "  2) Użyj API (wymaga klucza)"
                echo "  3) Użyj CLI"
                echo -n "Wybierz [1-3]: "
                read -r windsurf_choice
                # Tu dodaj logikę konfiguracji
                ;;
            5)
                echo ""
                echo -e "${BLUE}KONFIGURACJA JETBRAINS IDE${NC}"
                echo ""
                
                # Wykryj zainstalowane IDE
                print_step "Wykrywanie zainstalowanych IDE JetBrains..."
                
                DETECTED_IDES=""
                if command -v pycharm &> /dev/null || [ -d "/Applications/PyCharm.app" ] || [ -d "$HOME/.local/share/JetBrains/Toolbox/apps/PyCharm" ]; then
                    DETECTED_IDES="${DETECTED_IDES}PyCharm "
                    print_success "Znaleziono PyCharm"
                fi
                if command -v idea &> /dev/null || [ -d "/Applications/IntelliJ IDEA.app" ] || [ -d "$HOME/.local/share/JetBrains/Toolbox/apps/IDEA" ]; then
                    DETECTED_IDES="${DETECTED_IDES}IntelliJ "
                    print_success "Znaleziono IntelliJ IDEA"
                fi
                if command -v webstorm &> /dev/null || [ -d "/Applications/WebStorm.app" ] || [ -d "$HOME/.local/share/JetBrains/Toolbox/apps/WebStorm" ]; then
                    DETECTED_IDES="${DETECTED_IDES}WebStorm "
                    print_success "Znaleziono WebStorm"
                fi
                
                if [ -z "$DETECTED_IDES" ]; then
                    print_warning "Nie znaleziono zainstalowanych IDE JetBrains"
                    echo "Zalecane: Zainstaluj PyCharm z https://www.jetbrains.com/pycharm/"
                else
                    echo ""
                    echo "Wybierz główne IDE:"
                    echo "  1) PyCharm"
                    echo "  2) IntelliJ IDEA"
                    echo "  3) WebStorm"
                    echo "  4) PhpStorm"
                    echo "  5) GoLand"
                    echo "  6) Auto-detect"
                    echo -n "Wybierz [1-6]: "
                    read -r ide_choice
                    
                    case $ide_choice in
                        1) IDE_TYPE="pycharm" ;;
                        2) IDE_TYPE="intellij" ;;
                        3) IDE_TYPE="webstorm" ;;
                        4) IDE_TYPE="phpstorm" ;;
                        5) IDE_TYPE="goland" ;;
                        *) IDE_TYPE="auto" ;;
                    esac
                    
                    # Zapisz do config
                    cat >> "$devix_DIR/config.yaml" << EOF

# JetBrains IDE Configuration (generated)
ide_type: $IDE_TYPE
jetbrains_integration:
  jetbrains_ide: $IDE_TYPE
  use_inspections: true
  use_quick_fixes: true
  sync_on_save: true
EOF
                    print_success "Konfiguracja JetBrains zapisana"
                    
                    # Test połączenia
                    echo ""
                    print_step "Testowanie połączenia z IDE..."
                    cd "$devix_DIR"
                    if python jetbrains_controller.py test 2>/dev/null; then
                        print_success "Połączenie z IDE działa!"
                        
                        # Instalacja wtyczki
                        echo ""
                        echo -e "${YELLOW}Czy chcesz zainstalować wtyczkę devix w IDE? (zalecane) (y/n)${NC}"
                        read -r install_plugin
                        if [[ "$install_plugin" =~ ^[Yy]$ ]]; then
                            print_step "Instalowanie wtyczki..."
                            if [ -f "jetbrains-plugin/install.sh" ]; then
                                bash jetbrains-plugin/install.sh
                            else
                                print_warning "Instalator wtyczki niedostępny"
                                echo "Zainstaluj ręcznie: Settings → Plugins → Install from disk"
                            fi
                        fi
                    else
                        print_warning "Nie można połączyć z IDE"
                        echo "Upewnij się że IDE jest uruchomione i spróbuj ponownie"
                    fi
                fi
                ;;
            6)
                # Powrót do menu
                exec "$0"
                ;;
        esac
        ;;
        
    8)
        # Docker
        print_step "Uruchamianie w Docker..."
        cd "$devix_DIR"
        docker-compose up -d
        echo ""
        print_success "devix uruchomiony w Docker"
        echo "Zobacz logi: docker-compose logs -f"
        echo "Zatrzymaj: docker-compose down"
        ;;
        
    9)
        # Testy
        print_step "Uruchamianie testów devix..."
        cd "$devix_DIR"
        source venv/bin/activate 2>/dev/null || true
        pytest tests/ -v --cov=. --cov-report=term
        ;;
        
    10)
        # Dokumentacja
        echo ""
        less "$devix_DIR/README.md"
        ;;
        
    11)
        print_success "Do widzenia!"
        exit 0
        ;;
        
    *)
        print_error "Nieprawidłowy wybór"
        exit 1
        ;;
esac

echo ""
print_success "Gotowe!"
echo ""
echo -e "${CYAN}Wskazówki:${NC}"
echo "  • Logi znajdują się w: $devix_DIR/logs/"
echo "  • Konfiguracja w: $devix_DIR/config.yaml"
echo "  • Uruchom ponownie: $0"
echo ""
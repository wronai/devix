# 🔧 devix - Integracja z JetBrains IDE

## 📋 Wspierane IDE

- ✅ **PyCharm** (Professional & Community)
- ✅ **IntelliJ IDEA** (Ultimate & Community)
- ✅ **WebStorm**
- ✅ **PhpStorm**
- ✅ **GoLand**
- ✅ **Rider**
- ✅ **CLion**
- ✅ **RubyMine**

## 🚀 Szybki Start

### 1. **Automatyczna konfiguracja**

```bash
cd twoj-projekt/
./devix/quickstart.sh
# Wybierz opcję: "JetBrains Integration Setup"
```

### 2. **Manualna konfiguracja**

#### Krok 1: Edytuj `devix/config.yaml`

```yaml
# Wybierz swoje IDE
ide_type: pycharm  # lub: intellij, webstorm, auto, both

# Konfiguracja JetBrains
jetbrains_integration:
  jetbrains_ide: pycharm
  jetbrains_ai_assistant: true  # Jeśli masz licencję
  use_inspections: true
  use_quick_fixes: true
```

#### Krok 2: Uruchom kalibrację

```bash
python devix/jetbrains_controller.py test
```

#### Krok 3: Uruchom devix

```bash
make -C devix run-auto
```

## 🎯 Metody Integracji

### **1. HTTP API (Zalecana)**

Zainstaluj wtyczkę devix w JetBrains:

1. Otwórz PyCharm/IntelliJ
2. Settings → Plugins → Marketplace
3. Szukaj "devix Integration" (lub zainstaluj ręcznie)
4. Restart IDE

### **2. External Tools**

devix automatycznie utworzy External Tool:

1. Settings → Tools → External Tools
2. devix powinien pojawić się automatycznie
3. Możesz przypisać skrót klawiszowy

### **3. File Watchers**

Automatyczna synchronizacja przy zapisie:

1. Settings → Tools → File Watchers
2. devix Watcher będzie dodany automatycznie
3. Każda zmiana pliku `.py` triggeruje analizę

### **4. GUI Automation**

Jeśli inne metody nie działają:

```bash
# Kalibruj pozycje przycisków
python devix/jetbrains_controller.py calibrate
```

## 📊 Funkcje Specyficzne dla IDE

### **PyCharm**

```python
# W config.yaml
jetbrains_integration:
  jetbrains_ide: pycharm
  pycharm_specific:
    run_pytest: true
    profile_code: true
    django_support: true
    jupyter_support: true
```

**Dodatkowe funkcje:**
- Automatyczne uruchamianie pytest
- Profilowanie wydajności
- Integracja z Django
- Wsparcie dla Jupyter notebooks

### **IntelliJ IDEA**

```python
# W config.yaml
jetbrains_integration:
  jetbrains_ide: intellij
  intellij_specific:
    maven_integration: true
    gradle_integration: true
    spring_support: true
```

**Dodatkowe funkcje:**
- Maven/Gradle build automation
- Spring framework support
- Database tools integration

### **WebStorm**

```python
# W config.yaml
jetbrains_integration:
  jetbrains_ide: webstorm
  webstorm_specific:
    npm_scripts: true
    eslint_integration: true
    typescript_support: true
```

**Dodatkowe funkcje:**
- NPM scripts automation
- ESLint/Prettier integration
- TypeScript refactoring

## 🔄 Synchronizacja Dwukierunkowa

### **IDE → devix**

Zmiany w IDE są automatycznie wykrywane przez:
- File system watchers
- Git hooks
- IDE server protocol

### **devix → IDE**

devix wysyła zmiany do IDE przez:
- Quick fixes
- Refactoring actions
- Code generation
- Format & optimize

## 🤖 AI Assistant Integration

Jeśli masz JetBrains AI Assistant:

```yaml
jetbrains_integration:
  jetbrains_ai_assistant: true
  ai_settings:
    auto_complete: true
    auto_refactor: true
    explain_errors: true
    generate_tests: true
```

devix będzie współpracował z AI Assistant dla lepszych rezultatów.

## ⚙️ Zaawansowane Opcje

### **Custom Inspection Profiles**

```yaml
jetbrains_integration:
  inspections:
    - MyCustomProfile
    - StrictCodeQuality
```

### **Skróty Klawiszowe**

```yaml
jetbrains_integration:
  shortcuts:
    custom_action: ['ctrl', 'alt', 'shift', 'a']
```

### **Automatyczne Akcje**

```yaml
jetbrains_integration:
  auto_actions:
    before_fix:
      - optimize_imports
      - format_code
    after_fix:
      - run_tests
      - update_documentation
```

## 📝 Przykłady Użycia

### **Przykład 1: Automatyczna naprawa z PyCharm**

```bash
# Uruchom devix z PyCharm
cd moj-projekt/
echo "ide_type: pycharm" >> devix/config.yaml
make -C devix run-auto
```

devix będzie:
1. Wykrywał błędy przez PyCharm inspections
2. Generował prompty do naprawy
3. Aplikował quick fixes
4. Formatował kod
5. Uruchamiał testy

### **Przykład 2: Profiling i Optymalizacja**

```python
# W config.yaml
jetbrains_integration:
  profile_code: true
  auto_actions:
    optimize_performance: true
```

```bash
# Uruchom profiling
python devix/jetbrains_controller.py profile
```

### **Przykład 3: Współpraca IDE**

```yaml
# Użyj PyCharm dla analizy, Windsurf dla AI
ide_type: both

jetbrains_integration:
  jetbrains_ide: pycharm
  use_inspections: true

windsurf_integration:
  use_windsurf_api: true
```

## 🛠️ Troubleshooting

### **Problem: IDE nie jest wykrywane**

```bash
# Sprawdź czy IDE działa
python devix/jetbrains_controller.py test

# Ustaw ręcznie ścieżkę
export PYCHARM_PATH="/Applications/PyCharm.app/Contents/MacOS/pycharm"
```

### **Problem: HTTP API nie działa**

1. Sprawdź czy port jest wolny:
```bash
lsof -i :63342
```

2. Restart IDE z włączonym API:
```bash
pycharm --api-port=63342
```

### **Problem: GUI automation nie działa**

```bash
# Re-kalibruj
python devix/jetbrains_controller.py calibrate

# Lub wyłącz w config:
jetbrains_integration:
  communication_methods:
    - external_tool  # Użyj tylko external tools
    # - gui_automation  # Wyłącz GUI
```

## 📊 Metryki i Raporty

devix z JetBrains zbiera dodatkowe metryki:

- **Code Inspections**: Liczba warnings/errors z IDE
- **Quick Fixes Applied**: Automatyczne naprawy
- **Refactorings**: Wykonane refaktoryzacje
- **Test Coverage**: Z IDE test runner
- **Performance Profiling**: CPU/Memory hotspots

```bash
# Zobacz raport
make -C devix report-jetbrains
```

## 🔗 Integracja z CI/CD

```yaml
# .github/workflows/devix.yml
name: devix with JetBrains

on: [push, pull_request]

jobs:
  devix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup JetBrains IDE
        run: |
          snap install pycharm-community --classic
          
      - name: Run devix
        run: |
          cd devix
          python supervisor.py --ide=pycharm --max-iterations=10
```

## 💡 Best Practices

1. **Używaj inspection profiles** dostosowanych do projektu
2. **Włącz file watchers** dla real-time sync
3. **Skonfiguruj quick fixes** dla common issues
4. **Używaj AI Assistant** jeśli dostępny
5. **Profile przed optymalizacją** dla data-driven fixes

## 🚀 Workflow Przykłady

### **Development Workflow**

```bash
# Morning standup
make -C devix status-jetbrains

# Active development
make -C devix watch-jetbrains

# Before commit
make -C devix validate-jetbrains

# Night optimization
make -C devix optimize-jetbrains
```

### **Team Workflow**

```yaml
# Shared team config
team_config:
  ide_type: jetbrains
  jetbrains_integration:
    inspections:
      - TeamCodeStyle
      - SecurityAudit
    auto_actions:
      enforce_style: true
      check_security: true
```

## 📚 Dokumentacja IDE

- [PyCharm Documentation](https://www.jetbrains.com/pycharm/docs/)
- [IntelliJ Platform SDK](https://plugins.jetbrains.com/docs/intellij/)
- [External Tools](https://www.jetbrains.com/help/pycharm/external-tools.html)
- [File Watchers](https://www.jetbrains.com/help/pycharm/file-watchers.html)

---

**💡 Pro Tip:** Dla najlepszych rezultatów używaj `ide_type: both` aby wykorzystać analizę JetBrains i AI z Windsurf/Claude jednocześnie!
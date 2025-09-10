# 🔧 devix JetBrains - Troubleshooting Guide

## ❌ Częste problemy i rozwiązania

### **Problem: IDE nie jest wykrywane**

#### Symptomy:
```
❌ IDE not found
❌ Could not connect to JetBrains IDE
```

#### Rozwiązania:

**1. Sprawdź czy IDE jest uruchomione:**
```bash
# Linux/Mac
ps aux | grep -i pycharm
ps aux | grep -i idea

# Windows
tasklist | findstr pycharm
```

**2. Ustaw ścieżkę ręcznie:**
```bash
# Linux
export PYCHARM_PATH="/opt/pycharm/bin/pycharm.sh"

# Mac
export PYCHARM_PATH="/Applications/PyCharm.app/Contents/MacOS/pycharm"

# Windows
set PYCHARM_PATH="C:\Program Files\JetBrains\PyCharm\bin\pycharm64.exe"
```

**3. Sprawdź instalację Toolbox:**
```bash
# JetBrains Toolbox instaluje IDE w niestandardowych lokalizacjach
find ~ -name "pycharm*" 2>/dev/null
```

---

### **Problem: HTTP API nie działa**

#### Symptomy:
```
Connection refused on port 63342
HTTP API timeout
```

#### Rozwiązania:

**1. Włącz REST API w IDE:**
- Settings → Build, Execution, Deployment → Debugger
- Enable "Allow unsigned requests"
- Restart IDE

**2. Sprawdź czy port jest zajęty:**
```bash
# Linux/Mac
lsof -i :63342
netstat -an | grep 63342

# Windows
netstat -an | findstr 63342
```

**3. Zmień port w konfiguracji:**
```yaml
jetbrains_integration:
  jetbrains_http_port: 63343  # Użyj innego portu
```

**4. Firewall/Antivirus:**
- Dodaj wyjątek dla portów 63342-63343
- Dodaj PyCharm/IntelliJ do wyjątków firewall

---

### **Problem: GUI Automation nie działa**

#### Symptomy:
```
pyautogui.FailSafeException
Could not locate button/window
```

#### Rozwiązania:

**1. Wyłącz failsafe (tymczasowo):**
```python
import pyautogui
pyautogui.FAILSAFE = False
```

**2. Re-kalibracja:**
```bash
python devix/jetbrains_controller.py calibrate
```

**3. Sprawdź rozdzielczość:**
```python
# Dostosuj do swojego ekranu
pyautogui.size()  # Powinno zwrócić właściwą rozdzielczość
```

**4. Uprawnienia (Mac):**
- System Preferences → Security & Privacy → Privacy → Accessibility
- Dodaj Terminal/Python do listy

**5. Uprawnienia (Linux):**
```bash
# Może wymagać xhost
xhost +local:
```

---

### **Problem: File Watcher nie działa**

#### Symptomy:
```
File changes not detected
Sync not working
```

#### Rozwiązania:

**1. Sprawdź konfigurację File Watchers:**
- Settings → Tools → File Watchers
- Upewnij się że devix watcher jest włączony

**2. Zwiększ limit inotify (Linux):**
```bash
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**3. Wyczyść cache IDE:**
- File → Invalidate Caches and Restart

---

### **Problem: Inspection nie znajduje błędów**

#### Symptomy:
```
No issues found but code has problems
Empty inspection results
```

#### Rozwiązania:

**1. Sprawdź profil inspekcji:**
```bash
# Lista dostępnych profili
ls ~/.config/JetBrains/PyCharm*/inspection/
```

**2. Utwórz custom profile:**
- Settings → Editor → Inspections
- Utwórz nowy profil "devix"
- Włącz wszystkie relevant inspections
- Zapisz i użyj w config.yaml

**3. Uruchom ręcznie:**
```bash
pycharm inspect /path/to/project /path/to/profile /tmp/results
```

---

### **Problem: Quick Fixes nie są aplikowane**

#### Symptomy:
```
Quick fix failed
Changes not applied
```

#### Rozwiązania:

**1. Sprawdź uprawnienia do plików:**
```bash
# Upewnij się że pliki są writable
chmod -R u+w src/
```

**2. Wyłącz Safe Write:**
- Settings → Appearance & Behavior → System Settings
- Uncheck "Use safe write"

**3. Sprawdź czy IDE nie jest w Read-Only mode:**
- Kliknij na lock icon w status bar
- Toggle read-only mode

---

### **Problem: Wtyczka devix nie instaluje się**

#### Symptomy:
```
Plugin installation failed
Plugin not compatible
```

#### Rozwiązania:

**1. Instalacja ręczna:**
```bash
# Znajdź folder plugins
# Mac
cd ~/Library/Application\ Support/JetBrains/PyCharm*/plugins/

# Linux
cd ~/.local/share/JetBrains/PyCharm*/plugins/

# Windows
cd %APPDATA%\JetBrains\PyCharm*\plugins\

# Skopiuj wtyczkę
cp -r /path/to/devix/jetbrains-plugin ./devix
```

**2. Sprawdź kompatybilność:**
- Upewnij się że wersja IDE >= 2020.3
- Sprawdź build number: Help → About

**3. Install from disk:**
- Settings → Plugins → ⚙️ → Install Plugin from Disk
- Wybierz devix-plugin.zip

---

### **Problem: Performance issues**

#### Symptomy:
```
IDE bardzo wolne podczas devix
High CPU/Memory usage
```

#### Rozwiązania:

**1. Zwiększ pamięć dla IDE:**
```bash
# Edit vmoptions
# Help → Edit Custom VM Options
-Xmx4096m
-Xms1024m
```

**2. Wyłącz niepotrzebne plugins:**
- Settings → Plugins
- Disable unused plugins

**3. Ogranicz scope analizy:**
```yaml
jetbrains_integration:
  inspection_scope: src/  # Tylko folder src
  exclude_folders:
    - node_modules
    - venv
    - .git
```

---

### **Problem: Synchronizacja z Git nie działa**

#### Symptomy:
```
Git hooks not triggered
Changes not committed
```

#### Rozwiązania:

**1. Sprawdź Git hooks:**
```bash
ls -la .git/hooks/
# Powinny być executable
chmod +x .git/hooks/pre-commit
```

**2. Bypass hooks tymczasowo:**
```bash
git commit --no-verify
```

**3. Debug hook:**
```bash
bash -x .git/hooks/pre-commit
```

---

## 🐛 Debugging devix z JetBrains

### **Enable Debug Mode:**

```yaml
# config.yaml
log_level: DEBUG
jetbrains_integration:
  debug_mode: true
  verbose_output: true
```

### **Debug Logs:**

```bash
# Tail logs
tail -f devix/logs/*.log

# Filter JetBrains logs
grep -i jetbrains devix/logs/*.log

# Watch specific component
tail -f devix/logs/*.log | grep -i "jetbrains_controller"
```

### **Test Connection Manually:**

```python
# Test script
from devix.jetbrains_controller import get_jetbrains_controller

config = {
    'jetbrains_ide': 'pycharm',
    'jetbrains_http_port': 63342
}

controller = get_jetbrains_controller(config)

# Test różnych metod
print("Testing IDE detection:", controller.ide_type)
print("IDE Path:", controller.ide_path)
print("Focus window:", controller._focus_ide_window())
print("HTTP API:", controller._send_via_http_api("test", "test"))
```

### **Network Debugging:**

```bash
# Check ports
curl -v http://localhost:63342/api/about

# Test with netcat
nc -zv localhost 63342

# Wireshark/tcpdump
sudo tcpdump -i lo port 63342
```

---

## 🔍 Diagnostyka

### **Run Full Diagnostic:**

```bash
# Diagnostic script
cat > devix/diagnose.sh << 'EOF'
#!/bin/bash
echo "=== devix JetBrains Diagnostic ==="
echo ""

echo "1. Checking IDE processes..."
ps aux | grep -E "(pycharm|idea|webstorm|phpstorm)" | grep -v grep

echo ""
echo "2. Checking ports..."
netstat -an | grep -E "(63342|63343)"

echo ""
echo "3. Checking Python modules..."
python -c "import pyautogui, psutil, requests, watchdog; print('✓ All modules installed')"

echo ""
echo "4. Checking IDE paths..."
for ide in pycharm idea webstorm; do
    which $ide 2>/dev/null && echo "✓ $ide found"
done

echo ""
echo "5. Testing devix connection..."
python devix/jetbrains_controller.py test

echo ""
echo "=== Diagnostic Complete ==="
EOF

chmod +x devix/diagnose.sh
./devix/diagnose.sh
```

---

## 📞 Getting Help

### **Logi do załączenia przy zgłaszaniu problemu:**

```bash
# Zbierz logi
tar -czf devix-debug.tar.gz \
  devix/logs/*.log \
  devix/config.yaml \
  .idea/workspace.xml
```

### **Informacje systemowe:**

```bash
# System info
uname -a
python --version
pip list | grep -E "(pyautogui|psutil|watchdog)"

# IDE info
pycharm --version 2>/dev/null || echo "PyCharm not in PATH"
```

### **Sprawdź znaną issues:**

1. GitHub Issues: `https://github.com/devix/issues`
2. JetBrains YouTrack
3. Stack Overflow tag: `devix-jetbrains`

---

## ✅ Checklist przed uruchomieniem

- [ ] IDE jest uruchomione
- [ ] Projekt otwarty w IDE
- [ ] Python 3.8+ zainstalowany
- [ ] Wszystkie dependencies zainstalowane
- [ ] Uprawnienia do modyfikacji plików
- [ ] Porty 63342-63343 wolne
- [ ] Dla GUI automation: uprawnienia accessibility
- [ ] Dla File Watchers: inotify limits (Linux)
- [ ] Backup projektu zrobiony

---

## 🆘 Emergency Recovery

Jeśli devix zepsuł kod:

```bash
# 1. Zatrzymaj devix
pkill -f devix

# 2. Revert changes
git reset --hard HEAD

# 3. Lub użyj IDE local history
# Right click → Local History → Show History

# 4. Disable auto mode
echo "auto_continue: false" >> devix/config.yaml

# 5. Run in safe mode
make -C devix monitor  # Tylko monitoruj, nie naprawiaj
```
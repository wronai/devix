# 🚀 devix Workflows - Przykłady dla różnych projektów

## 📐 Python + PyCharm Workflow

### **1. Nowy projekt Python**

```bash
# Krok 1: Inicjalizacja projektu
mkdir my-python-app && cd my-python-app
python -m venv venv
source venv/bin/activate
pip install flask pytest pytest-cov pylint black

# Krok 2: Skopiuj devix
cp -r /path/to/devix .

# Krok 3: Konfiguracja dla PyCharm
cat > devix/config.yaml << EOF
ide_type: pycharm
project_type: python_web

jetbrains_integration:
  jetbrains_ide: pycharm
  use_inspections: true
  use_quick_fixes: true
  
  pycharm_specific:
    pytest_integration: true
    flask_support: true
    virtualenv_path: "../venv"

test_coverage_threshold: 90
code_quality_threshold: 9.0
EOF

# Krok 4: Otwórz w PyCharm
pycharm .

# Krok 5: Uruchom devix
make -C devix pycharm
```

### **2. Istniejący projekt z problemami**

```bash
cd problematic-project/

# Quick fix wszystkich problemów
./devix/quickstart.sh
# Wybierz: "1" (Quick Start)
# Wybierz: "PyCharm" gdy zapyta o IDE

# devix automatycznie:
# - Wykryje wszystkie błędy przez PyCharm inspections
# - Naprawi importy
# - Doda brakujące testy
# - Poprawi formatowanie
# - Doda type hints
```

### **3. Nocna optymalizacja**

```bash
# Setup dla nocnej optymalizacji
cat > devix/night-config.yaml << EOF
ide_type: pycharm
max_iterations: 500
iteration_delay: 10

jetbrains_integration:
  profile_code: true
  optimize_performance: true
  
schedule:
  night_mode:
    enabled: true
    start_hour: 22
    end_hour: 6
    
improvement_goals:
  optimize_algorithms: true
  reduce_complexity: true
  add_caching: true
  parallelize_operations: true
EOF

# Uruchom o 22:00
echo "0 22 * * * cd $(pwd) && make -C devix optimize-jetbrains" | crontab -l
```

---

## ☕ Java + IntelliJ IDEA Workflow

### **1. Spring Boot Project**

```bash
cd spring-boot-app/

# Konfiguracja dla IntelliJ
cat > devix/config.yaml << EOF
ide_type: intellij
project_type: spring_boot

jetbrains_integration:
  jetbrains_ide: intellij
  
  intellij_specific:
    maven_integration: true
    spring_support: true
    database_tools: true
    
test_command: mvn test
run_command: mvn spring-boot:run
build_command: mvn clean package
EOF

# Uruchom z IntelliJ
make -C devix intellij
```

### **2. Microservices Workflow**

```bash
# Dla każdego microservice
for service in auth-service user-service payment-service; do
  cd $service
  cp -r ../devix .
  
  # Specific config dla microservice
  echo "service_name: $service" >> devix/config.yaml
  
  # Uruchom devix w tle
  nohup make -C devix run-auto &
  
  cd ..
done

# Monitor wszystkich
make -C devix monitor-all
```

---

## 🌐 JavaScript/TypeScript + WebStorm Workflow

### **1. React Application**

```bash
cd react-app/

# Setup dla WebStorm + React
cat > devix/config.yaml << EOF
ide_type: webstorm
project_type: react

jetbrains_integration:
  jetbrains_ide: webstorm
  
  webstorm_specific:
    npm_scripts: true
    eslint_integration: true
    prettier_integration: true
    typescript_support: true
    jest_integration: true
    
test_command: npm test
run_command: npm start
build_command: npm run build
lint_command: npm run lint
EOF

# Integracja z npm scripts
npm install --save-dev devix-npm-bridge

# package.json
{
  "scripts": {
    "devix": "make -C devix webstorm",
    "devix:fix": "make -C devix run-auto",
    "devix:watch": "make -C devix watch-jetbrains"
  }
}

# Uruchom
npm run devix
```

### **2. Node.js Backend**

```bash
cd node-backend/

# Express + TypeScript setup
cat > devix/config.yaml << EOF
ide_type: webstorm
project_type: node_backend

jetbrains_integration:
  webstorm_specific:
    node_debugging: true
    npm_scripts: true
    typescript_support: true
    
error_patterns:
  - "TypeError"
  - "ReferenceError"
  - "SyntaxError"
  - "UnhandledPromiseRejection"
  
improvement_goals:
  add_error_middleware: true
  add_validation: true
  add_rate_limiting: true
  add_cors_config: true
EOF

make -C devix webstorm
```

---

## 🐘 PHP + PhpStorm Workflow

### **1. Laravel Project**

```bash
cd laravel-app/

cat > devix/config.yaml << EOF
ide_type: phpstorm
project_type: laravel

jetbrains_integration:
  jetbrains_ide: phpstorm
  
  phpstorm_specific:
    composer_integration: true
    phpunit_integration: true
    laravel_support: true
    database_tools: true
    
test_command: php artisan test
run_command: php artisan serve
migrate_command: php artisan migrate
EOF

make -C devix run-auto
```

---

## 🚦 Go + GoLand Workflow

### **1. Go Microservice**

```bash
cd go-service/

cat > devix/config.yaml << EOF
ide_type: goland
project_type: go_service

jetbrains_integration:
  jetbrains_ide: goland
  
  goland_specific:
    go_modules: true
    goroutine_debugging: true
    benchmarking: true
    
test_command: go test ./...
run_command: go run main.go
build_command: go build -o app
bench_command: go test -bench=.
EOF

make -C devix run-auto
```

---

## 🎯 Multi-IDE Workflow (Both)

### **Używanie PyCharm + Windsurf razem**

```bash
# Konfiguracja dla obu IDE
cat > devix/config.yaml << EOF
ide_type: both

# PyCharm dla analizy i refactoringu
jetbrains_integration:
  jetbrains_ide: pycharm
  use_inspections: true
  use_quick_fixes: true
  profile_code: true
  
# Windsurf/Claude dla AI-powered fixes
windsurf_integration:
  use_windsurf_api: true
  
# Podział zadań
task_delegation:
  jetbrains:
    - code_analysis
    - refactoring
    - performance_profiling
    - debugging
  windsurf:
    - complex_fixes
    - test_generation
    - documentation_generation
    - ai_suggestions
EOF

# Uruchom z oboma
make -C devix run-both
```

---

## 📊 Data Science Workflow

### **Jupyter + PyCharm Professional**

```bash
cd data-science-project/

cat > devix/config.yaml << EOF
ide_type: pycharm
project_type: data_science

jetbrains_integration:
  pycharm_specific:
    scientific_mode: true
    jupyter_support: true
    pandas_support: true
    matplotlib_support: true
    
improvement_goals:
  optimize_dataframes: true
  add_data_validation: true
  vectorize_operations: true
  add_visualizations: true
  
special_patterns:
  - "MemoryError"
  - "DataFrame"
  - "NaN"
  - "inf"
EOF

# Notebook analysis
make -C devix analyze-notebooks
```

---

## 🔄 CI/CD Integration Workflows

### **GitHub Actions + JetBrains**

```yaml
# .github/workflows/devix.yml
name: devix Analysis

on:
  pull_request:
  schedule:
    - cron: '0 2 * * *'  # Nightly

jobs:
  devix:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install JetBrains CLI
      run: |
        wget https://download.jetbrains.com/python/pycharm-professional-2024.1.tar.gz
        tar -xzf pycharm-professional-2024.1.tar.gz
        export PATH=$PATH:$(pwd)/pycharm-2024.1/bin
    
    - name: Run devix
      run: |
        cd devix
        pip install -r requirements.txt
        python supervisor.py --ide=pycharm --max-iterations=20
    
    - name: Upload Report
      uses: actions/upload-artifact@v3
      with:
        name: devix-report
        path: devix/logs/report_*.json
```

### **GitLab CI + devix**

```yaml
# .gitlab-ci.yml
devix-analysis:
  stage: quality
  image: python:3.11
  
  before_script:
    - apt-get update
    - apt-get install -y xvfb
    - pip install -r devix/requirements.txt
    
  script:
    - xvfb-run -a python devix/supervisor.py --ide=pycharm --max-iterations=20
    
  artifacts:
    reports:
      junit: devix/logs/test-report.xml
    paths:
      - devix/logs/
    
  only:
    - merge_requests
    - schedules
```

---

## 🎮 Game Development Workflow

### **Unity + Rider**

```bash
cd unity-project/

cat > devix/config.yaml << EOF
ide_type: rider
project_type: unity

jetbrains_integration:
  jetbrains_ide: rider
  
  rider_specific:
    unity_support: true
    csharp_support: true
    shader_support: true
    
improvement_goals:
  optimize_update_loops: true
  reduce_draw_calls: true
  fix_null_references: true
  add_object_pooling: true
EOF

make -C devix run-auto
```

---

## 📱 Mobile Development Workflow

### **Android + Android Studio (IntelliJ based)**

```bash
cd android-app/

cat > devix/config.yaml << EOF
ide_type: intellij
project_type: android

jetbrains_integration:
  intellij_specific:
    android_support: true
    gradle_integration: true
    kotlin_support: true
    
test_command: ./gradlew test
build_command: ./gradlew build
lint_command: ./gradlew lint
EOF

make -C devix run-auto
```

---

## 🔧 DevOps Workflow

### **Terraform + IntelliJ**

```bash
cd infrastructure/

cat > devix/config.yaml << EOF
ide_type: intellij
project_type: terraform

jetbrains_integration:
  terraform_support: true
  
validation_commands:
  - terraform fmt -check
  - terraform validate
  - tflint
  
improvement_goals:
  add_variables: true
  add_outputs: true
  modularize_resources: true
  add_documentation: true
EOF

make -C devix run-auto
```

---

## 💡 Best Practices dla Workflows

### **1. Staged Approach**

```bash
# Stage 1: Critical Fixes
make -C devix fix-critical

# Stage 2: Test Coverage
make -C devix increase-coverage

# Stage 3: Code Quality
make -C devix improve-quality

# Stage 4: Performance
make -C devix optimize-performance

# Stage 5: Documentation
make -C devix add-documentation
```

### **2. Team Workflow**

```bash
# Morning standup - check status
make -C devix status-jetbrains

# During development - real-time monitoring
make -C devix watch-jetbrains

# Before PR - validate
make -C devix validate-jetbrains

# After merge - full optimization
make -C devix optimize-jetbrains
```

### **3. Incremental Improvements**

```bash
# Day 1: Fix errors
echo "focus: errors" >> devix/config.yaml
make -C devix run-auto

# Day 2: Add tests
echo "focus: tests" >> devix/config.yaml
make -C devix run-auto

# Day 3: Improve performance
echo "focus: performance" >> devix/config.yaml
make -C devix run-auto
```

---

## 📈 Monitoring & Reporting

### **Dashboard Setup**

```bash
# Create dashboard
cd devix
python -m http.server 8080 --directory logs/

# View in browser
open http://localhost:8080
```

### **Slack Integration**

```bash
# Add to config
echo "slack_webhook: https://hooks.slack.com/..." >> config.yaml

# devix will send notifications
```

### **Email Reports**

```bash
# Daily report
echo "0 9 * * * cd $(pwd) && make -C devix report | mail -s 'devix Report' team@company.com" | crontab -l
```
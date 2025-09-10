#!/bin/bash
# Project status check for Devix
# Shows comprehensive project status and configuration

set -e

PACKAGE_NAME="devix"
SRC_DIR="src"
TEST_DIR="tests"

echo " Devix Project Status Report"
echo "============================="
echo "Generated: $(date)"
echo "Package: ${PACKAGE_NAME}"
echo ""

# Check if we're in devix directory or parent
if [ "$(basename $(pwd))" = "devix" ]; then
    PROJECT_ROOT="../"
    DEVIX_ROOT="."
    # But first check if pyproject.toml exists in current directory (devix itself is the project)
    if [ -f "pyproject.toml" ]; then
        PROJECT_ROOT="."
        DEVIX_ROOT="."
    fi
else
    PROJECT_ROOT="."
    DEVIX_ROOT="./devix"
fi

echo " Directory Structure:"
echo "----------------------"

# Check key files and directories
check_path() {
    local path="$1"
    local name="$2"
    local relative_path
    
    # Construct path properly based on PROJECT_ROOT
    if [ "$PROJECT_ROOT" = "." ]; then
        relative_path="$path"
    else
        relative_path="${PROJECT_ROOT}$path"
    fi
    
    if [ -f "$relative_path" ] || [ -d "$relative_path" ]; then
        echo " $name: $relative_path"
    else
        echo " $name: $relative_path (missing)"
    fi
    # Always return success to avoid script termination due to set -e
    return 0
}

# Project files
check_path "pyproject.toml" "Project config"
check_path ".devixignore" "Devix ignore file"
check_path "README.md" "Documentation"
# Check .gitignore in current or parent directory
if ! check_path ".gitignore" "Git ignore file"; then
    # Try parent directory
    check_path "../.gitignore" "Git ignore file (parent)"
fi

# Devix structure - adjust paths based on context
if [ "$PROJECT_ROOT" = "." ] && [ "$DEVIX_ROOT" = "." ]; then
    # We're in devix directory and it's the project root
    check_path "${SRC_DIR}" "Devix source"
    check_path "test_devix_integration.py" "Integration tests"
    check_path "Makefile" "Build system"
else
    # We're in parent directory looking at devix subdirectory
    check_path "devix/${SRC_DIR}" "Devix source"
    check_path "devix/test_devix_integration.py" "Integration tests"
    check_path "devix/Makefile" "Build system"
fi

echo ""

echo " Devix Configuration:"
echo "----------------------"

# Check if Devix is installed
if python3 -c "import devix" 2>/dev/null; then
    echo " Devix package: Installed"
    
    # Get version if available
    VERSION=$(python3 -c "import importlib.metadata; print(importlib.metadata.version('devix'))" 2>/dev/null || echo "unknown")
    echo " Version: $VERSION"
else
    echo " Devix package: Not installed"
    echo "   Run: make install"
fi

# Check .devixignore patterns
if [ -f ".devixignore" ]; then
    echo " .devixignore exists"
    PATTERNS=$(grep -v "^#" .devixignore | grep -v "^$" | wc -l | tr -d ' ')
    echo " Ignore patterns: $PATTERNS"
else
    echo " .devixignore missing"
fi

# Check recent analysis reports
if [ -d "reports" ]; then
    REPORT_COUNT=$(find reports -name "*.md" -o -name "*.txt" 2>/dev/null | wc -l | tr -d ' ')
    echo " Analysis reports: $REPORT_COUNT"
    if [ "$REPORT_COUNT" -gt 0 ]; then
        LATEST=$(find reports -name "*.md" -o -name "*.txt" 2>/dev/null | head -1)
        if [ -n "$LATEST" ]; then
            MOD_TIME=$(stat -c %y "$LATEST" 2>/dev/null | cut -d' ' -f1)
            echo " Last report: $MOD_TIME"
        fi
    fi
else
    echo " Analysis reports: 0 (no reports directory)"
fi

echo ""

echo " Quick Commands:"
echo "-----------------"
echo "  make run         # Run analysis on current project"

echo "  make test        # Run tests"

echo "  make lint        # Check code quality"

echo "  make format      # Format code"

echo "  make build       # Build package"

echo "  make help        # Show all commands"

echo ""

echo "================================"

# Ensure script exits with success status
exit 0

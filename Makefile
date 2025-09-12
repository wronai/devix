# Devix Makefile
# Modern Python Package Management with UV

.PHONY: help install build test run analyze publish version clean dev lint format check setup

# Python and UV configuration
PYTHON := python3
UV := uv
PACKAGE_NAME := devix
SRC_DIR := src
TEST_DIR := tests

# Version management
VERSION_FILE := $(SRC_DIR)/$(PACKAGE_NAME)/__init__.py

# Default target
help:
	@echo "🔧 Devix - Modern Code Analysis Package"
	@echo ""
	@echo "📦 Package Management:"
	@echo "  make install     - Install dependencies with UV"
	@echo "  make build       - Build the package"
	@echo "  make publish     - Publish to PyPI (auto-bumps version)"
	@echo "  make publish-test - Publish to Test PyPI (auto-bumps version)"
	@echo "  make version     - Show current version"
	@echo "  make version-bump VERSION=x.y.z - Bump to specific version"
	@echo "  make version-bump-auto - Auto-increment patch version"
	@echo ""
	@echo "🧪 Development & Testing:"
	@echo "  make test        - Run all tests"
	@echo "  make test-unit   - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make lint        - Run linting (flake8, pylint)"
	@echo "  make format      - Format code (black, isort)"
	@echo "  make check       - Type checking with mypy"
	@echo ""
	@echo "🚀 Usage:"
	@echo "  make run         - Run devix analysis on current project"
	@echo "  make analyze     - Run devix with custom path"
	@echo "  make dev         - Install in development mode"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make setup       - Setup development environment"
	@echo "  make status      - Show comprehensive project status"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Devix in Docker container"
	@echo "  make docker-shell  - Open interactive Docker shell"
	@echo "  make docker-clean  - Clean Docker images"
	@echo ""
	@echo "🚀 Advanced:"
	@echo "  make watch       - Watch mode (continuous analysis)"
	@echo "  make init-project - Initialize new project for Devix"
	@echo "  make dev-workflow - Complete development workflow"
	@echo "  make ci          - CI/CD pipeline simulation"
	@echo ""
	@echo "📖 Usage Examples:"
	@echo "  make run                    # Analyze current directory"
	@echo "  make analyze PATH=../myproject  # Analyze specific project"
	@echo "  make publish VERSION=1.0.1     # Publish with version bump"
	@echo "  make docker-run             # Run analysis in Docker"
	@echo "  make watch                  # Continuous analysis mode"

# Development setup
setup:
	@echo "🛠️ Setting up Devix development environment..."
	@if ! command -v uv &> /dev/null; then \
		echo "UV not found. You can install it manually with:"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo "Or continue using pip/build/twine for package management."; \
	else \
		echo "✅ UV found and ready to use"; \
	fi
	@echo "✅ Development environment ready"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	@if false; then \
		echo "Using UV..."; \
		$(UV) sync; \
	else \
		echo "Using pip..."; \
		$(PYTHON) -m pip install -e .; \
		$(PYTHON) -m pip install pytest coverage flake8 pylint black isort build twine; \
	fi
	@echo "✅ Dependencies installed"

# Development installation
dev: install
	@echo "🔧 Installing in development mode..."
	$(PYTHON) -m pip install -e .
	@echo "✅ Development installation complete"

# Build package
build:
	@echo "🏗️ Building Devix package..."
	@$(PYTHON) -m build
	@echo "✅ Package built successfully"

# Run devix analysis
run:
	@echo "🚀 Running Devix analysis..."
	@echo "📁 Project: $$(pwd)/.."
	cd .. && PYTHONPATH=$$(pwd)/devix/$(SRC_DIR) $(PYTHON) -m devix analyze

# Run devix with custom path
analyze:
	@echo "🔍 Running Devix analysis..."
	@if [ -n "$(PROJECT_PATH)" ]; then \
		echo "📁 Project: $(PROJECT_PATH)"; \
		PYTHONPATH=$$(pwd)/$(SRC_DIR) $(PYTHON) -m devix analyze $(PROJECT_PATH); \
	else \
		echo "📁 Project: $$(pwd)/.."; \
		cd .. && PYTHONPATH=$$(pwd)/devix/$(SRC_DIR) $(PYTHON) -m devix analyze; \
	fi

# Testing
test:
	@echo "🧪 Running all Devix tests..."
	$(PYTHON) -m pytest test_devix_integration.py -v --override-ini addopts=
	@echo "✅ Tests completed"

test-unit:
	@echo "🧪 Running unit tests..."
	$(PYTHON) -m pytest $(TEST_DIR)/ -v --override-ini addopts= --cov=$(SRC_DIR) --cov-report=term
	@echo "✅ Unit tests completed"

test-integration:
	@echo "🧪 Running integration tests..."
	$(PYTHON) test_devix_integration.py
	@echo "✅ Integration tests completed"

# Code quality
lint:
	@echo "🔍 Running linting..."
	$(PYTHON) -m flake8 $(SRC_DIR)/$(PACKAGE_NAME)
	$(PYTHON) -m pylint $(SRC_DIR)/$(PACKAGE_NAME)
	@echo "✅ Linting completed"

format:
	@echo "🎨 Formatting code..."
	$(PYTHON) -m black $(SRC_DIR) $(TEST_DIR)
	$(PYTHON) -m isort $(SRC_DIR) $(TEST_DIR)
	@echo "✅ Code formatted"

check:
	@echo "🔍 Type checking..."
	$(PYTHON) -m mypy $(SRC_DIR)/$(PACKAGE_NAME)
	@echo "✅ Type checking completed"

# Version management
version:
	@echo "📋 Current version:"
	@grep "__version__" $(VERSION_FILE) | sed 's/.*= *"\([^"]*\)".*/\1/'

version-bump:
	@echo "🔢 Bumping version..."
	@if [ -z "$(VERSION)" ]; then \
		echo "❌ Please specify VERSION: make version-bump VERSION=1.0.1"; \
		exit 1; \
	fi
	@sed -i 's/__version__ = "[^"]*"/__version__ = "$(VERSION)"/' $(VERSION_FILE)
	@sed -i 's/version = "[^"]*"/version = "$(VERSION)"/' pyproject.toml
	@echo "✅ Version bumped to $(VERSION) in both files"

version-bump-auto:
	@echo "🔢 Auto-bumping version..."
	@CURRENT_VERSION=$$(grep "__version__" $(VERSION_FILE) | sed 's/.*= *"\([^"]*\)".*/\1/'); \
	echo "📋 Current version: $$CURRENT_VERSION"; \
	NEW_VERSION=$$(echo $$CURRENT_VERSION | awk -F. '{$$NF=$$NF+1; print $$1"."$$2"."$$NF}'); \
	echo "📈 New version: $$NEW_VERSION"; \
	sed -i 's/__version__ = "[^"]*"/__version__ = "'"$$NEW_VERSION"'"/' $(VERSION_FILE); \
	sed -i 's/version = "[^"]*"/version = "'"$$NEW_VERSION"'"/' pyproject.toml; \
	echo "✅ Version auto-bumped to $$NEW_VERSION in both files"

# Publishing
publish:
	@echo "📤 Publishing to PyPI..."
	@echo "🧹 Cleaning previous builds..."
	@make clean > /dev/null 2>&1 || true
	@if [ -n "$(VERSION)" ]; then \
		make version-bump VERSION=$(VERSION); \
	else \
		make version-bump-auto; \
	fi
	@echo "🏗️ Building package with new version..."
	@make build
	@if false; then \
		echo "Using UV for publishing..."; \
		$(UV) publish; \
	else \
		echo "Using twine for publishing..."; \
		$(PYTHON) -m pip install --upgrade twine; \
		$(PYTHON) -m twine upload dist/*; \
	fi
	@echo "✅ Package published successfully"

publish-test: 
	@echo "📤 Publishing to Test PyPI..."
	@echo "🧹 Cleaning previous builds..."
	@make clean > /dev/null 2>&1 || true
	@if [ -n "$(VERSION)" ]; then \
		make version-bump VERSION=$(VERSION); \
	else \
		make version-bump-auto; \
	fi
	@echo "🏗️ Building package with new version..."
	@make build
	@if false; then \
		echo "Using UV for publishing to Test PyPI..."; \
		$(UV) publish --repository testpypi; \
	else \
		echo "Using twine for publishing to Test PyPI..."; \
		$(PYTHON) -m pip install --upgrade twine; \
		$(PYTHON) -m twine upload --repository testpypi dist/*; \
	fi
	@echo "✅ Package published to Test PyPI"

# Generate report
report:
	@echo "📊 Generating Devix analysis report..."
	$(PYTHON) -m devix analyze --output-format both --output-dir reports/
	@echo "✅ Report generated in reports/ directory"

# Clean build artifacts and cache
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".coverage" -delete
	find . -name "*.cover" -delete
	find . -name "*.log" -delete
	@echo "✅ Cleanup completed"

# Show package information
info:
	@echo "📋 Devix Package Information"
	@echo "================================"
	@echo "Package: $(PACKAGE_NAME)"
	@echo "Source: $(SRC_DIR)/$(PACKAGE_NAME)"
	@echo "Tests: $(TEST_DIR)"
	@echo "Python: $(PYTHON)"
	@echo "UV: $(UV)"
	@echo ""
	@echo "📊 Project Statistics:"
	@find $(SRC_DIR) -name "*.py" | wc -l | sed 's/^/Python files: /'
	@find $(SRC_DIR) -name "*.py" -exec cat {} \; | wc -l | sed 's/^/Lines of code: /'

# Quick development workflow
dev-workflow: clean lint test build
	@echo "🎉 Development workflow completed successfully!"

# CI/CD pipeline simulation
ci: clean lint test build
	@echo "🚀 CI Pipeline completed successfully!"

# Watch mode - continuous development
watch:
	@echo "👀 Starting watch mode..."
	@./scripts/watch.sh

# Docker commands (for containerization)
docker-build:
	@./scripts/docker.sh build

docker-run:
	@./scripts/docker.sh run

docker-shell:
	@./scripts/docker.sh shell

docker-clean:
	@./scripts/docker.sh clean

# Project initialization for new users
init-project:
	@./scripts/init-project.sh

# Project status check
status:
	@./scripts/status.sh
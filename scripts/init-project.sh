#!/bin/bash
# Project initialization for new Devix users
# Sets up configuration files and directory structure

set -e

PYTHON="python3"

echo "🎯 Initializing Devix for new project..."
echo ""

# Check if we're in the right location
if [ ! -f "pyproject.toml" ] && [ ! -f "../pyproject.toml" ]; then
    echo "⚠️  No pyproject.toml found in current or parent directory"
fi

# Navigate to project root (parent of devix directory if we're in devix)
if [ -d "../devix" ] && [ "$(basename $(pwd))" = "devix" ]; then
    cd ..
    echo "📁 Working in project root: $(pwd)"
elif [ -d "devix" ]; then
    echo "📁 Working in project root: $(pwd)"
else
    echo "📁 Working in current directory: $(pwd)"
fi

# Create pyproject.toml if it doesn't exist
if [ ! -f "pyproject.toml" ]; then
    echo "Creating pyproject.toml..."
    cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "your-project-name"
version = "0.1.0"
description = "Project analyzed with Devix"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers", 
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

[project.urls]
Homepage = "https://github.com/yourusername/your-project"
Repository = "https://github.com/yourusername/your-project"
Documentation = "https://your-project.readthedocs.io"

[tool.setuptools.packages.find]
where = ["src"]
include = ["your_project*"]

[tool.devix]
# Devix configuration
ignore_patterns = ["*.pyc", "__pycache__/", ".git/", ".pytest_cache/", "node_modules/"]
analyzers = ["security", "quality", "performance", "testing"]
output_format = "both"
EOF
    echo "✅ pyproject.toml created"
    echo "   📝 Please update the project name, author, and URLs"
else
    echo "✅ pyproject.toml already exists"
fi

# Create .devixignore if it doesn't exist
if [ ! -f ".devixignore" ]; then
    echo "Creating .devixignore..."
    cat > .devixignore << 'EOF'
# Devix ignore patterns
# Files and directories to exclude from analysis

# Python
*.pyc
*.pyo
*.pyd
__pycache__/
*.egg-info/
build/
dist/
.coverage
.pytest_cache/

# Version control
.git/
.gitignore
.gitattributes

# IDEs and editors
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Dependencies
node_modules/
venv/
env/
.env

# Logs and temporary files
*.log
*.tmp
*.temp

# Documentation build
docs/_build/
site/

# Test and coverage
htmlcov/
.coverage.*
.cache
.mypy_cache/
.tox/

# Package managers
.uv/
EOF
    echo "✅ .devixignore created"
else
    echo "✅ .devixignore already exists"
fi

# Create basic directory structure if needed
if [ ! -d "src" ] && [ ! -d "tests" ] && [ ! -d "docs" ]; then
    echo "Creating basic project structure..."
    mkdir -p src
    mkdir -p tests
    mkdir -p docs
    echo "✅ Basic directory structure created (src/, tests/, docs/)"
fi

# Create README.md template if it doesn't exist
if [ ! -f "README.md" ]; then
    echo "Creating README.md template..."
    cat > README.md << 'EOF'
# Your Project Name

Brief description of your project.

## Installation

```bash
pip install your-project-name
```

## Usage

```python
import your_project

# Your usage examples here
```

## Development

This project uses [Devix](https://github.com/yourusername/devix) for code analysis and quality assurance.

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/your-project.git
cd your-project

# Install dependencies
pip install -e .

# Run code analysis
python -m devix analyze
```

### Running Tests

```bash
pytest
```

## Code Quality

This project maintains high code quality using:

- **Devix Analysis**: Comprehensive code analysis and quality checks
- **Testing**: Unit and integration tests with pytest
- **Linting**: Code style enforcement with flake8 and pylint
- **Formatting**: Automatic code formatting with black and isort

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `python -m devix analyze` to ensure code quality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
EOF
    echo "✅ README.md template created"
    echo "   📝 Please customize the content for your project"
else
    echo "✅ README.md already exists"
fi

echo ""
echo "🎉 Project initialization completed!"
echo ""
echo "📋 Next steps:"
echo "  1. Update pyproject.toml with your project details"
echo "  2. Customize README.md"
echo "  3. Review and modify .devixignore patterns"
echo "  4. Run: python -m devix analyze"
echo ""
echo "🚀 Your project is ready for Devix analysis!"

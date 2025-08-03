# Dependency Management Migration

## Overview

This document describes the migration from multiple requirements files to a single `pyproject.toml` file for dependency management.

## Changes Made

### 1. Consolidated Dependencies

**Before:**
- `requirements.txt` - Core dependencies
- `requirements-dev.txt` - Development dependencies (included requirements.txt)

**After:**
- `pyproject.toml` - All dependencies in a single file

### 2. Dependency Organization

**Core Dependencies (16 total):**
- `requests>=2.31.0` - HTTP requests
- `validators>=0.22.0` - Data validation
- `python-dateutil>=2.8.2` - Date parsing
- `rich>=13.7.0` - Terminal formatting
- `beautifulsoup4>=4.12.3` - HTML parsing
- `click>=8.1.7` - CLI interface
- `selenium>=4.1.0` - Web scraping
- `webdriver-manager>=3.5.2` - WebDriver management
- `playwright>=1.42.0` - Modern web scraping
- `neo4j>=5.17.0` - Graph database
- `openai>=1.12.0` - AI text processing
- `PyYAML>=6.0.1` - YAML configuration
- `python-dotenv>=1.0.0` - Environment variables
- `spacy>=3.7.0` - Natural language processing
- `networkx>=3.2.0` - Graph visualization
- `matplotlib>=3.8.0` - Plotting

**Development Dependencies (7 total):**
- `pytest>=8.0.0` - Testing framework
- `pytest-selenium>=4.0.0` - Selenium testing
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Linting
- `mypy>=1.0.0` - Type checking
- `pytest-cov>=4.0.0` - Coverage reporting
- `pre-commit>=3.0.0` - Git hooks

### 3. Tool Configuration

Added comprehensive tool configurations:

**Black (Code Formatting):**
- Line length: 88 characters
- Target Python version: 3.8+
- Excludes common directories

**MyPy (Type Checking):**
- Strict type checking enabled
- Python 3.8+ compatibility
- Comprehensive warning settings

**Pytest (Testing):**
- Test discovery patterns
- Verbose output
- Custom markers for test categorization
- Coverage integration

**Coverage (Code Coverage):**
- Source directory configuration
- Exclusion patterns
- Report customization

### 4. Installation Instructions

**Before:**
```bash
pip install -r requirements-dev.txt
pip install -e .
```

**After:**
```bash
# Install core dependencies
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

## Benefits

1. **Single Source of Truth**: All dependencies in one file
2. **Modern Python Packaging**: Uses PEP 621 standard
3. **Better Tool Integration**: All tool configurations in one place
4. **Cleaner Installation**: Simplified installation commands
5. **Version Consistency**: Easier to manage dependency versions
6. **Development Workflow**: Clear separation between core and dev dependencies

## Migration Steps

1. ✅ Consolidated all dependencies into `pyproject.toml`
2. ✅ Added comprehensive tool configurations
3. ✅ Updated README installation instructions
4. ✅ Removed old requirements files
5. ✅ Validated package structure

## Usage

### For Users
```bash
# Install core functionality
pip install -e .
```

### For Developers
```bash
# Install everything including development tools
pip install -e ".[dev]"
```

### For CI/CD
```bash
# Install with development dependencies for testing
pip install -e ".[dev]"
pytest
```

## Validation

The migration was validated using:
- TOML parser validation
- Package structure verification
- Dependency count verification
- Tool configuration validation

All dependencies are properly organized and the package can be installed successfully using modern Python packaging tools. 
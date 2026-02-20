# Contributing to MedeX

Thank you for your interest in contributing to MedeX! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)

## 📜 Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to gonzalorome6@gmail.com.

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Med-X-KimiK2-RAG.git
   cd Med-X-KimiK2-RAG
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/DeepRatAI/Med-X-KimiK2-RAG.git
   ```

## 💻 Development Setup

### Prerequisites

- Python 3.10+
- Git
- A Moonshot/Kimi API key (for testing)

### Environment Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/medex --cov-report=html

# Run specific test file
pytest tests/test_detection.py -v
```

## ✏️ Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-new-detection-pattern`
- `fix/emergency-detection-false-positive`
- `docs/update-api-reference`
- `refactor/modularize-engine`

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:

```
feat(detection): add psychiatric emergency keywords
fix(engine): handle empty API response gracefully
docs(readme): add streaming example
```

## 🔄 Pull Request Process

1. **Update your fork** with the latest upstream changes:

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** and commit them

4. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** on GitHub

### PR Requirements

- [ ] Tests pass locally
- [ ] Code follows project style guidelines
- [ ] Documentation is updated if needed
- [ ] Commit messages follow conventions
- [ ] PR description explains the changes

## 📝 Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all functions
- Maximum line length: 88 characters (Black default)
- Use Google-style docstrings

### Type Hints

```python
def detect_emergency(self, query: str) -> EmergencyResult:
    """Detect emergency from query text.

    Args:
        query: The user's query text

    Returns:
        EmergencyResult with detection details
    """
    ...
```

### Docstrings

```python
class EmergencyDetector:
    """Detects medical emergencies from query text.

    Uses comprehensive keyword matching for various emergency
    categories including cardiac, respiratory, neurological,
    trauma, and other critical conditions.

    Attributes:
        CRITICAL_KEYWORDS: Set of critical emergency keywords
        URGENT_KEYWORDS: Set of urgent condition keywords

    Example:
        detector = EmergencyDetector()
        result = detector.detect("dolor torácico intenso")
        if result.is_emergency:
            print(f"Emergency detected: {result.category}")
    """
```

### Imports

Organize imports in this order:

1. Standard library
2. Third-party packages
3. Local imports

```python
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAI

from medex.core.config import MedeXConfig
from medex.detection.emergency import EmergencyDetector
```

## 🧪 Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_detection.py    # Detection tests
├── test_engine.py       # Engine tests
└── test_knowledge.py    # Knowledge base tests
```

### Writing Tests

```python
class TestEmergencyDetector:
    """Tests for EmergencyDetector."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.detector = EmergencyDetector()

    def test_detects_critical_chest_pain(self) -> None:
        """Test detection of critical chest pain."""
        query = "Tengo dolor precordial muy intenso"
        result = self.detector.detect(query)

        assert result.is_emergency is True
        assert result.level == EmergencyLevel.CRITICAL
```

### Test Coverage

We aim for >80% test coverage. Run coverage report:

```bash
pytest tests/ --cov=src/medex --cov-report=term-missing
```

## 🏥 Medical Content Guidelines

When adding medical content:

1. **Use authoritative sources** (ESC, AHA, WHO, etc.)
2. **Include evidence levels** when applicable
3. **Use proper medical terminology**
4. **Add appropriate disclaimers**
5. **Review with medical professionals** when possible

## ❓ Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Contact: gonzalorome6@gmail.com

---

Thank you for contributing to MedeX! 🙏

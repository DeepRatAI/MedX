# Changelog

All notable changes to MedeX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-02

### Added

- **Modular Package Structure**: Complete refactoring into `src/medex/` package
  - `medex.core`: Main engine, configuration, and system prompts
  - `medex.detection`: User type and emergency detection modules
  - `medex.knowledge`: Medical knowledge base and pharmaceutical database
  - `medex.vision`: Medical image analysis
- **Type Annotations**: Full type hints across all modules with `py.typed` marker

- **Professional Documentation**

  - Comprehensive README with examples
  - CONTRIBUTING.md with development guidelines
  - SECURITY.md with vulnerability reporting process
  - CODE_OF_CONDUCT.md

- **Test Suite**: pytest-based test suite with fixtures

  - Detection module tests
  - Engine configuration tests
  - System prompt tests

- **CI/CD Pipeline**: GitHub Actions workflows
  - Code quality checks (Black, Ruff, mypy)
  - Automated testing on multiple Python versions
  - Docker build verification

### Changed

- **Configuration**: Moved from hardcoded fallback to proper error handling when API key is missing
- **Prompts**: Extracted system prompts into dedicated `SystemPrompts` class
- **Detection**: Modularized user type and emergency detection with dataclass results

### Removed

- Hardcoded API key fallback (security improvement)
- Dead code in `core/` directory (4 unused files, ~2,800 lines)

### Security

- API key must now be provided via environment variable or file
- No secrets in source code

---

## [0.1.0] - 2025-10-17

### Added

- Initial release of MedeX Medical AI System
- Dual-mode operation (Professional/Educational)
- Emergency detection with keyword matching
- Medical image analysis (RX, CT, MRI, US)
- RAG system with SentenceTransformers
- Pharmaceutical database
- Streamlit web interface
- Docker deployment support
- HuggingFace Spaces integration

---

[1.0.0]: https://github.com/DeepRatAI/Med-X-KimiK2-RAG/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/DeepRatAI/Med-X-KimiK2-RAG/releases/tag/v0.1.0

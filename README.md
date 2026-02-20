<div align="center">

# 🏥 MedX

**Medical AI Intelligence System**

[![CI](https://github.com/DeepRatAI/MedX/actions/workflows/ci.yml/badge.svg)](https://github.com/DeepRatAI/MedX/actions/workflows/ci.yml)
[![Canary](https://github.com/DeepRatAI/MedX/actions/workflows/canary.yml/badge.svg)](https://github.com/DeepRatAI/MedX/actions/workflows/canary.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An open-source medical AI assistant that combines multi-model LLM routing, RAG-enhanced clinical knowledge, emergency detection, and medical image analysis into a single, production-ready platform. MedX is designed for clinical decision support and medical education — not as a replacement for professional medical judgment.

[Documentation](#-documentation) · [Quick Start](#-quick-start) · [Contributing](CONTRIBUTING.md) · [Disclaimer](DISCLAIMER.md)

</div>

<p align="center">
  <img src="docs/assets/med-x.gif" alt="MedX Demo" width="90%">
</p>

---

## 🖥️ UI Preview

<table>
<tr>
<td align="center"><strong>Clinical Consultation</strong></td>
<td align="center"><strong>Drug Interaction Checker</strong></td>
<td align="center"><strong>Emergency Triage</strong></td>
</tr>
<tr>
<td><img src="docs/assets/ui-main-consultation.svg" alt="Main Consultation" width="100%"></td>
<td><img src="docs/assets/ui-drug-interactions.svg" alt="Drug Interactions" width="100%"></td>
<td><img src="docs/assets/ui-emergency-triage.svg" alt="Emergency Triage" width="100%"></td>
</tr>
</table>

---

## ✨ Key Features

| | Feature | Description |
|---|---|---|
| 🎭 | **Dual-Mode Consultation** | Professional mode (SOAP notes, ICD-10, evidence-based protocols) and patient-friendly educational mode with automatic detection |
| 🚨 | **Emergency Detection** | 50+ pattern recognizer with real-time triage classification (Critical / Urgent / Routine) across cardiac, respiratory, neurological, and trauma categories |
| 🔬 | **Medical Image Analysis** | Vision-model powered interpretation for RX, CT, MRI, and ultrasound with modality validation and clinical context integration |
| 📚 | **RAG Knowledge Base** | 1,000+ medical conditions and 500+ medications indexed into Qdrant for vector-similarity retrieval, with ICD-10 coding and pharmaceutical interaction data |
| 💊 | **Pharmaceutical Database** | Comprehensive drug information including dosages, contraindications, drug-drug interactions, and Micromedex-style monographs |
| 🧠 | **Differential Diagnosis** | Structured diagnostic reasoning engine that generates ranked differential lists with supporting and opposing evidence |
| 🔎 | **Scientific Literature Search** | Integrated PubMed and Semantic Scholar queries for evidence-based references and up-to-date research |
| 🤖 | **Multi-Model LLM Routing** | Intelligent routing across 8 models via HuggingFace Inference Providers — selects the best model per task (reasoning, vision, speed) |
| 🖥️ | **Reflex UI** | Interactive chat interface with medical tool panels, conversation history, and PDF export — built with Reflex (Python-native) |
| ⚡ | **FastAPI Backend** | Async streaming API with structured endpoints for chat, image analysis, and tool invocation |
| 🐳 | **Production Infrastructure** | Docker Compose stack with PostgreSQL (sessions), Redis (cache), and Qdrant (vector store) |
| 🔒 | **HIPAA-Aware Logging** | PII anonymization pipeline, audit trails, and configurable log redaction for sensitive medical data |

---

## 🏗️ Architecture

MedX follows a modular, layered architecture:

```
User → Reflex UI → FastAPI API → Agent Controller → LLM Router → Model Providers
                                       ↓
                              Detection · RAG · Tools
                              (Emergency, Knowledge, PubMed, Diagnosis)
                                       ↓
                              PostgreSQL · Redis · Qdrant
```

Each domain lives in its own package under `src/medex/` — see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full component breakdown, data flow diagrams, and infrastructure details.

---

## 🚀 Quick Start

### 📋 Prerequisites

- **Python 3.10+**
- **Docker & Docker Compose** (for infrastructure services)
- **HuggingFace API token** with Inference Providers access
- (Optional) GPU for local embedding models

### Installation

```bash
# Clone the repository
git clone https://github.com/DeepRatAI/MedX.git
cd MedX

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in editable mode
pip install -e .
```

### Using Make

```bash
make install       # Install production dependencies
make dev           # Install dev + production dependencies
make infra-up      # Start PostgreSQL, Redis, Qdrant
make run-api       # Start FastAPI server on port 8000
make run-ui        # Start Reflex UI
```

### Using Docker Compose (full stack)

```bash
docker compose up -d
```

---

## ⚙️ Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

**Required variables:**

| Variable | Description |
|---|---|
| `HF_TOKEN` | HuggingFace API token (Inference Providers) |
| `MEDEX_ENV` | Environment: `development`, `production`, `test` |

**Infrastructure (auto-configured via Docker Compose):**

| Variable | Default |
|---|---|
| `POSTGRES_DSN` | `postgresql://medex:medex@localhost:5432/medex` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `QDRANT_URL` | `http://localhost:6333` |

See [.env.example](.env.example) for the full list of configurable options.

---

## 🧪 Testing

```bash
# Run full test suite
make test

# Run with coverage report
make test-cov

# Run a specific test file
pytest tests/test_detection.py -v --asyncio-mode=auto

# Run fast (stop on first failure)
make test-fast
```

Tests use `pytest` with `pytest-asyncio` for async test support. Infrastructure-dependent tests are skipped automatically when services are unavailable.

---

## 📖 Documentation

| Document | Description |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | System design, component map, data flow |
| [Technical Documentation](docs/TECHNICAL_DOCUMENTATION.md) | Implementation details and API internals |
| [Knowledge Base API](docs/KNOWLEDGE_BASE_API.md) | RAG pipeline and knowledge indexing |
| [Ontology Reference](docs/ONTOLOGY_REFERENCE.md) | Medical ontology and ICD-10 mapping |
| [Streaming & Thinking](docs/STREAMING_THINKING_DECISIONS.md) | Real-time streaming architecture decisions |
| [Tools Roadmap](docs/TOOLS_ROADMAP.md) | Planned tool integrations |
| [User Guide](docs/user_guide.md) | End-user usage guide |
| [Roadmap](docs/ROADMAP.md) | Development roadmap |
| [Release Report](MEDX_PUBLIC_RELEASE_REPORT.md) | Public release audit report |

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on:

- Development setup and workflow
- Code style and conventions
- Pull request process
- Code of Conduct

---

## ⚠️ Disclaimer

**MedX is NOT a medical device and is NOT a substitute for professional medical advice, diagnosis, or treatment.**

This software is provided for **educational and research purposes only**. It has not undergone clinical validation or regulatory approval. Always consult a qualified healthcare professional for medical decisions. For emergencies, call your local emergency number (911, 112, etc.).

See [DISCLAIMER.md](DISCLAIMER.md) for the full legal disclaimer.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **HuggingFace** — Inference Providers and model hosting
- **Qdrant** — Vector similarity search engine
- **Reflex** — Python-native web framework
- **FastAPI** — High-performance async API framework
- **SentenceTransformers** — Embedding models for RAG
- **PubMed / Semantic Scholar** — Scientific literature APIs
- The open-source medical AI research community

---

<div align="center">

**Built by [Gonzalo Romero](https://github.com/DeepRatAI) — [@DeepRatAI](https://github.com/DeepRatAI)**

_Building tools that think_

</div>

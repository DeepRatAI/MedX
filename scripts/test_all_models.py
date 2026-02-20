#!/usr/bin/env python3
"""
MedeX Model Testing Script
==========================
Tests all available models with a battery of medical questions
in both educational and professional modes.

Generates a comprehensive report documenting model performance.
"""

import asyncio
import json
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any

import httpx

# =============================================================================
# Configuration
# =============================================================================

API_URL = "http://localhost:8000"

# All models available in the UI selector
MODELS = [
    "qwen-72b",
    "llama-70b",
    "deepseek-r1",
    "gemini-2-flash",
    "openbiollm-70b",
    "meditron-70b",
    "med42-llama3-70b",
    "biomistral-7b",
    "medalpaca-13b",
    "llama3-aloe-8b",
]

# Test questions (medical scenarios)
TEST_QUESTIONS = [
    {
        "id": "q1",
        "question": "¿Cuáles son los síntomas típicos de la diabetes tipo 2?",
        "category": "symptoms",
        "expected_topics": [
            "poliuria",
            "polidipsia",
            "polifagia",
            "fatiga",
            "visión borrosa",
        ],
    },
    {
        "id": "q2",
        "question": "¿Qué medicamentos se usan para tratar la hipertensión arterial?",
        "category": "treatment",
        "expected_topics": [
            "IECA",
            "ARA-II",
            "diuréticos",
            "betabloqueantes",
            "calcioantagonistas",
        ],
    },
    {
        "id": "q3",
        "question": "¿Cuáles son las contraindicaciones del ibuprofeno?",
        "category": "pharmacology",
        "expected_topics": [
            "úlcera",
            "insuficiencia renal",
            "embarazo",
            "alergia AINE",
            "hemorragia",
        ],
    },
    {
        "id": "q4",
        "question": "¿Cómo se interpreta una glucosa en ayunas de 126 mg/dL?",
        "category": "diagnosis",
        "expected_topics": ["diabetes", "prediabetes", "confirmación", "HbA1c", "PTOG"],
    },
    {
        "id": "q5",
        "question": "¿Cuál es el tratamiento de primera línea para la neumonía adquirida en la comunidad?",
        "category": "treatment",
        "expected_topics": [
            "amoxicilina",
            "macrólido",
            "fluoroquinolona",
            "ambulatorio",
            "hospitalización",
        ],
    },
]

# Modes to test
MODES = ["educational", "professional"]


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class TestResult:
    """Single test result."""

    model_id: str
    question_id: str
    mode: str
    success: bool
    latency_ms: float
    response_length: int
    response_preview: str
    tokens_used: int = 0
    error: str = ""
    model_hf: str = ""
    topics_found: list[str] = field(default_factory=list)


@dataclass
class ModelReport:
    """Report for a single model."""

    model_id: str
    model_hf: str = ""
    total_tests: int = 0
    successful_tests: int = 0
    avg_latency_ms: float = 0
    avg_response_length: int = 0
    avg_tokens: int = 0
    results: list[TestResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0
        return (self.successful_tests / self.total_tests) * 100


# =============================================================================
# Testing Functions
# =============================================================================


async def test_model_query(
    model_id: str,
    question: str,
    mode: str,
    timeout: float = 120.0,
) -> tuple[dict[str, Any], float]:
    """Test a single query against a model."""
    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{API_URL}/api/v1/query",
            json={
                "query": question,
                "user_type": mode,
                "model": model_id,
                "language": "es",
            },
        )
        response.raise_for_status()
        data = response.json()

    latency = (time.perf_counter() - start_time) * 1000
    return data, latency


def check_topics(response: str, expected_topics: list[str]) -> list[str]:
    """Check which expected topics are mentioned in the response."""
    response_lower = response.lower()
    found = []
    for topic in expected_topics:
        if topic.lower() in response_lower:
            found.append(topic)
    return found


async def run_model_tests(model_id: str) -> ModelReport:
    """Run all tests for a single model."""
    report = ModelReport(model_id=model_id)

    print(f"\n{'=' * 60}")
    print(f"Testing model: {model_id}")
    print(f"{'=' * 60}")

    for mode in MODES:
        print(f"\n  Mode: {mode.upper()}")
        print(f"  {'-' * 40}")

        for q in TEST_QUESTIONS:
            result = TestResult(
                model_id=model_id,
                question_id=q["id"],
                mode=mode,
                success=False,
                latency_ms=0,
                response_length=0,
                response_preview="",
            )

            try:
                data, latency = await test_model_query(
                    model_id=model_id,
                    question=q["question"],
                    mode=mode,
                )

                response_text = data.get("response", "")
                tokens = data.get("tokens", {})

                result.success = True
                result.latency_ms = latency
                result.response_length = len(response_text)
                result.response_preview = (
                    response_text[:200] + "..."
                    if len(response_text) > 200
                    else response_text
                )
                result.tokens_used = tokens.get("total", 0)
                result.model_hf = data.get("model_hf", "")
                result.topics_found = check_topics(
                    response_text, q.get("expected_topics", [])
                )

                # Update report
                if not report.model_hf:
                    report.model_hf = result.model_hf

                print(
                    f"    ✅ {q['id']}: {latency:.0f}ms, {len(response_text)} chars, {result.tokens_used} tokens"
                )
                print(f"       Topics: {result.topics_found}")

            except Exception as e:
                result.error = str(e)
                print(f"    ❌ {q['id']}: ERROR - {e}")

            report.results.append(result)
            report.total_tests += 1
            if result.success:
                report.successful_tests += 1

    # Calculate averages
    successful_results = [r for r in report.results if r.success]
    if successful_results:
        report.avg_latency_ms = sum(r.latency_ms for r in successful_results) / len(
            successful_results
        )
        report.avg_response_length = sum(
            r.response_length for r in successful_results
        ) // len(successful_results)
        report.avg_tokens = sum(r.tokens_used for r in successful_results) // len(
            successful_results
        )

    return report


async def run_all_tests() -> list[ModelReport]:
    """Run tests for all models."""
    reports = []

    print("\n" + "=" * 70)
    print("  MedeX Model Testing Suite")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"\nModels to test: {len(MODELS)}")
    print(f"Questions per model: {len(TEST_QUESTIONS)}")
    print(f"Modes: {MODES}")
    print(f"Total tests: {len(MODELS) * len(TEST_QUESTIONS) * len(MODES)}")

    for model_id in MODELS:
        try:
            report = await run_model_tests(model_id)
            reports.append(report)
        except Exception as e:
            print(f"\n❌ FAILED to test {model_id}: {e}")
            reports.append(ModelReport(model_id=model_id))

    return reports


def generate_markdown_report(reports: list[ModelReport]) -> str:
    """Generate markdown report from test results."""
    lines = [
        "# MedeX Model Testing Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Models Tested:** {len(reports)}",
        "",
        "---",
        "",
        "## Summary Table",
        "",
        "| Model ID | HF Model | Success Rate | Avg Latency (ms) | Avg Tokens | Avg Chars |",
        "|----------|----------|--------------|------------------|------------|-----------|",
    ]

    for r in reports:
        lines.append(
            f"| {r.model_id} | {r.model_hf or 'N/A'} | {r.success_rate:.0f}% | {r.avg_latency_ms:.0f} | {r.avg_tokens} | {r.avg_response_length} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Detailed Results by Model",
            "",
        ]
    )

    for report in reports:
        lines.extend(
            [
                f"### {report.model_id}",
                "",
                f"- **HuggingFace Model:** `{report.model_hf or 'N/A'}`",
                f"- **Success Rate:** {report.success_rate:.0f}%",
                f"- **Average Latency:** {report.avg_latency_ms:.0f} ms",
                f"- **Average Tokens:** {report.avg_tokens}",
                "",
                "#### Test Results",
                "",
                "| Question | Mode | Status | Latency | Tokens | Topics Found |",
                "|----------|------|--------|---------|--------|--------------|",
            ]
        )

        for result in report.results:
            status = "✅" if result.success else "❌"
            topics = ", ".join(result.topics_found[:3]) if result.topics_found else "-"
            lines.append(
                f"| {result.question_id} | {result.mode} | {status} | {result.latency_ms:.0f}ms | {result.tokens_used} | {topics} |"
            )

        lines.append("")

    # Insights section
    lines.extend(
        [
            "---",
            "",
            "## Insights and Recommendations",
            "",
        ]
    )

    # Find best performers
    successful_reports = [r for r in reports if r.success_rate > 0]
    if successful_reports:
        fastest = min(
            successful_reports,
            key=lambda x: x.avg_latency_ms if x.avg_latency_ms > 0 else float("inf"),
        )
        most_detailed = max(successful_reports, key=lambda x: x.avg_response_length)
        most_tokens = max(successful_reports, key=lambda x: x.avg_tokens)

        lines.extend(
            [
                f"### Performance Leaders",
                "",
                f"- **Fastest Response:** `{fastest.model_id}` ({fastest.avg_latency_ms:.0f}ms average)",
                f"- **Most Detailed:** `{most_detailed.model_id}` ({most_detailed.avg_response_length} chars average)",
                f"- **Most Comprehensive:** `{most_tokens.model_id}` ({most_tokens.avg_tokens} tokens average)",
                "",
            ]
        )

    return "\n".join(lines)


def save_report(reports: list[ModelReport], output_path: str):
    """Save report to file."""
    markdown = generate_markdown_report(reports)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"\n📄 Report saved to: {output_path}")


async def main():
    """Main entry point."""
    reports = await run_all_tests()

    # Print summary
    print("\n" + "=" * 70)
    print("  TESTING COMPLETE - SUMMARY")
    print("=" * 70)

    for r in reports:
        status = (
            "✅" if r.success_rate == 100 else ("⚠️" if r.success_rate > 0 else "❌")
        )
        print(
            f"  {status} {r.model_id}: {r.success_rate:.0f}% success, {r.avg_latency_ms:.0f}ms avg"
        )

    # Save report
    output_path = f"/home/gonzalor/Desktop/Edicion_total_repositorios/MedeX/docs/model_testing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    save_report(reports, output_path)

    # Also save raw JSON data
    json_path = output_path.replace(".md", ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "model_id": r.model_id,
                    "model_hf": r.model_hf,
                    "success_rate": r.success_rate,
                    "avg_latency_ms": r.avg_latency_ms,
                    "avg_tokens": r.avg_tokens,
                    "results": [
                        {
                            "question_id": res.question_id,
                            "mode": res.mode,
                            "success": res.success,
                            "latency_ms": res.latency_ms,
                            "tokens": res.tokens_used,
                            "error": res.error,
                        }
                        for res in r.results
                    ],
                }
                for r in reports
            ],
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"📊 JSON data saved to: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())

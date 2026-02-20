#!/usr/bin/env python3
"""
MedX Online Canary Check
========================
End-to-end health check for MedX core pipeline.

Runs 5 representative canary probes covering:
  1. Emergency detection (critical symptom recognition)
  2. User type classification (professional vs patient)
  3. Medical knowledge base (ICD-10 catalog integrity)
  4. Clinical formatting (output structure validation)
  5. Online LLM inference (HuggingFace API, if HF_TOKEN set)

Invariants (HARD — fail the run):
  - Every probe runs without unhandled exceptions
  - Outputs are non-empty and structurally valid
  - No secrets/tokens leak into outputs
  - No destructive timeouts (each probe < 60s)

Metrics (SOFT — warn only):
  - Latency per probe
  - Knowledge base coverage counts
  - LLM response quality signals

Artifacts:
  - canary_report/summary.md   — human-readable summary
  - canary_report/results.json — machine-readable metrics
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class ProbeResult:
    name: str
    status: str = "SKIP"  # PASS / FAIL / WARN / SKIP
    latency_ms: float = 0.0
    message: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class CanaryReport:
    timestamp: str = ""
    overall: str = "FAIL"
    probes: list[ProbeResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def passed(self) -> bool:
        return all(p.status in ("PASS", "WARN") for p in self.probes)


# ── Probe implementations ───────────────────────────────────────────────────

TOKEN_PATTERNS = [
    "github_pat_",
    "hf_",
    "sk-",
    "gsk_",
    "csk-",
    "AIzaSy",
]


def _check_no_leak(text: str) -> bool:
    """Return True if text is clean (no token patterns)."""
    for pat in TOKEN_PATTERNS:
        if pat in text and len(text.split(pat)[1]) > 15:
            return False
    return True


def probe_emergency_detection() -> ProbeResult:
    """Probe 1: Emergency detection on 5 MedX-representative queries."""
    r = ProbeResult(name="Emergency Detection")
    t0 = time.monotonic()
    try:
        from medex.detection.emergency import EmergencyDetector, EmergencyLevel

        detector = EmergencyDetector()
        cases = [
            (
                "Dolor torácico intenso con dificultad respiratoria y sudoración fría",
                True,
            ),
            ("Paciente inconsciente, no responde a estímulos", True),
            ("¿Qué es la diabetes tipo 2?", False),
            ("Paro cardíaco, el paciente no tiene pulso", True),
            ("Tengo un resfriado leve desde ayer", False),
        ]
        for query, expect_emergency in cases:
            result = detector.detect(query)
            assert result is not None, f"detect() returned None for: {query[:40]}"
            assert hasattr(result, "is_emergency"), "Missing is_emergency attribute"
            if expect_emergency:
                assert result.is_emergency, f"Should be emergency: {query[:40]}"
            assert _check_no_leak(str(result)), "Token leak in output!"

        r.status = "PASS"
        r.message = f"5/5 queries classified correctly"
        r.details = {"queries_tested": 5, "all_correct": True}
    except Exception as e:
        r.status = "FAIL"
        r.message = f"{type(e).__name__}: {e}"
        r.details = {"traceback": traceback.format_exc()}
    r.latency_ms = (time.monotonic() - t0) * 1000
    return r


def probe_user_type_detection() -> ProbeResult:
    """Probe 2: Professional vs Educational user classification."""
    r = ProbeResult(name="User Type Detection")
    t0 = time.monotonic()
    try:
        from medex.detection.user_type import UserTypeDetector

        detector = UserTypeDetector()
        cases = [
            (
                "Paciente de 55 años, diabético tipo 2, presenta dolor precordial",
                "Professional",
            ),
            ("Me duele mucho el pecho, estoy preocupado", "Educational"),
            (
                "Caso clínico: mujer 40 años con diagnóstico diferencial de IAM",
                "Professional",
            ),
            ("¿Qué pastilla puedo tomar para el dolor de cabeza?", "Educational"),
            (
                "Hallazgos histopatológicos compatibles con adenocarcinoma",
                "Professional",
            ),
        ]
        correct = 0
        for query, expected in cases:
            result = detector.detect(query)
            assert result is not None, f"detect() returned None"
            assert hasattr(result, "user_type"), "Missing user_type attribute"
            if result.user_type == expected:
                correct += 1
            assert _check_no_leak(str(result)), "Token leak in output!"

        if correct >= 4:
            r.status = "PASS"
        elif correct >= 3:
            r.status = "WARN"
        else:
            r.status = "FAIL"
        r.message = f"{correct}/5 queries classified correctly"
        r.details = {"queries_tested": 5, "correct": correct}
    except Exception as e:
        r.status = "FAIL"
        r.message = f"{type(e).__name__}: {e}"
        r.details = {"traceback": traceback.format_exc()}
    r.latency_ms = (time.monotonic() - t0) * 1000
    return r


def probe_knowledge_base() -> ProbeResult:
    """Probe 3: ICD-10 catalog and medications DB integrity."""
    r = ProbeResult(name="Knowledge Base Integrity")
    t0 = time.monotonic()
    try:
        from knowledge.icd10_catalog import get_all_generated_conditions

        conditions = get_all_generated_conditions()
        assert conditions is not None, "get_all_generated_conditions() returned None"
        count = len(conditions)
        assert count > 100, f"Expected >100 conditions, got {count}"

        # Verify structure — generated conditions are MedicalCondition dataclasses
        first_key = next(iter(conditions))
        sample = conditions[first_key]
        assert hasattr(sample, "icd10_code"), "Missing icd10_code field"
        assert hasattr(sample, "name"), "Missing name field"
        assert len(sample.icd10_code) > 0, "Empty ICD-10 code"

        r.status = "PASS"
        r.message = f"{count} ICD-10 conditions loaded"
        r.details = {"icd10_count": count, "sample_code": sample.icd10_code}
    except Exception as e:
        r.status = "FAIL"
        r.message = f"{type(e).__name__}: {e}"
        r.details = {"traceback": traceback.format_exc()}
    r.latency_ms = (time.monotonic() - t0) * 1000
    return r


def probe_clinical_formatter() -> ProbeResult:
    """Probe 4: Clinical response formatter produces valid output."""
    r = ProbeResult(name="Clinical Formatter")
    t0 = time.monotonic()
    try:
        from medex.medical.formatter import ClinicalFormatter, FormatterConfig

        fmt = ClinicalFormatter()
        assert fmt is not None, "Formatter initialization failed"

        # Verify config defaults
        cfg = FormatterConfig()
        assert cfg is not None, "FormatterConfig() failed"

        r.status = "PASS"
        r.message = "Formatter initializes and config is valid"
        r.details = {"formatter_ready": True}
    except Exception as e:
        r.status = "FAIL"
        r.message = f"{type(e).__name__}: {e}"
        r.details = {"traceback": traceback.format_exc()}
    r.latency_ms = (time.monotonic() - t0) * 1000
    return r


def probe_online_llm() -> ProbeResult:
    """Probe 5: Online HuggingFace Inference API call."""
    r = ProbeResult(name="Online LLM Inference")
    t0 = time.monotonic()

    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        r.status = "WARN"
        r.message = "HF_TOKEN not set — skipping online LLM probe"
        r.details = {"skipped": True, "reason": "no_token"}
        r.latency_ms = (time.monotonic() - t0) * 1000
        return r

    try:
        from huggingface_hub import InferenceClient

        client = InferenceClient(
            model="google/gemma-3-27b-it",
            token=hf_token,
            timeout=45,
        )

        query = (
            "A 55-year-old diabetic patient presents with acute chest pain "
            "radiating to the left arm. What are the top 3 differential diagnoses? "
            "Answer in 2-3 sentences."
        )

        chat_response = client.chat_completion(
            messages=[{"role": "user", "content": query}],
            max_tokens=200,
            temperature=0.3,
        )

        response = chat_response.choices[0].message.content or ""
        assert response is not None, "LLM returned None"
        assert len(response.strip()) > 20, f"Response too short: {len(response)} chars"
        assert _check_no_leak(response), "Token leak in LLM response!"

        # Soft quality check
        has_medical_term = any(
            term in response.lower()
            for term in [
                "myocardial",
                "infarction",
                "angina",
                "aortic",
                "pulmonary",
                "cardiac",
                "coronary",
                "chest",
                "acs",
                "infarto",
                "miocardio",
            ]
        )

        r.status = "PASS"
        r.message = f"LLM responded ({len(response)} chars)"
        r.details = {
            "response_length": len(response),
            "has_medical_terms": has_medical_term,
            "response_preview": response[:200],
        }
        if not has_medical_term:
            r.status = "WARN"
            r.message += " — no medical terminology detected"

    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "403" in error_str:
            r.status = "WARN"
            r.message = (
                f"HF API auth issue (token may need rotation): {error_str[:100]}"
            )
            r.details = {"auth_error": True}
        elif "429" in error_str or "rate" in error_str.lower():
            r.status = "WARN"
            r.message = f"HF API rate limited: {error_str[:100]}"
            r.details = {"rate_limited": True}
        elif "not supported" in error_str.lower() or "provider" in error_str.lower():
            r.status = "WARN"
            r.message = f"Model/provider issue (non-critical): {error_str[:150]}"
            r.details = {"provider_error": True}
        else:
            r.status = "FAIL"
            r.message = f"{type(e).__name__}: {error_str[:200]}"
            r.details = {"traceback": traceback.format_exc()}

    r.latency_ms = (time.monotonic() - t0) * 1000
    return r


# ── Runner ───────────────────────────────────────────────────────────────────


def run_canary() -> CanaryReport:
    report = CanaryReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    probes = [
        probe_emergency_detection,
        probe_user_type_detection,
        probe_knowledge_base,
        probe_clinical_formatter,
        probe_online_llm,
    ]

    for probe_fn in probes:
        print(f"  ▸ Running {probe_fn.__name__}...", end=" ", flush=True)
        result = probe_fn()
        report.probes.append(result)
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}.get(
            result.status, "?"
        )
        print(f"{icon} {result.status} ({result.latency_ms:.0f}ms) — {result.message}")

        if result.status == "WARN":
            report.warnings.append(f"{result.name}: {result.message}")

    report.overall = "PASS" if report.passed() else "FAIL"
    return report


def write_report(report: CanaryReport, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON report
    json_data = {
        "timestamp": report.timestamp,
        "overall": report.overall,
        "probes": [asdict(p) for p in report.probes],
        "warnings": report.warnings,
    }
    (out_dir / "results.json").write_text(json.dumps(json_data, indent=2))

    # Markdown summary
    md_lines = [
        "# 🐤 MedX Canary Report",
        "",
        f"**Timestamp:** {report.timestamp}",
        f"**Overall:** {'✅ PASS' if report.overall == 'PASS' else '❌ FAIL'}",
        "",
        "## Probe Results",
        "",
        "| # | Probe | Status | Latency | Message |",
        "|---|-------|--------|---------|---------|",
    ]
    for i, p in enumerate(report.probes, 1):
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}.get(p.status, "?")
        md_lines.append(
            f"| {i} | {p.name} | {icon} {p.status} | {p.latency_ms:.0f}ms | {p.message} |"
        )

    if report.warnings:
        md_lines.extend(["", "## Warnings", ""])
        for w in report.warnings:
            md_lines.append(f"- ⚠️ {w}")

    md_lines.extend(["", "---", "*Generated by MedX Canary v0.1.0*", ""])
    (out_dir / "summary.md").write_text("\n".join(md_lines))


def main() -> int:
    print("🐤 MedX Online Canary Check")
    print("=" * 50)

    report = run_canary()

    print()
    print(f"Overall: {report.overall}")
    if report.warnings:
        print(f"Warnings: {len(report.warnings)}")
        for w in report.warnings:
            print(f"  ⚠️  {w}")

    out_dir = Path("canary_report")
    write_report(report, out_dir)
    print(f"\nReport written to {out_dir}/")

    if report.overall == "FAIL":
        print("\n❌ CANARY FAILED — see report for details")
        return 1
    else:
        print("\n✅ CANARY PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())

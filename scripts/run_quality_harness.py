#!/usr/bin/env python3
"""Run the reproducible LKS-SDD M4 quality and regression harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
QUALITY_ROOT = PLUGIN_ROOT / "quality"
CATALOG_PATH = QUALITY_ROOT / "catalog.json"
CORPUS_PATH = QUALITY_ROOT / "corpora" / "activation.json"
DEFINITION_CORPUS_PATH = QUALITY_ROOT / "corpora" / "definition-v0.6.0.json"
FIXTURE_MANIFEST_PATH = QUALITY_ROOT / "fixture-manifest.json"
DEFAULT_BASELINE_PATH = QUALITY_ROOT / "baselines" / "v0.4.0.json"
MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
ALLOWED_SKILLS = {
    "lks-sdd-help",
    "lks-sdd-define",
    "lks-sdd-adopt-existing",
    "lks-sdd-assess-readiness",
    "lks-sdd-implement",
    "lks-sdd-verify",
}
SCORE_KEYS = {
    "correctness",
    "completeness",
    "clarity",
    "verifiability",
    "traceability",
    "proportionality",
    "operational_utility",
    "audience_fit",
    "information_separation",
    "information_protection",
}


class HarnessError(Exception):
    """Expected, actionable harness failure."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HarnessError(f"JSON ilegible {path}: {exc}") from exc


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HarnessError(f"{label} debe ser un objeto JSON.")
    return value


def validate_catalog(value: Any) -> dict[str, Any]:
    catalog = _require_object(value, "El catálogo")
    if catalog.get("schema_version") != "1.0":
        raise HarnessError("El catálogo debe usar schema_version 1.0.")
    cases = catalog.get("cases")
    thresholds = catalog.get("thresholds")
    channels = catalog.get("channels")
    if not isinstance(cases, list) or not cases:
        raise HarnessError("El catálogo debe declarar casos.")
    if not isinstance(thresholds, dict) or not thresholds:
        raise HarnessError("El catálogo debe declarar umbrales calculables.")
    if not isinstance(channels, dict) or set(channels) != {"candidate", "stable"}:
        raise HarnessError("El catálogo debe declarar los canales candidate y stable.")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise HarnessError("Cada caso del catálogo debe ser un objeto.")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"FX-[0-9]{2}", case_id):
            raise HarnessError(f"ID de caso inválido: {case_id!r}")
        if case_id in ids:
            raise HarnessError(f"Caso duplicado: {case_id}")
        ids.add(case_id)
        if case.get("mode") not in {"automated", "semantic", "human", "pilot"}:
            raise HarnessError(f"Modo inválido en {case_id}.")
        if not isinstance(case.get("critical"), bool):
            raise HarnessError(f"{case_id} debe declarar critical como booleano.")
        evidence = case.get("evidence")
        if not isinstance(evidence, list) or not all(
            isinstance(item, str) and re.fullmatch(r"(?:eval|test|profile):[A-Za-z0-9._-]+", item)
            for item in evidence
        ):
            raise HarnessError(f"Evidencia inválida en {case_id}.")
        if case.get("mode") == "automated" and not evidence:
            raise HarnessError(f"{case_id} es automatizado pero no declara evidencia.")
    expected = {f"FX-{index:02d}" for index in range(1, 20)}
    if ids != expected:
        raise HarnessError(
            f"El catálogo debe cubrir FX-01 a FX-19; diferencia: {sorted(ids ^ expected)}"
        )
    fx01 = next(case for case in cases if case["id"] == "FX-01")
    if fx01.get("mode") != "semantic" or fx01.get("evidence") != []:
        raise HarnessError(
            "FX-01 debe ser semántico y permanecer sin evidencia hasta una conversación controlada."
        )
    extension_cases = catalog.get("extension_cases")
    if not isinstance(extension_cases, list) or not extension_cases:
        raise HarnessError("El catálogo debe declarar los casos de extensión v0.6.")
    extension_ids: set[str] = set()
    for case in extension_cases:
        if not isinstance(case, dict):
            raise HarnessError("Cada caso de extensión debe ser un objeto.")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"FX-[0-9]{2}", case_id):
            raise HarnessError(f"ID de caso de extensión inválido: {case_id!r}")
        if case_id in ids or case_id in extension_ids:
            raise HarnessError(f"Caso de extensión duplicado: {case_id}")
        extension_ids.add(case_id)
        if case.get("mode") not in {"semantic", "human"}:
            raise HarnessError(f"{case_id} debe requerir evaluación semántica o humana.")
        if not isinstance(case.get("critical"), bool):
            raise HarnessError(f"{case_id} debe declarar critical como booleano.")
        if case.get("evidence") != []:
            raise HarnessError(
                f"{case_id} no puede declarar evidencia antes de ejecutar el corpus v0.6."
            )
    if extension_ids != {"FX-20", "FX-21"}:
        raise HarnessError("La extensión v0.6 debe declarar exactamente FX-20 y FX-21.")
    if "definition-conversation" not in channels["candidate"].get("optional", []):
        raise HarnessError(
            "Candidate debe mostrar definition-conversation como evidencia opcional."
        )
    if "definition-conversation" not in channels["stable"].get("required", []):
        raise HarnessError(
            "Stable debe exigir el canal definition-conversation."
        )
    for name, threshold in thresholds.items():
        if not isinstance(threshold, dict):
            raise HarnessError(f"Umbral inválido: {name}")
        if threshold.get("direction") not in {"higher", "lower"}:
            raise HarnessError(f"Dirección de umbral inválida: {name}")
        if not isinstance(threshold.get("target"), (int, float)):
            raise HarnessError(f"Target de umbral inválido: {name}")
    return catalog


def validate_corpus(value: Any) -> dict[str, Any]:
    corpus = _require_object(value, "El corpus")
    if corpus.get("schema_version") != "1.0":
        raise HarnessError("El corpus debe usar schema_version 1.0.")
    cases = corpus.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        raise HarnessError("El corpus de activación debe contener al menos diez casos.")
    ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise HarnessError("Cada entrada del corpus debe ser un objeto.")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(r"ACT-[0-9]{3}", case_id):
            raise HarnessError(f"ID de activación inválido: {case_id!r}")
        if case_id in ids:
            raise HarnessError(f"Caso de activación duplicado: {case_id}")
        ids.add(case_id)
        expected = case.get("expected_skill")
        if expected is not None and expected not in ALLOWED_SKILLS:
            raise HarnessError(f"Skill esperada inválida en {case_id}: {expected!r}")
        if not isinstance(case.get("text"), str) or not case["text"].strip():
            raise HarnessError(f"Texto vacío en {case_id}.")
        if not isinstance(case.get("critical"), bool):
            raise HarnessError(f"{case_id} debe declarar critical como booleano.")
    return corpus


def validate_definition_corpus(value: Any, catalog: dict[str, Any]) -> dict[str, Any]:
    corpus = _require_object(value, "El corpus de definición v0.6")
    if corpus.get("schema_version") != "1.0":
        raise HarnessError("El corpus de definición debe usar schema_version 1.0.")
    if corpus.get("execution_status") != "not-run" or corpus.get("evidence") != []:
        raise HarnessError(
            "El corpus de definición debe permanecer not-run y sin evidencia hasta una ejecución controlada."
        )
    cases = corpus.get("cases")
    if not isinstance(cases, list):
        raise HarnessError("El corpus de definición debe declarar casos.")
    ids: set[str] = set()
    allowed_dimensions = {
        "premise_control",
        "question_relevance",
        "coverage_clarity",
        "interaction_completeness",
        "visual_traceability",
        "human_validation",
        "information_protection",
    }
    for case in cases:
        if not isinstance(case, dict):
            raise HarnessError("Cada caso de definición debe ser un objeto.")
        case_id = case.get("id")
        if (
            not isinstance(case_id, str)
            or case_id in ids
            or case_id not in {"FX-01", "FX-20", "FX-21"}
        ):
            raise HarnessError(f"Caso de definición inválido o duplicado: {case_id!r}")
        ids.add(case_id)
        if not isinstance(case.get("input"), str) or not case["input"].strip():
            raise HarnessError(f"{case_id} debe declarar una entrada sintética.")
        for field in ("expected", "forbidden", "review_dimensions"):
            items = case.get(field)
            if not isinstance(items, list) or not items:
                raise HarnessError(f"{case_id} debe declarar {field}.")
        dimensions = set(case["review_dimensions"])
        if not dimensions.issubset(allowed_dimensions):
            raise HarnessError(f"{case_id} contiene dimensiones de revisión desconocidas.")
    expected_ids = {"FX-01", *[case["id"] for case in catalog["extension_cases"]]}
    if ids != expected_ids:
        raise HarnessError(
            f"El corpus de definición no coincide con el catálogo: {sorted(ids ^ expected_ids)}"
        )
    evaluation = corpus.get("evaluation")
    if not isinstance(evaluation, dict) or evaluation.get("required_review") != [
        "semantic",
        "human",
    ]:
        raise HarnessError("El corpus de definición debe exigir revisión semántica y humana.")
    return corpus


def evaluate_definition_conversation(corpus: dict[str, Any]) -> dict[str, Any]:
    if corpus.get("execution_status") != "not-run" or corpus.get("evidence") != []:
        raise HarnessError(
            "No existe todavía un contrato de observaciones ejecutadas para definición v0.6."
        )
    return {
        "status": "not-run",
        "observed": 0,
        "total": len(corpus["cases"]),
        "corpus_id": corpus["corpus_id"],
        "required_review": corpus["evaluation"]["required_review"],
    }


def validate_fixture_manifest(
    plugin_root: Path = PLUGIN_ROOT, manifest_value: Any | None = None
) -> dict[str, Any]:
    manifest = _require_object(
        manifest_value
        if manifest_value is not None
        else _load_json(plugin_root / "quality" / "fixture-manifest.json"),
        "El manifiesto de fixtures",
    )
    errors: list[str] = []
    if manifest.get("schema_version") != "1.0":
        errors.append("El manifiesto de fixtures debe usar schema_version 1.0.")
    if manifest.get("classification") != "synthetic-only":
        errors.append("Los fixtures deben estar clasificados como synthetic-only.")
    relative_root = manifest.get("root")
    if relative_root != "tests/fixtures":
        errors.append("La raíz de fixtures debe ser tests/fixtures.")
        relative_root = "tests/fixtures"
    fixtures_root = (plugin_root / relative_root).resolve()
    declared: set[str] = set()
    entries = manifest.get("fixtures")
    if not isinstance(entries, list) or not entries:
        errors.append("El manifiesto debe declarar fixtures.")
        entries = []
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("Cada fixture declarado debe ser un objeto.")
            continue
        relative = entry.get("path")
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or Path(relative).suffix != ".json"
        ):
            errors.append(f"Ruta de fixture inválida: {relative!r}")
            continue
        if relative in declared:
            errors.append(f"Fixture duplicado: {relative}")
            continue
        declared.add(relative)
        path = fixtures_root / relative
        try:
            path.resolve().relative_to(fixtures_root)
        except ValueError:
            errors.append(f"Fixture fuera de la raíz: {relative}")
            continue
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            errors.append(f"Fixture enlazado no permitido: {relative}")
            continue
        if not path.is_file():
            errors.append(f"Fixture ausente: {relative}")
            continue
        try:
            payload = _load_json(path)
        except HarnessError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(payload, dict) or payload.get("id") != entry.get("id"):
            errors.append(f"ID no coincidente en {relative}.")
        expected_hash = entry.get("sha256")
        actual_hash = _sha256_file(path)
        if expected_hash != actual_hash:
            errors.append(
                f"Hash de fixture no coincidente en {relative}: {actual_hash}"
            )
    actual = {
        path.name
        for path in fixtures_root.glob("*.json")
        if path.is_file() and not path.is_symlink()
    }
    undeclared = sorted(actual - declared)
    missing = sorted(declared - actual)
    if undeclared:
        errors.append(f"Fixtures no declarados: {undeclared}")
    if missing:
        errors.append(f"Fixtures declarados ausentes: {missing}")
    return {
        "status": "passed" if not errors else "failed",
        "fixture_count": len(declared),
        "errors": errors,
    }


def validate_observations(value: Any, corpus: dict[str, Any]) -> dict[str, Any]:
    observations = _require_object(value, "Las observaciones")
    required = {
        "schema_version",
        "corpus_id",
        "corpus_sha256",
        "evaluator_context",
        "activation_results",
        "document_reviews",
    }
    if set(observations) != required:
        raise HarnessError(
            f"Campos de observaciones inválidos: {sorted(set(observations) ^ required)}"
        )
    if observations.get("schema_version") != "1.0":
        raise HarnessError("Las observaciones deben usar schema_version 1.0.")
    if observations.get("corpus_id") != corpus.get("corpus_id"):
        raise HarnessError("corpus_id no coincide con el corpus evaluado.")
    corpus_hash = _sha256_bytes(_canonical_bytes(corpus))
    if observations.get("corpus_sha256") != corpus_hash:
        raise HarnessError("corpus_sha256 no coincide; las observaciones están obsoletas.")
    context = observations.get("evaluator_context")
    if not isinstance(context, dict) or set(context) != {
        "kind",
        "product",
        "executed_on",
        "evidence_reference",
    }:
        raise HarnessError("evaluator_context no respeta el contrato saneado.")
    if context.get("kind") not in {"controlled-codex-session", "human-review"}:
        raise HarnessError("kind de evaluador no soportado.")
    if context.get("product") != "Codex":
        raise HarnessError("Las observaciones de esta implementación deben proceder de Codex.")
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", str(context.get("executed_on"))):
        raise HarnessError("executed_on debe ser una fecha ISO.")
    if not isinstance(context.get("evidence_reference"), str) or len(
        context["evidence_reference"].strip()
    ) < 3:
        raise HarnessError("Falta una referencia de evidencia saneada.")
    activation_results = observations.get("activation_results")
    document_reviews = observations.get("document_reviews")
    if not isinstance(activation_results, list) or not isinstance(document_reviews, list):
        raise HarnessError("activation_results y document_reviews deben ser listas.")
    seen: set[str] = set()
    for result in activation_results:
        if not isinstance(result, dict) or set(result) != {"case_id", "actual_skill"}:
            raise HarnessError("Resultado de activación inválido.")
        case_id = result.get("case_id")
        actual = result.get("actual_skill")
        if not isinstance(case_id, str) or not re.fullmatch(r"ACT-[0-9]{3}", case_id):
            raise HarnessError(f"case_id observado inválido: {case_id!r}")
        if case_id in seen:
            raise HarnessError(f"Observación duplicada: {case_id}")
        seen.add(str(case_id))
        if actual is not None and actual not in ALLOWED_SKILLS:
            raise HarnessError(f"Skill observada inválida en {case_id}: {actual!r}")
    for review in document_reviews:
        if not isinstance(review, dict) or set(review) != {
            "artifact_reference",
            "scores",
        }:
            raise HarnessError("Revisión documental inválida.")
        scores = review.get("scores")
        if not isinstance(review.get("artifact_reference"), str) or len(
            review["artifact_reference"].strip()
        ) < 3:
            raise HarnessError("artifact_reference debe ser una referencia saneada.")
        if not isinstance(scores, dict) or set(scores) != SCORE_KEYS:
            raise HarnessError("La revisión documental debe incluir las diez dimensiones.")
        if any(not isinstance(score, int) or not 1 <= score <= 5 for score in scores.values()):
            raise HarnessError("Las puntuaciones documentales deben ser enteros entre 1 y 5.")
    return observations


def evaluate_activation(
    corpus: dict[str, Any], observations: dict[str, Any] | None, thresholds: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, float | int], list[str]]:
    if observations is None:
        return {"status": "not-run", "observed": 0, "total": len(corpus["cases"])}, {}, []
    expected = {case["id"]: case for case in corpus["cases"]}
    actual = {result["case_id"]: result["actual_skill"] for result in observations["activation_results"]}
    unknown = sorted(set(actual) - set(expected))
    if unknown:
        raise HarnessError(f"Observaciones para casos inexistentes: {unknown}")
    correct_selected = 0
    predicted_selected = 0
    expected_selected = 0
    correct_routes = 0
    critical_failures: list[str] = []
    for case_id, result in actual.items():
        target = expected[case_id]["expected_skill"]
        if result is not None:
            predicted_selected += 1
        if target is not None:
            expected_selected += 1
        if result == target:
            correct_routes += 1
            if target is not None:
                correct_selected += 1
        elif expected[case_id]["critical"]:
            critical_failures.append(
                f"{case_id}: routing esperado {target!r}, observado {result!r}"
            )
    count = len(actual)
    precision = correct_selected / predicted_selected if predicted_selected else 0.0
    recall = correct_selected / expected_selected if expected_selected else 0.0
    accuracy = correct_routes / count if count else 0.0
    metrics: dict[str, float | int] = {
        "activation_samples": count,
        "activation_precision": round(precision, 6),
        "activation_recall": round(recall, 6),
        "routing_accuracy": round(accuracy, 6),
    }
    complete = count == len(expected)
    failures: list[str] = []
    for name in ("activation_precision", "activation_recall", "routing_accuracy"):
        rule = thresholds[name]
        if count < rule.get("minimum_samples", 0):
            failures.append(f"{name}: muestra insuficiente ({count})")
        elif metrics[name] < rule["target"]:
            failures.append(f"{name}: {metrics[name]} < {rule['target']}")
    status = "passed" if complete and not failures and not critical_failures else "failed" if critical_failures or (complete and failures) else "incomplete"
    return {
        "status": status,
        "observed": count,
        "total": len(expected),
        "failures": failures,
    }, metrics, critical_failures


def evaluate_document_reviews(
    observations: dict[str, Any] | None, thresholds: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, float | int]]:
    if observations is None or not observations["document_reviews"]:
        return {"status": "not-run", "reviewed": 0}, {}
    artifact_averages = [
        sum(review["scores"].values()) / len(review["scores"])
        for review in observations["document_reviews"]
    ]
    average = round(sum(artifact_averages) / len(artifact_averages), 6)
    minimum = round(min(artifact_averages), 6)
    metrics: dict[str, float | int] = {
        "document_review_samples": len(artifact_averages),
        "document_review_average": average,
        "document_review_minimum": minimum,
    }
    failures = []
    if average < thresholds["document_review_average"]["target"]:
        failures.append("La media documental no alcanza 4 sobre 5.")
    if minimum < thresholds["document_review_minimum"]["target"]:
        failures.append("Existe un documento con media inferior a 3 sobre 5.")
    return {
        "status": "passed" if not failures else "failed",
        "reviewed": len(artifact_averages),
        "failures": failures,
    }, metrics


def evaluate_pilot(summary: dict[str, Any] | None) -> dict[str, Any]:
    if summary is None:
        return {"status": "not-run", "decision": "not-evaluated"}
    if summary.get("schema_version") != "1.0":
        raise HarnessError("El resumen de piloto debe usar schema_version 1.0.")
    decision = summary.get("decision")
    if not isinstance(decision, dict):
        raise HarnessError("El resumen de piloto no contiene una decisión válida.")
    status = decision.get("status")
    if status == "go":
        channel_status = "passed"
    elif status in {"not-evaluated", "go-conditioned"}:
        channel_status = "incomplete"
    elif status in {"no-go", "withdrawal"}:
        channel_status = "failed"
    else:
        raise HarnessError(f"Decisión de piloto no soportada: {status!r}")
    return {
        "status": channel_status,
        "decision": status,
        "project_count": summary.get("project_count"),
        "participant_count": summary.get("participant_count"),
        "sample_sufficient": summary.get("sample_sufficient"),
    }


def _run_command(check_id: str, command: list[str], json_output: bool = False, timeout: int = 600) -> tuple[dict[str, Any], Any | None, str]:
    process = subprocess.run(
        command,
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout,
    )
    combined = f"{process.stdout}\n{process.stderr}".strip()
    payload: Any | None = None
    parse_error = ""
    if json_output and process.returncode == 0:
        try:
            payload = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            parse_error = f"salida JSON inválida: {exc}"
    passed = process.returncode == 0 and not parse_error
    summary = "exit=0" if passed else f"exit={process.returncode}"
    if parse_error:
        summary = f"{summary}; {parse_error}"
    return {
        "id": check_id,
        "status": "passed" if passed else "failed",
        "critical": True,
        "summary": summary,
    }, payload, combined


def run_automated(include_complete_profile: bool) -> tuple[list[dict[str, Any]], dict[str, float | int], list[str]]:
    checks: list[dict[str, Any]] = []
    metrics: dict[str, float | int] = {}
    critical_failures: list[str] = []
    fixture_result = validate_fixture_manifest()
    checks.append(
        {
            "id": "fixture-integrity",
            "status": fixture_result["status"],
            "critical": True,
            "summary": f"fixtures={fixture_result['fixture_count']}",
        }
    )
    if fixture_result["errors"]:
        critical_failures.extend(fixture_result["errors"])
    commands = [
        (
            "plugin-contract",
            [sys.executable, "-X", "utf8", "scripts/validate_plugin_contract.py", "."],
            False,
            120,
        ),
        (
            "reference-profile-structure",
            [sys.executable, "-X", "utf8", "scripts/validate_reference_profile.py"],
            False,
            120,
        ),
        (
            "unit-tests",
            [sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
            False,
            600,
        ),
        (
            "deterministic-evals",
            [sys.executable, "-X", "utf8", "tests/run_evals.py"],
            True,
            600,
        ),
    ]
    if include_complete_profile:
        commands.append(
            (
                "reference-profile-complete",
                [sys.executable, "-X", "utf8", "scripts/run_reference_profile_gate.py", "--runtime", "docker", "--containers", "--json"],
                True,
                1800,
            )
        )
    for check_id, command, json_output, timeout in commands:
        check, payload, output = _run_command(check_id, command, json_output, timeout)
        checks.append(check)
        if check["status"] != "passed":
            critical_failures.append(f"{check_id}: {check['summary']}")
            continue
        if check_id == "reference-profile-structure":
            metrics["profile_structure_gate"] = 1
        elif check_id == "unit-tests":
            match = re.search(r"Ran ([0-9]+) tests?", output)
            metrics["unit_tests_passed"] = int(match.group(1)) if match else 0
        elif check_id == "deterministic-evals" and isinstance(payload, dict):
            results = payload.get("results", [])
            passed_count = sum(1 for result in results if result.get("passed") is True)
            total = len(results)
            metrics["automated_eval_cases"] = total
            metrics["automated_eval_pass_rate"] = round(passed_count / total, 6) if total else 0.0
            for result in results:
                if result.get("passed") is not True:
                    critical_failures.append(f"Eval determinista fallida: {result.get('id')}")
        elif check_id == "reference-profile-complete" and isinstance(payload, dict):
            metrics["profile_complete_gate"] = 1 if payload.get("complete_gate") is True else 0
            if payload.get("complete_gate") is not True:
                critical_failures.append("El gate completo del perfil no quedó acreditado.")
    metrics["critical_failures"] = len(critical_failures)
    return checks, metrics, critical_failures


def compare_metrics(current: dict[str, float | int], baseline: dict[str, Any]) -> dict[str, Any]:
    baseline_metrics = baseline.get("metrics")
    if not isinstance(baseline_metrics, dict):
        raise HarnessError("La baseline no declara metrics.")
    lower_is_better = {"critical_failures"}
    comparisons = []
    regressions = []
    for name in sorted(set(current) & set(baseline_metrics)):
        old = baseline_metrics[name]
        new = current[name]
        if not isinstance(old, (int, float)) or not isinstance(new, (int, float)):
            continue
        regressed = new > old if name in lower_is_better else new < old
        comparisons.append(
            {"metric": name, "baseline": old, "current": new, "regressed": regressed}
        )
        if regressed:
            regressions.append(f"{name}: {new} frente a {old}")
    return {
        "baseline_version": baseline.get("plugin_version"),
        "status": "failed" if regressions else "passed",
        "comparisons": comparisons,
        "regressions": regressions,
        "not_compared": sorted(set(baseline_metrics) - set(current)),
    }


def build_report(
    evaluated_on: str,
    channel: str,
    observations_path: Path | None,
    pilot_summary_path: Path | None,
    baseline_path: Path,
    include_complete_profile: bool,
) -> dict[str, Any]:
    catalog = validate_catalog(_load_json(CATALOG_PATH))
    corpus = validate_corpus(_load_json(CORPUS_PATH))
    definition_corpus = validate_definition_corpus(
        _load_json(DEFINITION_CORPUS_PATH), catalog
    )
    manifest = _require_object(_load_json(MANIFEST_PATH), "El manifest del plugin")
    if definition_corpus.get("plugin_version") != manifest.get("version"):
        raise HarnessError(
            "El corpus de definición debe coincidir con la versión del manifest."
        )
    observations = None
    if observations_path is not None:
        observations = validate_observations(_load_json(observations_path), corpus)
    pilot_summary = None
    if pilot_summary_path is not None:
        pilot_summary = _require_object(
            _load_json(pilot_summary_path), "El resumen de piloto"
        )
    checks, metrics, critical_failures = run_automated(include_complete_profile)
    activation, activation_metrics, activation_critical = evaluate_activation(
        corpus, observations, catalog["thresholds"]
    )
    document_review, document_metrics = evaluate_document_reviews(
        observations, catalog["thresholds"]
    )
    metrics.update(activation_metrics)
    metrics.update(document_metrics)
    critical_failures.extend(activation_critical)
    metrics["critical_failures"] = len(critical_failures)
    baseline = _require_object(_load_json(baseline_path), "La baseline")
    comparison = compare_metrics(metrics, baseline)
    channels = {
        "automated": {
            "status": "passed" if all(check["status"] == "passed" for check in checks) else "failed"
        },
        "fixture-integrity": next(check for check in checks if check["id"] == "fixture-integrity"),
        "profile-complete": {
            "status": next(
                (
                    check["status"]
                    for check in checks
                    if check["id"] == "reference-profile-complete"
                ),
                "not-run",
            )
        },
        "regression": {"status": comparison["status"]},
        "definition-conversation": evaluate_definition_conversation(
            definition_corpus
        ),
        "activation": activation,
        "document-review": document_review,
        "pilot": evaluate_pilot(pilot_summary),
    }
    required = catalog["channels"][channel]["required"]
    blockers = list(critical_failures)
    if comparison["regressions"]:
        blockers.extend(f"Regresión: {item}" for item in comparison["regressions"])
    missing_evidence = [
        name
        for name in required
        if channels[name]["status"] in {"not-run", "incomplete"}
    ]
    failed_channels = [
        name for name in required if channels[name]["status"] == "failed"
    ]
    blockers.extend(f"Canal requerido fallido: {name}" for name in failed_channels)
    if blockers:
        gate_status = "failed"
    elif missing_evidence:
        gate_status = "incomplete"
    else:
        gate_status = "passed"
    return {
        "schema_version": "1.0",
        "suite": catalog["suite"],
        "plugin_version": manifest.get("version"),
        "evaluated_on": evaluated_on,
        "channel": channel,
        "inputs": {
            "catalog_sha256": _sha256_bytes(_canonical_bytes(catalog)),
            "corpus_sha256": _sha256_bytes(_canonical_bytes(corpus)),
            "definition_corpus_sha256": _sha256_bytes(
                _canonical_bytes(definition_corpus)
            ),
            "fixture_manifest_sha256": _sha256_file(FIXTURE_MANIFEST_PATH),
            "observations_sha256": _sha256_file(observations_path) if observations_path else None,
            "pilot_summary_sha256": _sha256_file(pilot_summary_path) if pilot_summary_path else None,
            "baseline_sha256": _sha256_file(baseline_path),
        },
        "checks": checks,
        "channels": channels,
        "metrics": dict(sorted(metrics.items())),
        "critical_failures": sorted(critical_failures),
        "comparison": comparison,
        "gate": {
            "status": gate_status,
            "eligible": gate_status == "passed",
            "blockers": sorted(set(blockers)),
            "missing_evidence": sorted(missing_evidence),
        },
    }


def _atomic_write(path: Path, value: dict[str, Any], force: bool) -> None:
    destination = path.expanduser().resolve()
    if destination.exists() and not force:
        raise HarnessError(f"El reporte ya existe; use --force para reemplazarlo: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary_name, destination)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=("candidate", "stable"), default="candidate")
    parser.add_argument("--date", default=date.today().isoformat(), dest="evaluated_on")
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--pilot-summary", type=Path)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--include-complete-profile", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", args.evaluated_on):
        print("ERROR: --date debe usar YYYY-MM-DD.", file=sys.stderr)
        return 2
    try:
        report = build_report(
            args.evaluated_on,
            args.channel,
            args.observations,
            args.pilot_summary,
            args.baseline.expanduser().resolve(),
            args.include_complete_profile,
        )
        if args.output:
            _atomic_write(args.output, report, args.force)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if report["gate"]["status"] == "passed":
            return 0
        return 3 if report["gate"]["status"] == "incomplete" else 2
    except (HarnessError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

"""Reproducible synthetic journey and bounded real-source conversion; no network.

This measures scripted runtime work, not human/agent planning or real delivery.
All application mutations take place in owned fixtures/copies.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile

import sdd
from test_sdd import FACTS, fixture, meta, put, update


SOURCE_COMMIT = "e55f87a122aa6e3595d8a26d2bb729dd867cad26"


def measure(fn):
    start = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - start


def distribution(values, percentile=False):
    result = {"samples": len(values), "min_s": min(values), "median_s": statistics.median(values),
              "max_s": max(values)}
    if percentile:
        result["empirical_p95_s"] = sorted(values)[math.ceil(len(values) * .95) - 1]
    return result


def journey(repetitions):
    runs = []
    for _ in range(repetitions):
        with tempfile.TemporaryDirectory(prefix="sdd-v5-journey-") as tmp:
            root = Path(tmp)
            fixture(root)
            put(root, "product.py", "def visible(value):\n    return value is not None\n")
            start = time.perf_counter()
            _, prepare = measure(lambda: fixture(root))
            first_patch = time.perf_counter() - start
            _, implementation = measure(lambda: put(root, "product.py", "def visible(value):\n    return bool(value)\n"))
            tested, validation = measure(lambda: sdd.check_task(root, "T-001", "C1"))
            put(root, "README.md", "Documentación corregida; entradas de C1 intactas.\n")
            reused, reuse = measure(lambda: sdd.check_task(root, "T-001", "C1"))
            revised = update(root)
            closed, closure = measure(lambda: sdd.close(root, "T-001", revised, FACTS))
            total = time.perf_counter() - start
            assert tested["status"] == "passed" and reused["status"] == "reused"
            assert closed["status"] == "applied"
            documents = list((root / "docs/sdd").rglob("*.md"))
            runs.append({"prepare_s": prepare, "first_patch_s": first_patch,
                         "implementation_s": implementation, "validation_s": validation,
                         "reuse_s": reuse, "closure_s": closure, "total_scripted_s": total,
                         "runtime_operations": 3, "test_executions": 1, "test_reuses": 1,
                         "task_files": 2, "unit_files": 1,
                         "durable_document_bytes": sum(p.stat().st_size for p in documents),
                         "pending_journals": int((root / ".sdd-work/journal.json").exists()),
                         "task_temporaries": len(list((root / ".sdd-work/tmp").glob("*"))),
                         "delivery": FACTS})
    return {"runs": runs, "total": distribution([r["total_scripted_s"] for r in runs]),
            "closure": distribution([r["closure_s"] for r in runs]),
            "measurement": "Scripted authoring, known tiny patch, one real local test, reuse and closure",
            "not_measured": ["agent planning/reading", "human work", "real delivery", "billing"]}


def history(repetitions):
    results = []
    with tempfile.TemporaryDirectory(prefix="sdd-v5-history-") as tmp:
        root = Path(tmp)
        fixture(root)
        previous = 0
        baseline = None
        for count in (10, 100, 1000):
            for index in range(previous, count):
                put(root, f"docs/sdd/tareas/old-{index}/plan.md", "Closed unrelated task\n" * 50)
            previous = count
            durations = []
            for _ in range(repetitions):
                result, elapsed = measure(lambda: sdd.context(root, "T-001"))
                durations.append(elapsed)
            if baseline is None:
                baseline = result
            assert result == baseline
            results.append({"history_files": count, "context_bytes": result["bytes"],
                            "files_read": result["files_read"], **distribution(durations, True)})
        cold = []
        for _ in range(30):
            _, elapsed = measure(lambda: subprocess.run(
                [sys.executable, "-B", "-X", "utf8", str(Path(sdd.__file__)), str(root), "context", "T-001"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True))
            cold.append(elapsed)
    return {"warm": results, "new_process": distribution(cold),
            "cold_limit": "New Python process; OS/disk cache not flushed, not a cold-machine claim"}


def real_conversion(repo, output):
    """Convert one bounded, inline 3.1 task from the supplied real repository.

    This is an explicit editorial mapping for this fixture, not a generic
    semantic migration algorithm. It does not certify full-project retirement.
    """
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args])

    initial_status = git("status", "--porcelain")
    index = json.loads(git("show", SOURCE_COMMIT + ":.lks-sdd/project.json"))["elements"]
    selected = {"TASK-7400", "PLAN-7400", "FR-7400", "AC-7400", "TEST-7400"}
    paths = sorted({entry["path"] for entry in index.values() if entry["id"] in selected})
    if len(paths) != 3:
        raise ValueError("Source shape changed; review the bounded mapping")
    root = output / "real-case"
    root.mkdir(parents=True, exist_ok=False)
    source_hashes, elements = {}, {}
    for name in paths:
        raw = git("show", SOURCE_COMMIT + ":" + name)
        source_hashes[name] = sdd.digest(raw)
        put(root, name, raw)
        for metadata, body in sdd.legacy_read(raw):
            if metadata["id"] not in selected:
                raise ValueError("Additional source meaning needs reconciliation")
            elements[metadata["id"]] = (metadata, body)
    if set(elements) != selected:
        raise ValueError("Incomplete source extraction")
    recovery_name = ".sdd-work/recovery/source.zip"
    recovery = sdd.path_at(root, recovery_name)
    recovery.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(recovery, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in paths:
            archive.writestr(name, sdd.read(root, name))
    recovery_info = {"kind": "zip", "path": recovery_name,
                     "sha256": sdd.digest(recovery.read_bytes()), "owner": "v5 controlled experiment",
                     "expires": (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()}
    task_id, unit = "T-7400", "maestros-demostracion"
    # The source contract is preserved literally. Exact repeated paragraphs are
    # stored once; no generated paraphrase is presented as a confirmed requirement.
    paragraphs, seen = [], set()
    for key in ("FR-7400", "AC-7400"):
        for paragraph in elements[key][1].split("\n\n"):
            if paragraph not in seen:
                seen.add(paragraph)
                paragraphs.append(paragraph)
    unit_body = "# Maestros y datos de demostración\n\n" + "\n\n".join(paragraphs)
    unit_body += "\n\nEste contrato no acredita despliegue ni aceptación de la implementación."
    task_body = ("# Completar cuatro maestros\n\nPetición y alcance: [contrato de maestros](../../especificaciones/" + unit + ".md).\n\n"
                 "Conservar el cambio solicitado en TASK-7400: descripción persistente de modelos, "
                 "datos de demostración coherentes y retirada visual/XLSX de Stock y Almacén, "
                 "preservando inventario interno, permisos, multitenencia y atomicidad.\n\n"
                 "Criterios de aceptación: AC-7400, en la especificación enlazada. "
                 "Sin cambios sobre bases instaladas ni acceso a producción.\n\n"
                 "La autoridad de origen queda como antecedente, sin autorizar ejecutar esta copia. "
                 "El registro fuente combina estado ready con continuation=reconciliation-required "
                 "y health=needs-reverification; la copia conserva esa necesidad de reconciliación.")
    plan_body = ("# Plan, seguimiento y resultado\n\n" + elements["PLAN-7400"][1] +
                 "\n\n## Comprobaciones pendientes de vigencia\n\n" + elements["TEST-7400"][1] +
                 "\n\n## Decisión de conversión del experimento\n\n"
                 "PLAN-7400 y TEST-7400 se reúnen aquí. FR-7400 y AC-7400 están en la unidad funcional. "
                 "El expediente EVID/checkpoint del mecanismo anterior se sustituye por resultados "
                 "en este plan; no se elimina ninguna prueba, revisión de diff, control Sonar, "
                 "restricción de entorno o aceptación pendiente. Las referencias anteriores son "
                 "identificadores de procedencia, no un runtime ni rutas operativas.\n\n"
                 "La conversión documental no prueba implementación, integración, despliegue o aceptación. "
                 "Antes de ejecutar deben reconciliarse evidencia y autoridad actuales.")
    # Preserve task-only operational constraints in the one plan rather than
    # retaining the legacy task as a second operational document.
    task_specific = elements["TASK-7400"][1].split("Aplicar integralmente", 1)[-1]
    task_specific = task_specific.replace("PLAN-7400, FR-7400, AC-7400 y TEST-7400.",
                                          "este plan y la especificación enlazada.")
    task_specific = task_specific.replace("Una ejecución normativa con checkpoint antes de revisión o bloqueo.",
                                          "Actualizar este plan antes de revisión o bloqueo.")
    task_specific = task_specific.replace("No afirmar done sin EVID formal y aceptación;",
                                          "No afirmar aceptación sin resultado comprobado y aceptación explícita;")
    plan_body += "\n\n## Restricciones de ejecución conservadas\n\nAplicar integralmente" + task_specific
    provenance = {"commit": SOURCE_COMMIT, "source_ids": sorted(selected)}
    task_meta = meta("task", task_id, units=[unit], owner=elements["TASK-7400"][0]["data"]["owner"],
                     policies=[], provenance=provenance)
    unit_meta = meta("unit", unit, depends_on=[], contract_state="confirmed-in-source", provenance=provenance)
    unit_raw = sdd.document(unit_meta, unit_body)
    plan_meta = meta("plan", task_id, state="bloqueado", next="Reconciliar evidencia y autoridad de ejecución",
                     blockers=["needs-reverification; continuation=reconciliation-required"],
                     bases={sdd.unit_path(unit): sdd.digest(unit_raw)}, checks={},
                     delivery={k: "not-established-by-this-extraction" for k in FACTS}, provenance=provenance)
    targets = {sdd.unit_path(unit): unit_raw,
               sdd.task_path(task_id, "tarea"): sdd.document(task_meta, task_body),
               sdd.task_path(task_id, "plan"): sdd.document(plan_meta, plan_body)}
    resolution = {m["uid"]: "Mapped to " + ("unit" if key in {"FR-7400", "AC-7400"} else
                                             "task" if key == "TASK-7400" else "single plan")
                  for key, (m, _) in elements.items()}
    # Exercise a real unresolved conversion before supplying the explicit mapping.
    unresolved = dict(resolution)
    unresolved.pop(next(iter(unresolved)))
    try:
        sdd.migration_preview(root, paths, targets, resolution=unresolved, recovery_reference=recovery_info)
    except ValueError:
        assert all(sdd.digest(sdd.read(root, k)) == v for k, v in source_hashes.items())
    else:
        raise AssertionError("Unresolved mapping accepted")
    start = time.perf_counter()
    preview = sdd.migration_preview(root, paths, targets, resolution=resolution, recovery_reference=recovery_info)
    # Authorization is limited to these generated test copies by the prototype request.
    try:
        sdd.migrate(root, preview, preview["preview"], interrupt_after=1)
    except InterruptedError:
        pass
    sdd.resume(root)
    elapsed = time.perf_counter() - start
    assert all(sdd.read(root, name) is None for name in paths)
    assert len(list((root / "docs/sdd").rglob("*.md"))) == 3
    text = "\n".join(v.decode() for v in targets.values())
    for phrase in ("ceros iniciales", "aislamiento multitenant", "inventario interno", "sin escritura", "Sonar"):
        assert phrase in text, phrase
    assert git("status", "--porcelain") == initial_status
    result = {"status": "bounded-conversion-verified", "source_commit": SOURCE_COMMIT,
              "source_files": source_hashes, "source_elements": len(elements), "target_files": 3,
              "contract_units": 1, "converted_tasks": 1, "seconds_after_editorial_mapping": elapsed,
              "recovery_after_interruption": "passed", "unresolved_source_protection": "passed",
              "source_worktree_status_unchanged": True, "semantic_acceptance": "not-run",
              "full_project_migration": "not-run", "active_runtime_replacement": "not-run",
              "real_source_authority_reconciliation": "pending", "recovery": recovery_info,
              "copy": str(root)}
    # Small provenance/metrics only; no private original content in versioned output.
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sat-repo", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = {"version": "v5-experimental", "platform": platform.platform(), "python": sys.version,
              "started_utc": datetime.now(timezone.utc).isoformat(), "billed_tokens": None,
              "small_change_definition": "one unit, one acceptance criterion, one local assertion test",
              "journey": journey(10), "history": history(100)}
    if args.sat_repo:
        result["real_conversion"] = real_conversion(args.sat_repo, args.output)
    else:
        result["real_conversion"] = {"status": "not-run"}
    path = args.output / "results.json"
    path.write_text(sdd.encode(result), encoding="utf-8")
    print(sdd.encode({"results": str(path), "journey": result["journey"]["total"],
                      "closure": result["journey"]["closure"], "history": result["history"],
                      "real_conversion": result["real_conversion"]}))


if __name__ == "__main__":
    main()

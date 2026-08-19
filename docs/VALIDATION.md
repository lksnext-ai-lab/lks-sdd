# Validación local

Ejecutar desde la raíz del repositorio con Python 3:

```powershell
python C:\Users\j.ormazabal\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\lks-sdd-help
python C:\Users\j.ormazabal\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\lks-sdd-define
python C:\Users\j.ormazabal\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\lks-sdd-assess-readiness
python C:\Users\j.ormazabal\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\lks-sdd-implement
python C:\Users\j.ormazabal\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\lks-sdd-verify
python C:\Users\j.ormazabal\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\lks-sdd-adopt-existing
python C:\Users\j.ormazabal\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
python scripts\validate_reference_profile.py
python scripts\run_reference_profile_gate.py --runtime docker --containers
python scripts\validate_plugin_contract.py .
python scripts\validate_fixture_manifest.py .
python -m unittest discover -s tests -p "test_*.py" -v
python tests\run_evals.py
python scripts\run_quality_harness.py --channel candidate --date 2026-08-20 --baseline quality\baselines\v0.4.0.json --include-complete-profile
```

`validate_plugin_contract.py` comprueba manifiesto, skills implementadas, ausencia de componentes fuera de alcance, hashes de las fuentes canónicas y recursos declarados. `validate_reference_profile.py` comprueba el contrato y el lock H0. `validate_fixture_manifest.py` bloquea altas no declaradas y deriva de los fixtures sintéticos. El harness M4 vuelve a ejecutar las comprobaciones automatizables, calcula umbrales y compara contra la baseline; use `--include-complete-profile` para incorporar también Docker en su reporte. El gate completo requiere Docker y red, levanta servicios temporales y siempre ejecuta `compose down --volumes`.

El canal `stable` requiere además `--observations` con resultados reales de activación y revisión documental, más la evidencia agregada de M5. Si faltan, el harness devuelve `incomplete` con código `3`; nunca los presenta como superados.

La infraestructura M5 se comprueba con la suite y con:

```powershell
python scripts\manage_pilot.py validate-config pilot\pilot-config.example.json
python scripts\build_candidate_package.py --date 2026-08-20 --source-commit COMMIT_COMPLETO --output C:\ruta\externa\lks-sdd-v0.5.0
```

La configuración de ejemplo debe devolver `blocked` con código `3`: demuestra que no puede arrancar sin muestra, aliases, responsables, canal confidencial, checksum y rollback. El builder exige una carpeta externa inexistente.

Para validar un proyecto consumidor ya inicializado:

```powershell
python scripts\validate_project.py C:\ruta\al\proyecto
python scripts\validate_spec.py C:\ruta\al\proyecto
python scripts\check_traceability.py C:\ruta\al\proyecto --increment INC-001
python skills\lks-sdd-assess-readiness\scripts\assess_readiness.py C:\ruta\al\proyecto --increment INC-001
```

La adopción usa `inspect_repository.py`, `validate_adoption.py` y `materialize_adoption.py` en ese orden. La migración usa `migrate_project.py --dry-run` antes de `--apply`; el backup debe estar fuera del proyecto. Las vistas cliente se previsualizan con `render_client_view.py --dry-run` y se escriben solo con autorización y hash coincidente.

Los códigos `0`, `2` y `3` significan respectivamente éxito/listo, contrato inválido o readiness bloqueado. Un resultado listo no autoriza implementación; la confirmación de la persona usuaria sigue siendo independiente.

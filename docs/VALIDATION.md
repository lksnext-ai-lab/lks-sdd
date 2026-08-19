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
python -m unittest discover -s tests -p "test_*.py" -v
python tests\run_evals.py
```

`validate_plugin_contract.py` comprueba manifiesto, skills implementadas, ausencia de componentes fuera de alcance, hashes de las fuentes canónicas y recursos declarados. `validate_reference_profile.py` comprueba el contrato y el lock H0. El gate completo requiere Docker y red para obtener los artefactos bloqueados; levanta servicios temporales y siempre ejecuta `compose down --volumes`. Los tests y evals trabajan en carpetas temporales, no publican ni instalan el plugin y no modifican fixtures.

Para validar un proyecto consumidor ya inicializado:

```powershell
python scripts\validate_project.py C:\ruta\al\proyecto
python scripts\validate_spec.py C:\ruta\al\proyecto
python scripts\check_traceability.py C:\ruta\al\proyecto --increment INC-001
python skills\lks-sdd-assess-readiness\scripts\assess_readiness.py C:\ruta\al\proyecto --increment INC-001
```

La adopción usa `inspect_repository.py`, `validate_adoption.py` y `materialize_adoption.py` en ese orden. La migración usa `migrate_project.py --dry-run` antes de `--apply`; el backup debe estar fuera del proyecto. Las vistas cliente se previsualizan con `render_client_view.py --dry-run` y se escriben solo con autorización y hash coincidente.

Los códigos `0`, `2` y `3` significan respectivamente éxito/listo, contrato inválido o readiness bloqueado. Un resultado listo no autoriza implementación; la confirmación de la persona usuaria sigue siendo independiente.

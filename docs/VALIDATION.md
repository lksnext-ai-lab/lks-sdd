# Validación local

Ejecutar desde la raíz del repositorio con Python 3:

```powershell
python C:\Users\j.ormazabal\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\lks-sdd-help
python C:\Users\j.ormazabal\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\lks-sdd-define
python C:\Users\j.ormazabal\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\lks-sdd-assess-readiness
python C:\Users\j.ormazabal\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
python scripts\validate_plugin_contract.py .
python -m unittest discover -s tests -p "test_*.py" -v
python tests\run_evals.py
```

`validate_plugin_contract.py` comprueba manifiesto, skills implementadas, ausencia de componentes fuera de alcance, hashes de las fuentes canónicas y recursos declarados. Los tests y evals trabajan en carpetas temporales, no publican ni instalan el plugin y no modifican fixtures.

Para validar un proyecto consumidor ya inicializado:

```powershell
python scripts\validate_project.py C:\ruta\al\proyecto
python skills\lks-sdd-assess-readiness\scripts\assess_readiness.py C:\ruta\al\proyecto --increment INC-001
```

Los códigos `0`, `2` y `3` significan respectivamente éxito/listo, contrato inválido o readiness bloqueado. Un resultado listo no autoriza implementación; la confirmación de la persona usuaria sigue siendo independiente.

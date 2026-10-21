# Validación de LKS-SDD 5

La release estable conserva cuatro comprobaciones: aprobación explícita de versión,
integridad estática del contrato y fixtures, veintitrés pruebas de humo y regresión real
de rutas largas Windows. El checkout debe estar limpio y ligado al commit evaluado.
No se sustituye esa condición por una preparación de archivos sin commit.

La selección de humo v5 verifica flujo de tarea, reutilización, autoridad ligada al
alcance, concurrencia, recuperación, limpieza, subtareas, resultados externos,
migración completa, cambios de fuente, lector nativo v2 y ambas distribuciones.
La lista exacta está en `scripts/run_release_gate.py:CORE_TESTS`. El escenario Windows
es `test_v5_scenarios.ScenarioTests.test_windows_long_paths_execute_full_migration`.

La petición de v5 añade una validación de desarrollo específica de los doce escenarios;
no convierte toda la suite histórica v2/v3/v4 en una obligación en cada publicación.
Esos módulos permanecen como historia y soporte de investigación del código anterior.

```powershell
python -B -X utf8 scripts/validate_plugin_contract.py .
python -B -X utf8 tests/run_unit_tests.py --module test_v5_core --module test_v5_scenarios --module test_v5_improvements
```

La conversión del caso SAT se ensaya exclusivamente en una copia del snapshot exacto
`e55f87a122aa6e3595d8a26d2bb729dd867cad26`, bajo `tests/reports/v5-full/sat-copy`.
`tests/exercise_v5_real.py` verifica ese límite antes de escribir. Incluye disposición
explícita y ligada a hash para evidencia histórica, wrappers obsoletos y CI existente.
No instala en el consumidor activo ni ejecuta su regresión de aplicación.

```powershell
python -B -X utf8 tests/exercise_v5_real.py --root tests/reports/v5-full/sat-copy
python -B -X utf8 scripts/prepare_v5_candidate.py
```

La preparación local genera archivos reproducibles con huella de contenido actual.
El builder estable sigue exigiendo fuente comprometida limpia y su gate válido.
La publicación, registro, instalación y nueva sesión del host son pasos diferentes.
Pruebas automáticas de CLI/adapters no acreditan aceptación conversacional de Codex,
Copilot, piloto humano ni aceptación organizativa. Esos canales permanecen not-run.

En cambios de fuentes se repiten los tests afectados. Los resultados y límites de
esta ejecución se mantienen en el plan de v5 del repositorio fuente. No se afirma
ahorro total de tarea o tokens a partir del tamaño de documentos o de tiempos del
runtime. Los informes de pruebas y copias reales son locales e ignorados por Git.

La regresión de mejoras cubre los siete hallazgos, migración definitiva sin backups,
criterios y controles operativos y volumen documental total estable con control
histórico creciente. Un documento funcional mayor no es por sí mismo un fallo.
El informe único de conversión tiene pruebas de medidas antes/después, emisión tras
éxito, manipulación de la preparación y reanudación sin informes duplicados.
La regresión administrativa verifica estados históricos sin reapertura, ausencia de
backlog por configuración, contenido de solicitudes sin tareas artificiales y alcance
de Sonar por rutas. Un cierre nuevo sigue rechazándose sin los controles aplicables.
La revisión final comprueba controles delegados sin repetición, cambio de responsable
sin reautorización, un solo log por fallo y limpieza tras éxito, reutilización de
hechos de entrega y alta con política explícita vacía. La migración SAT completa de
la candidata actual se conserva en `tests/reports/v5-full/sat-release-review`.

# Mantenimiento del repositorio

## Fuentes y salidas

Versionar código, contratos, skills, plantillas, fixtures, baselines de regresión activas y evidencia necesaria para explicar un límite vigente.
El historial de releases se concentra en `CHANGELOG.md`. La investigación, planes,
snapshots y notas cerradas no permanecen en el checkout de mantenimiento una vez que
sus decisiones y límites vigentes se han consolidado en la documentación activa; Git
conserva sus antecedentes.

No versionar dependencias instaladas, bytecode, cachés, builds locales, resultados
de navegador o directorios temporales. `.gitignore` protege estas salidas; cada
subproyecto declara las suyas. Antes de retirar una ruta, comprobar que no contiene
fuentes versionadas, personalizaciones ni evidencia única. Usar rutas resueltas y
una copia recuperable cuando no sea necesario destruir los datos.

## Salidas regenerables

Los builds `dist`, cachés de Python, linters, salidas de herramientas web,
entornos `.venv`, `node_modules`, resultados de navegador y temporales no forman
parte del checkout mantenido. `.gitignore` los excluye y no se publican respaldos
locales ni rutas personales. La limpieza no modifica instalaciones activas, otros
consumidores, worktrees ajenos ni fuentes de `specs/canonical/`.

Los informes de `tests/reports/` que respaldan resultados históricos se conservan
localmente, ignorados y fuera de los paquetes. El `quality-report.json` y los
artefactos de una release acreditan el commit exacto; no se sustituyen por resúmenes
o snapshots de desarrollo.

## Preparar una release

Revisar todas las ramas y worktrees antes de integrar; una rama de distribución
generada no se mezcla con fuentes de mantenimiento. Cada release nueva exige
aprobación propia, checkout limpio, validación y doble build exactos. Seguir
[VALIDATION](VALIDATION.md), [RELEASING](RELEASING.md) y
[DISTRIBUTION](DISTRIBUTION.md). No generar reportes dentro del checkout dedicado.
La limpieza de temporales no autoriza mover tags ni sustituir assets publicados.

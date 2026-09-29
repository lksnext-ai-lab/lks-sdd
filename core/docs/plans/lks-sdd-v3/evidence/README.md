# Evidencia de implementación v3

Estos archivos registran observaciones de desarrollo de 2026-09-29. No son telemetría
humana ni una puerta adicional permanente de release. El gate publicado identifica
el commit limpio exacto; las ejecuciones previas se realizaron sobre la rama de trabajo.

- `automated-results.json`: salidas del runner, incluidas correcciones y resultados negativos.
- `case-coverage.json`: cada caso literal aprobado, dueño y tests pertinentes. La
  etiqueta `automated-partial` no acredita todas las cláusulas del caso compuesto.
- `source-measurement.json`: estimación transparente de texto por host y experimento
  sintético de crecimiento de historia; sin tokens facturados ni aceptación de eficiencia.
- `implementation-sources.json`: inventario LF de los módulos, schemas y adaptadores
  finales de la implementación; no atribuye retroactivamente ese hash a ensayos anteriores.

La propuesta y el plan aprobados se conservan. La decisión de release y las pruebas
observadas con personas son canales distintos; ver `../PROGRESS.md`.

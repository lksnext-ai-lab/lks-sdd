# Ejecución de v3-plan-02

Autorización: [DEC-V3-002](AUTHORIZATION.md). Fecha de revisión: 2026-09-29.
Estado: implementación técnica v3 entregada; aceptación observada de uso pendiente.
La aceptación de release solicitada por el usuario no acredita el piloto de 017.

## Entrega técnica

| Tareas | Resultado disponible |
|---|---|
| 001–002 | Contrato 3, UUID permanentes, Markdown canónico, historial recuperable y transacciones con guardas de origen/recuperación. Lectores v2 conservados. |
| 003–004 | Perfiles configurables, miembros y autoridad vigente; propuesta funcional/técnica exacta y aprobación por porciones antes del plan. Permiso operativo separado y agrupable. |
| 005–007 | Transiciones y dependencias tipadas, excepciones delimitadas, asignación/relevos aceptados, rama/base/destino y reconciliación contra referencia independiente. |
| 008–009 | Sonar y Dependency-Check mediante informes normalizados o ejecutor existente autorizado; resultados terminales, vigencia, reintentos acotados y corrección durante implementación. Cierre distinto de integración/aceptación. |
| 010 | Contexto literal y deduplicado, incertidumbre conservada, caché local invalidable. El selector reducido permanece en comparación: no se activa por medir menos texto. |
| 011–012 | Inspección de adopción y migración 2.x explícita; originales, código, historia cerrada y plan activo conservados. Confirmaciones de contenido reutilizables solo con procedencia exacta; autorización operativa actual. |
| 013–015 | Estado por petición y proceso, trazabilidad, seis skills progresivas, CLI común y paquetes Codex/Copilot con runtime fijado. |
| 016 | Regresiones focales e integración automatizada ejecutadas; cobertura por caso registrada sin confundir evidencia parcial con cumplimiento de todas sus cláusulas. |
| 017 | Protocolo preparado. Observaciones humanas, servicios reales y coste total de uso: **not-run**. |

## Evidencia disponible

- [Resultados automatizados](evidence/automated-results.json): 72 tests únicos con
  resultado satisfactorio en los recorridos de desarrollo y repeticiones focales.
  Conserva también el fallo inicial del adaptador Copilot, corregido y repetido.
- Las 14 pruebas de humo finales pasaron en 234,634 s. Su límite del gate se amplía
  de 180 a 600 s para las escrituras durables v3 en Windows; no se eliminan controles.
- Cambio real de runtime fijado desde bytes publicados de v2.3.1, CLI v3 y adaptadores:
  passed tras la corrección. Rutas largas Windows: passed.
- Contrato estático y manifiesto de fixtures: passed. Diff revisado; ninguna fuente
  de `specs/canonical/` modificada. No se añaden agentes, MCP, hooks ni CI/CD consumidor.
- [Mapa de los 100 casos](evidence/case-coverage.json): 85 cuentan con evidencia
  automática pertinente parcial; los otros 15 conservan revisión de implementación
  o protocolo. **No equivale a 100 casos aceptados**, ni a probar todas las cláusulas
  de los 85 casos compuestos. Las fuentes aprobadas siguen siendo normativas.
- [Medición de fuentes](evidence/source-measurement.json): instrucciones ordinarias
  estimadas entre 1.336 y 1.933 tokens según skill/host, con caracteres/4. Metadatos de
  descubrimiento: 252 estimados, por separado. Excluye contrato consumidor, herramientas,
  instrucciones ajenas y secciones técnicas adicionales que sea necesario consultar.
- En una muestra sintética, ampliar la historia operativa de 10 a 100 eventos mantuvo
  5.025 caracteres normativos y 7 bloques. Lectura local: 0,4412 s y 1,1085 s. Es una
  observación, no una baseline ni una promesa de rendimiento o de ahorro facturado.

Los ensayos de inicializadores publicados cubren diez orígenes nativos 2.0.0–2.3.1,
con procedencia en `tests/fixtures/v3-migration/origins.json`; no prueban todos los
flujos posibles de cada versión. La migración de proyectos reales requiere su propia
vista previa y decisión; en esta entrega no se migra ningún consumidor.

## Aceptación y publicación

La decisión del usuario acepta la release 3.0 y autoriza merge, publicación y actualización
personal en Codex. La publicación exige además el gate del commit limpio integrado en
main. La evidencia definitiva del SHA, paquetes y checksums se conserva en el run
`stable-preflight` y en los assets de [v3.0.0](https://github.com/lksnext-ai-lab/lks-sdd/releases/tag/v3.0.0).
Los informes locales anteriores son evidencia de desarrollo; no sustituyen ese gate.

La aceptación funcional observada, agilidad/eficiencia total, continuidad conversacional
Codex/Copilot y uso real de Sonar/Dependency-Check permanecen pendientes conforme al
[protocolo de uso](../../V3-HOST-ACCEPTANCE.md). Instalar v3 no recarga necesariamente
las instrucciones de un chat ya abierto ni convierte automáticamente un proyecto v2.

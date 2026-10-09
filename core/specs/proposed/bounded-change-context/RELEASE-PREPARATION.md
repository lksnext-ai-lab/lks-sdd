# Preparación oficial de 3.3.0-rc.1

Fecha de planificación: 2026-10-10, Europe/Madrid.

## Autoridad y fuente

El «sí» del usuario autoriza crear el commit de los cambios ya revisados para
continuar con el gate oficial. Incluye la mejora de eficiencia documental y las
correcciones previas de inventarios/migración comprobadas en
[IMPLEMENTATION.md](IMPLEMENTATION.md). La rama es
`codex/fix-legacy-migration-inventory`; la base es
`6e1c4380c130d2ff4f7a9cae97b1257e05294724`.

Las fuentes de `specs/canonical/` se conservan. La nueva evidencia se guardará
fuera del repositorio, vinculada al SHA exacto. Los informes de desarrollo
anteriores acreditan su propio corte; no sustituyen el gate oficial.
Los JSON de evidencia conservan sus bytes mediante atributos Git locales para
mantener verificables los hashes históricos al hacer checkout en otro sistema.

## Tareas y dependencias

| Tarea | Trabajo | Condición para continuar |
|---|---|---|
| EF-10 | Revisar ámbito, archivos nuevos y diff staged; crear el commit autorizado. | Sin repositorios anidados, fuentes canónicas alteradas o cambios ajenos; checkout limpio y SHA registrado. |
| EF-11 | Ejecutar preflight y gate oficial de canal candidate, fecha 2026-10-10. | Readiness ready; integridad estática y los catorce casos de humo passed, ligados al mismo SHA limpio. Un fallo se conserva y se diagnostica antes de repetir. |
| EF-12 | Generar una vez los paquetes oficiales desde ese commit y gate. Validar plugin, marketplace, Copilot y checksums. | Manifiestos, versión, fuente y bytes coherentes; validación de paquetes passed; checkout sigue limpio. |

El gate candidate vigente exige estática y catorce casos de humo; la aprobación
stable y rutas largas de Windows pertenecen al gate stable. La regresión Windows
ya superada durante desarrollo se conserva como evidencia separada.

## Cierre que se puede acreditar

La candidata local podrá declararse técnicamente preparada al superar EF-10–12.
No se crea una aprobación stable, un tag o una release publicada con este permiso.
Aceptación humana de las funcionalidades, hosts reales, piloto, migración del
consumidor y ahorro facturado/tiempo humano permanecen pendientes.

El resultado final y las rutas de evidencia se entregarán al usuario tras validar
los paquetes, sin escribir informes nuevos sobre el árbol del commit evaluado.

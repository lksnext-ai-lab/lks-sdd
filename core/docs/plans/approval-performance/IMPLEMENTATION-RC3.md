# Preparación técnica de 3.4.3-rc.3

Mantenimiento autorizado el 2026-10-14. Base: 3.4.2,
`a657bf7b07461c8b03516f9adbb00bb7a6b9ed7c`. Se conservan los informes de
[rc.1](IMPLEMENTATION-RC1.md) y [rc.2](IMPLEMENTATION-RC2.md) y sus muestras.
No cambia el contrato canónico, schema 3.1 ni método 3.1.0.

## Causas y corrección

Los perfiles separados de rc.2 observan asignaciones por elemento para el mapa
de propietarios y listas de identidades únicas, además de la observación profunda
necesaria para la guardia. Se conserva esta última; el propietario único pasa a
una referencia débil y la identidad única guarda directamente su elemento. Los
casos compartidos o ambiguos conservan todos sus participantes. La construcción
privada prepara elementos y datos resueltos antes de conectar la tabla observable;
la validación y las consultas siguen operando sobre el modelo completo.

Los perfiles de carga observan coste dominante de consultas repetidas de rutas.
Se consultan atributos frescos de Windows, manteniendo la ruta portable y todos
los rechazos físicos. Se elimina una consulta redundante de tamaño anterior a
la lectura verificada. El doctor calcula las huellas por bloques en vez de
retener el archivo entero; sigue leyendo todos sus bytes y verificando las
instrucciones con la normalización anterior. No existe caché de confianza física.

Se añade la regresión de reinicialización de un elemento conectado al modelo:
conserva observadores, invalida índices y rechaza la edición antes de modificar
contenido durante una evaluación, incluso si el llamante captura la excepción.
Se ensayan sustitución/crecimiento entre observación y lectura y permiso denegado.

## Evidencia y cierre

Para medir exactamente los paquetes preparados, la evidencia final se guarda
fuera del runtime y no obliga a modificar ni reconstruir los ZIP después:

- `tests/reports/lks-sdd-3.4.3-rc.3.manifest.json`: base, parche, fuentes, herramientas,
  hashes de paquetes reproducidos y evidencias finales; estados de cierre reales.
- `tests/reports/rc3-final-report.md`: resultados de CPU, tiempo y memoria, rangos,
  interpretación y limitaciones, con comparación contra 3.4.2 y rc.2.
- `tests/reports/rc3-isolated.json`: todas las muestras, contadores, comparaciones,
  auditorías e inputs fijados; sin cProfile/tracemalloc ni pruebas concurrentes.
- `tests/reports/rc3-host-codex.json` y `rc3-host-copilot.json`: ciclo completo desde
  los paquetes exactos, doctor/autoridad/presentación/aplicación actuales y rechazos.
- `tests/reports/lks-sdd-3.4.3-rc.3-evidence.zip`: copia recuperable de esas evidencias.

La existencia de esta fuente no acredita pruebas o benchmarks terminados. El
manifiesto adjunto declara sus resultados y hashes reales. Se conserva la CPU
necesaria para la guardia y el coste de los observadores; no se promete coste
cero ni ausencia de regresiones para todos los tamaños y cargas.

El alcance y la reproducción están en [APPROVAL-PERFORMANCE](../../APPROVAL-PERFORMANCE.md).
No se ejecuta el gate stable de commit limpio sobre este árbol de desarrollo.
La aceptación humana o conversacional de host y el piloto permanecen `not-run`.
No se crea commit, push, etiqueta, publicación, instalación ni registro activo.

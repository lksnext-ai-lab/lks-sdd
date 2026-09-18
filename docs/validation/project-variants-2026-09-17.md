# Validación del MVP de variantes — 2026-09-17

Estado: implementación local sin publicar. Diagnóstico del árbol de trabajo sobre
`3b6e247`, no atestación de release ni aceptación de un consumidor real.

## Alcance comprobado

- Diagnóstico estático, diferencias de versión y dependencias, contradicciones
  manifest/lock, aprobación durable y caducidad, cambios de alcance y hashes.
- Preparación sin scaffold, ejecución de observers aislados, gates por etapa,
  reutilización sin rejuvenecer resultados, artefactos íntegros y cierre gobernado.
- Revisión visual a través del contrato canónico 1.2 existente; un observer no
  puede reemplazar la revisión humana. La prueba de contrato utiliza capturas
  sintéticas; no se presenta como aceptación visual de un producto.
- Inclusión de módulos y schemas nuevos en la distribución de desarrollo.

## Resultados observados

| Comprobación | Resultado |
|---|---|
| Suite general de diagnóstico | 401 casos: 399 passed, 1 failed, 1 skipped; 454,41 s |
| Primera revisión ampliada de variantes | 24/24 passed; 126,84 s |
| Revisión posterior de variantes + CLI + transiciones | 32/32 passed (25 + 3 + 4); 137,76 s |
| Cierre de revisión: caché y gates no deterministas | 2/2 passed; 27,51 s; 26 casos de variantes comprobados entre ambas ejecuciones |
| Evals existentes | 6/6 passed |
| Contrato del plugin | passed |
| Validación de las seis skills y manifiesto | passed |
| Estructura de perfiles | 23/23 válidos; no promueve candidatos |
| Catálogo de fixtures | 14 válidas |
| Ruff (errores F) y diff whitespace | passed |
| Benchmark existente | passed; status mediana 461,815 ms; work start 4330,77 ms; reducción administrativa 60 % |

Aceptación Docker explícita en fixture genérica: una aprobación, dos procesos
aislados iniciales, cero procesos en la repetición, cierre de TASK con `CKPT-003`,
`verified-with-reservations`, proyecto válido y `delivery_readiness=not-assessed`.
Última medición: primera verificación 5,789 s; repetición 2,276 s; recorrido 19,03 s.
Son medidas locales con otras validaciones en curso, no una garantía de rendimiento.
Las aserciones funcionales de esta fixture no certifican todas sus dependencias
ni todas las combinaciones del catálogo.

## Fallo previo y omisión

`test_native_plugin_paths_fit_a_windows_plugin_cache` falla por una ruta del
estudio previo de context compiler: 125 caracteres frente al límite de 110.
Se reprodujo el mismo máximo generando en memoria la proyección de Copilot desde
`git archive HEAD`, sin las modificaciones del evolutivo:

```text
core/docs/proposals/context-compiler-study-2026-09-11/repo-probe/corpora/parallel_three_tasks/TASK-001-seeds-only.txt
```

No se ha eliminado ni reorganizado ese estudio. La suite general no está verde y
este fallo debe resolverse antes de presentar una distribución como validada.

La prueba de symlink visual queda `skipped` por `WinError 1314` en este Windows.
No se ha elevado privilegios ni convertido esa omisión en un resultado superado.

## Conservación y límites

La intersección entre archivos cambiados y `CERTIFICATION_ENGINE_FILES` es vacía.
No hay cambios bajo `profiles/` o `specs/canonical/`. El flujo estricto y las
evidencias históricas se conservan; el documento optativo no cambia el schema 1.5.
La actualización de las seis skills usa referencias breves a la guía compartida,
sin nuevas skills ni cambios en sus descripciones de activación.

No se ha creado commit, etiqueta, push, publicación, instalación activa ni
aprobación de release. Los canales humanos, piloto y aceptación de ambos hosts
no se consideran ejecutados por estas pruebas.

Los reportes JSON de esta ejecución están en el directorio temporal
`lks-sdd-variants-validation-1789633324749`, bajo el temporal local de Windows.
Comandos reproducibles en [VALIDATION.md](../VALIDATION.md) y alcance en
[PROJECT-VARIANTS.md](../PROJECT-VARIANTS.md).
